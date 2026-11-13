from fastapi import FastAPI

from app.api import application_settings, assistant, contact_persons, conversations, preferences
from app.api.auth import router as auth_router
from app.api.calendar.calendar import router as calendar_router
from app.api.calendar.calendar_suggestions import router as calendar_suggestions_router
from app.api.employee_invitations import router as employee_invitations_router
from app.api.employees import router as employees_router
from app.api.profile import router as profile_router
from app.api.tasks import router as tasks_router
from app.core.csrf_config import configure_csrf
from app.api.calendar_integrations import router as calendar_integrations_router


def create_app() -> FastAPI:
    configure_csrf()

    app = FastAPI(
        title="NeuroLens API",
        version="0.1.0",
    )

    app.include_router(auth_router, prefix="/api")
    app.include_router(employees_router, prefix="/api")
    app.include_router(employee_invitations_router, prefix="/api")
    app.include_router(profile_router, prefix="/api")
    app.include_router(preferences.router, prefix="/api")
    app.include_router(application_settings.router, prefix="/api")
    app.include_router(contact_persons.router, prefix="/api")
    app.include_router(assistant.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(calendar_router, prefix="/api")
    app.include_router(calendar_suggestions_router, prefix="/api")
    app.include_router(calendar_integrations_router, prefix="/api")

    return app


app = create_app()


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "neurolens-api",
    }
