from sqlalchemy.orm import Session

from .models import Inventario
from .schemas import InventarioCreate



def obtener_inventario(db:Session):

    return db.query(Inventario).all()



def crear_inventario(
        db:Session,
        inventario:InventarioCreate
):

    nuevo = Inventario(

        nombre_evento=inventario.nombre_evento,

        cantidad_total=inventario.cantidad_total,

        disponibles=inventario.disponibles
    )


    db.add(nuevo)

    db.commit()

    db.refresh(nuevo)


    return nuevo



def verificar_disponibilidad(
        db:Session,
        id:int,
        cantidad:int
):

    item = db.query(Inventario)\
        .filter(Inventario.id==id)\
        .first()


    if not item:
        return False


    return item.disponibles >= cantidad