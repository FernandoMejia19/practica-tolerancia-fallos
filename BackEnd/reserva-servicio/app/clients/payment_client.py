import logging
import os

import requests

from ..resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError
)


logger = logging.getLogger(__name__)


PAYMENTS_URL = os.getenv(
    "PAYMENTS_URL",
    "http://pagos-service:8000"
)

PAYMENT_TIMEOUT = float(
    os.getenv("PAYMENT_TIMEOUT", "3")
)

payment_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30
)


class PaymentUnavailableError(Exception):
    """Pagos no está disponible o tardó demasiado."""


class PaymentRejectedError(Exception):
    """La solicitud fue rechazada por el servicio de pagos."""


def procesar_pago(
    id_reserva: int,
    monto: float,
    simular_demora: int = 0,
    simular_fallo: bool = False
) -> dict:
    payment_breaker.before_call()

    url = f"{PAYMENTS_URL}/payments"

    parametros = {
        "simular_demora": simular_demora,
        "simular_fallo": str(simular_fallo).lower()
    }

    payload = {
        "id_reserva": id_reserva,
        "monto": monto
    }

    try:
        logger.info(
            "Procesando pago de la reserva %s",
            id_reserva
        )

        response = requests.post(
            url,
            params=parametros,
            json=payload,
            timeout=PAYMENT_TIMEOUT
        )

        if response.status_code == 200:
            payment_breaker.register_success()
            return response.json()

        if 400 <= response.status_code < 500:
            raise PaymentRejectedError(
                f"Pago rechazado: {response.text}"
            )

        raise requests.RequestException(
            f"Pagos respondió HTTP {response.status_code}"
        )

    except PaymentRejectedError:
        payment_breaker.register_failure()
        raise

    except (
        requests.Timeout,
        requests.ConnectionError,
        requests.RequestException
    ) as error:
        payment_breaker.register_failure()

        logger.error(
            "Error temporal en Pagos: %s",
            error
        )

        raise PaymentUnavailableError(
            "La pasarela de pagos no respondió correctamente"
        ) from error