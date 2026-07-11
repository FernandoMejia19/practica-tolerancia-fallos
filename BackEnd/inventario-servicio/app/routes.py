from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from .database import get_db

from .schemas import InventarioCreate

from .services import (
    obtener_inventario,
    crear_inventario,
    verificar_disponibilidad
)



router = APIRouter(
    prefix="/inventario",
    tags=["Inventario"]
)



@router.get("/")
def listar(
    db:Session=Depends(get_db)
):

    return obtener_inventario(db)



@router.post("/")
def crear(
    data:InventarioCreate,
    db:Session=Depends(get_db)
):

    return crear_inventario(
        db,
        data
    )



@router.get("/{id}/disponible/{cantidad}")
def disponibilidad(
    id:int,
    cantidad:int,
    db:Session=Depends(get_db)
):

    return {
        "disponible":
        verificar_disponibilidad(
            db,
            id,
            cantidad
        )
    }