import logging
from typing import Any, Optional

from .clients.inventory_client import (
    confirmar_asiento,
    liberar_asiento,
    reservar_asiento_con_retry,
)
from .clients.notification_client import (
    NotificationUnavailableError,
    enviar_notificacion,
)
from .clients.payment_client import procesar_pago
from .database import get_connection


logger = logging.getLogger(__name__)


def insertar_reserva(reserva: Any) -> int:
    """
    Inserta una reserva en estado PENDIENTE y devuelve su ID.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO reservas (
                    id_asiento,
                    cliente,
                    correo,
                    monto,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_reserva
                """,
                (
                    reserva.id_asiento,
                    reserva.cliente,
                    reserva.correo,
                    reserva.monto,
                    "PENDIENTE",
                ),
            )

            resultado = cursor.fetchone()

            if resultado is None:
                raise RuntimeError(
                    "La base de datos no devolvió el ID de la reserva"
                )

            id_reserva = resultado[0]
            connection.commit()

            return id_reserva

    except Exception:
        connection.rollback()
        logger.exception(
            "Error al insertar la reserva del asiento %s",
            reserva.id_asiento,
        )
        raise

    finally:
        connection.close()


def actualizar_estado_reserva(
    id_reserva: int,
    nuevo_estado: str,
) -> None:
    """
    Actualiza el estado de una reserva.
    """

    estados_permitidos = {
        "PENDIENTE",
        "CONFIRMADA",
        "CANCELADA",
    }

    if nuevo_estado not in estados_permitidos:
        raise ValueError(
            f"Estado de reserva no permitido: {nuevo_estado}"
        )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE reservas
                SET estado = %s
                WHERE id_reserva = %s
                """,
                (
                    nuevo_estado,
                    id_reserva,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    f"No existe la reserva {id_reserva}"
                )

            connection.commit()

    except Exception:
        connection.rollback()
        logger.exception(
            "Error al actualizar la reserva %s al estado %s",
            id_reserva,
            nuevo_estado,
        )
        raise

    finally:
        connection.close()


def obtener_reservas() -> list[dict[str, Any]]:
    """
    Devuelve todas las reservas registradas.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_reserva,
                    id_asiento,
                    cliente,
                    correo,
                    monto,
                    estado
                FROM reservas
                ORDER BY id_reserva DESC
                """
            )

            filas = cursor.fetchall()

            return [
                {
                    "id_reserva": fila[0],
                    "id_asiento": fila[1],
                    "cliente": fila[2],
                    "correo": fila[3],
                    "monto": float(fila[4]),
                    "estado": fila[5],
                }
                for fila in filas
            ]

    except Exception:
        logger.exception(
            "Error al consultar todas las reservas"
        )
        raise

    finally:
        connection.close()


def obtener_reserva(
    id_reserva: int,
) -> Optional[dict[str, Any]]:
    """
    Devuelve una reserva por ID o None si no existe.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_reserva,
                    id_asiento,
                    cliente,
                    correo,
                    monto,
                    estado
                FROM reservas
                WHERE id_reserva = %s
                """,
                (id_reserva,),
            )

            fila = cursor.fetchone()

            if fila is None:
                return None

            return {
                "id_reserva": fila[0],
                "id_asiento": fila[1],
                "cliente": fila[2],
                "correo": fila[3],
                "monto": float(fila[4]),
                "estado": fila[5],
            }

    except Exception:
        logger.exception(
            "Error al consultar la reserva %s",
            id_reserva,
        )
        raise

    finally:
        connection.close()


def crear_reserva(
    reserva: Any,
    simular_demora_pago: int = 0,
    simular_fallo_pago: bool = False,
    simular_fallo_notificacion: bool = False,
    simular_demora_notificacion: int = 0,
) -> dict[str, Any]:

    asiento_retenido = False
    id_reserva = None

    try:
        reservar_asiento_con_retry(
            id_asiento=reserva.id_asiento
        )

        asiento_retenido = True

        id_reserva = insertar_reserva(reserva)

        pago = procesar_pago(
            id_reserva=id_reserva,
            monto=reserva.monto,
            simular_demora=simular_demora_pago,
            simular_fallo=simular_fallo_pago,
        )

        confirmar_asiento(
            reserva.id_asiento
        )

        asiento_retenido = False

        actualizar_estado_reserva(
            id_reserva,
            "CONFIRMADA",
        )

        try:
            resultado_notificacion = (
                enviar_notificacion(
                    id_reserva=id_reserva,
                    correo=str(reserva.correo),
                    simular_fallo=(
                        simular_fallo_notificacion
                    ),
                    simular_demora=(
                        simular_demora_notificacion
                    ),
                )
            )

            notificacion = {
                "estado": "ENVIADA",
                "detalle": resultado_notificacion,
            }

        except NotificationUnavailableError as error:
            logger.warning(
                "Fallback activado para "
                "la reserva %s: %s",
                id_reserva,
                error,
            )

            notificacion = {
                "estado": "PENDIENTE",
                "mensaje": (
                    "La compra fue confirmada, "
                    "pero el correo se enviará "
                    "posteriormente."
                ),
            }

        return {
            "id_reserva": id_reserva,
            "estado": "CONFIRMADA",
            "pago": pago,
            "notificacion": notificacion,
        }

    except Exception as error:
        logger.error(
            "Error al procesar la reserva: %s",
            error,
        )

        if id_reserva is not None:
            try:
                actualizar_estado_reserva(
                    id_reserva,
                    "CANCELADA",
                )

            except Exception as update_error:
                logger.error(
                    "No se pudo cancelar "
                    "la reserva %s: %s",
                    id_reserva,
                    update_error,
                )

        if asiento_retenido:
            try:
                liberar_asiento(
                    reserva.id_asiento
                )

            except Exception as release_error:
                logger.error(
                    "No se pudo liberar "
                    "el asiento %s: %s",
                    reserva.id_asiento,
                    release_error,
                )

        raise