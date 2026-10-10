from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(
    title="NeuroLens API",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "neurolens-api",
    }