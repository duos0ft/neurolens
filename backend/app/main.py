from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.employee_invitations import router as employee_invitations_router
from app.api.employees import router as employees_router
from app.core.csrf_config import configure_csrf


def create_app() -> FastAPI:
    configure_csrf()

    app = FastAPI(
        title="NeuroLens API",
        version="0.1.0",
    )

    app.include_router(auth_router, prefix="/api")
    app.include_router(employees_router, prefix="/api")
    app.include_router(employee_invitations_router, prefix="/api")

    return app


app = create_app()


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "neurolens-api",
    }