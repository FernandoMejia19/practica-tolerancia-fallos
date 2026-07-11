from sqlalchemy import Column, Integer, String
from .database import Base


class Inventario(Base):

    __tablename__ = "inventario"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    nombre_evento = Column(
        String,
        nullable=False
    )


    cantidad_total = Column(
        Integer,
        nullable=False
    )


    disponibles = Column(
        Integer,
        nullable=False
    )