from pydantic import BaseModel


class InventarioCreate(BaseModel):

    nombre_evento:str
    cantidad_total:int
    disponibles:int



class InventarioResponse(BaseModel):

    id:int
    nombre_evento:str
    cantidad_total:int
    disponibles:int


    class Config:
        from_attributes=True