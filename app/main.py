from fastapi import FastAPI

from app.api.routes import health, twilio, vapi
from app.config import settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    api = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )
    api.include_router(health.router)
    api.include_router(vapi.router)
    api.include_router(twilio.router)
    return api


app = create_app()
