from fastapi import FastAPI

from .routes import router


app = FastAPI(
    title="Reservation Service",
    version="2.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "reservation-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "service": "reservation-service",
        "status": "healthy"
    }