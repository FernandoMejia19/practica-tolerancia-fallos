import logging
import os
import time

import requests


logger = logging.getLogger(__name__)


INVENTORY_URL = os.getenv(
    "INVENTORY_URL",
    "http://inventario-service:8000"
)


class InventoryUnavailableError(Exception):
    """El servicio de inventario no respondió después de los reintentos."""


class SeatUnavailableError(Exception):
    """El asiento ya no se encuentra disponible."""


def reservar_asiento_con_retry(
    id_asiento: int,
    max_intentos: int = 4,
    timeout_segundos: int = 3
) -> dict:
    """
    Solicita la retención temporal de un asiento.

    Reintenta solamente ante errores temporales:
    - timeout
    - problemas de conexión
    - respuestas 5xx

    No reintenta ante 409 porque significa que el asiento
    ya está reservado o vendido.
    """

    url = (
        f"{INVENTORY_URL}/inventory/"
        f"seats/{id_asiento}/hold"
    )

    for intento in range(1, max_intentos + 1):
        try:
            logger.info(
                "Intentando reservar asiento %s. Intento %s/%s",
                id_asiento,
                intento,
                max_intentos
            )

            response = requests.post(
                url,
                timeout=timeout_segundos
            )

            if response.status_code == 200:
                logger.info(
                    "Asiento %s reservado correctamente",
                    id_asiento
                )
                return response.json()

            if response.status_code == 409:
                logger.warning(
                    "Asiento %s no disponible",
                    id_asiento
                )
                raise SeatUnavailableError(
                    "El asiento seleccionado ya no está disponible"
                )

            if response.status_code >= 500:
                raise requests.RequestException(
                    f"Inventario respondió {response.status_code}"
                )

            response.raise_for_status()

        except SeatUnavailableError:
            raise

        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.RequestException
        ) as error:
            logger.warning(
                "Fallo temporal al consultar Inventario: %s",
                error
            )

            if intento == max_intentos:
                logger.error(
                    "Inventario no disponible después de %s intentos",
                    max_intentos
                )
                raise InventoryUnavailableError(
                    "El servicio de inventario no está disponible"
                ) from error

            espera = 2 ** (intento - 1)

            logger.info(
                "Reintentando en %s segundo(s)",
                espera
            )

            time.sleep(espera)

    raise InventoryUnavailableError(
        "No fue posible comunicarse con Inventario"
    )