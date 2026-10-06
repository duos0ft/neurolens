from fastapi import FastAPI

app = FastAPI(
    title="NeuroLens API",
    description="Backend API for the NeuroLens workplace communication assistant.",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "neurolens-api",
    }
