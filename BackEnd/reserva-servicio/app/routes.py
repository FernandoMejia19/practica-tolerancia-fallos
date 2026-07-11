from fastapi import APIRouter, HTTPException

from .schemas import ReservaCreate
from .services import (
    crear_reserva,
    obtener_reservas,
    obtener_reserva
)

router = APIRouter()


@router.post("/reservations")
def create(reserva: ReservaCreate):

    reserva_id = crear_reserva(reserva)

    return {
        "mensaje":"Reserva creada correctamente",
        "id_reserva":reserva_id
    }


@router.get("/reservations")
def get_all():

    return obtener_reservas()


@router.get("/reservations/{id_reserva}")
def get_one(id_reserva:int):

    reserva = obtener_reserva(id_reserva)

    if reserva is None:
        raise HTTPException(
            status_code=404,
            detail="Reserva no encontrada"
        )

    return reserva