from fastapi import FastAPI

from app.api.profile import router as profile_router

app = FastAPI(
    title="NeuroLens API",
    version="0.1.0",
)

app.include_router(profile_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "neurolens-api",
    }