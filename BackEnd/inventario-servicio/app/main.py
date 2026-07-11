from fastapi import FastAPI

from .database import Base, engine

from .routes import router



Base.metadata.create_all(
    bind=engine
)



app = FastAPI(
    title="Inventario Servicio",
    version="1.0"
)



app.include_router(router)



@app.get("/")
def root():

    return {

        "servicio":
        "inventario-servicio",

        "estado":
        "activo"
    }