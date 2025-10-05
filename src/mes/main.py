"""Application entrypoint for the custom MES service."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import MESSettings, get_settings

LOGGER = logging.getLogger(__name__)


def create_app(config_path: Optional[Path] = None) -> FastAPI:
    """Instantiate a FastAPI application configured for the MES service."""

    if config_path:
        settings = get_settings(config_path=config_path)
    else:
        settings = get_settings()

    app = FastAPI(title="Custom MES", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - logging side effect
        LOGGER.info("Starting MES service in %s mode", settings.environment)

    return app


__all__ = ["create_app"]
