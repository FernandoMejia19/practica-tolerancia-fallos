from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Notification Service",
    version="1.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Notification Service",
        "status": "running"
    }
