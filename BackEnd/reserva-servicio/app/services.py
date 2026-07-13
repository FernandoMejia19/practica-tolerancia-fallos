from .clients.inventory_client import (
    InventoryUnavailableError,
    SeatUnavailableError,
    reservar_asiento_con_retry
)
from .database import get_connection


def crear_reserva(reserva):
    """
    Primero solicita a Inventario la retención del asiento.
    Solo si Inventario confirma, se registra la reserva.
    """

    reservar_asiento_con_retry(
        id_asiento=reserva.id_asiento
    )

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            query = """
                INSERT INTO reservas(
                    id_asiento,
                    cliente,
                    correo,
                    estado
                )
                VALUES (%s, %s, %s, 'PENDIENTE')
                RETURNING id_reserva;
            """

            cursor.execute(
                query,
                (
                    reserva.id_asiento,
                    reserva.cliente,
                    reserva.correo
                )
            )

            reserva_id = cursor.fetchone()[0]

        conn.commit()
        return reserva_id

    except Exception:
        if conn is not None:
            conn.rollback()

        raise

    finally:
        if conn is not None:
            conn.close()


def obtener_reservas():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_reserva,
                    id_asiento,
                    cliente,
                    correo,
                    estado
                FROM reservas
                ORDER BY id_reserva;
                """
            )

            filas = cursor.fetchall()

        return [
            {
                "id_reserva": fila[0],
                "id_asiento": fila[1],
                "cliente": fila[2],
                "correo": fila[3],
                "estado": fila[4]
            }
            for fila in filas
        ]

    finally:
        conn.close()


def obtener_reserva(id_reserva):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_reserva,
                    id_asiento,
                    cliente,
                    correo,
                    estado
                FROM reservas
                WHERE id_reserva = %s;
                """,
                (id_reserva,)
            )

            fila = cursor.fetchone()

        if fila is None:
            return None

        return {
            "id_reserva": fila[0],
            "id_asiento": fila[1],
            "cliente": fila[2],
            "correo": fila[3],
            "estado": fila[4]
        }

    finally:
        conn.close()