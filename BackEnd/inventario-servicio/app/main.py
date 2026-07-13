from fastapi import FastAPI

from .routes import router


app = FastAPI(
    title="Inventory Service",
    version="2.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "inventory-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "service": "inventory-service",
        "status": "healthy"
    }