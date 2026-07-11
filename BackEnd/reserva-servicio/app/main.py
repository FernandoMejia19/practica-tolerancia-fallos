from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Reservation Service",
    version="1.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service":"Reservation Service",
        "status":"running"
    }