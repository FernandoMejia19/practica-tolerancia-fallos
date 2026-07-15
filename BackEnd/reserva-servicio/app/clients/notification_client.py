import logging
import os
from typing import Any

import requests


logger = logging.getLogger(__name__)


NOTIFICATIONS_URL = os.getenv(
    "NOTIFICATIONS_URL",
    "http://notificaciones-service:8000"
)

NOTIFICATION_TIMEOUT = float(
    os.getenv(
        "NOTIFICATION_TIMEOUT",
        "3"
    )
)


class NotificationUnavailableError(Exception):
    pass


def enviar_notificacion(
    id_reserva: int,
    correo: str,
    simular_fallo: bool = False,
    simular_demora: int = 0,
) -> dict[str, Any]:

    url = (
        f"{NOTIFICATIONS_URL}/notifications"
    )

    params = {
        "simular_fallo": str(
            simular_fallo
        ).lower(),
        "simular_demora": simular_demora,
    }

    payload = {
        "id_reserva": id_reserva,
        "correo": correo,
    }

    try:
        response = requests.post(
            url,
            params=params,
            json=payload,
            timeout=NOTIFICATION_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()

        raise requests.RequestException(
            f"HTTP {response.status_code}"
        )

    except requests.RequestException as error:
        logger.warning(
            "Falló Notificaciones para "
            "la reserva %s: %s",
            id_reserva,
            error,
        )

        raise NotificationUnavailableError(
            "Servicio de notificaciones no disponible"
        ) from error