from pydantic import BaseModel, EmailStr


class ReservaCreate(BaseModel):
    id_asiento: int
    cliente: str
    correo: EmailStr


class ReservaResponse(BaseModel):
    id_reserva: int
    id_asiento: int
    cliente: str
    correo: str
    estado: str