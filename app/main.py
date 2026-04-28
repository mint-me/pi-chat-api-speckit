"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import configure_database, dispose_database
from app.errors import register_error_handlers
from app.logging import RequestIdMiddleware, configure_logging
from app.routers import auth, chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown hooks."""
    settings = get_settings()
    configure_logging()
    configure_database(settings.database_url)
    yield
    await dispose_database()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Minimal LLM-powered chat API with JWT auth, SSE streaming, and history.",
        version="0.1.0",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.add_middleware(RequestIdMiddleware)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    return app


app = create_app()
