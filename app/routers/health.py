"""Health check endpoint."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health() -> JSONResponse:
    """Return service status."""
    logger.info("health.check", extra={"event": "health.check"})
    return JSONResponse({"status": "ok"})
