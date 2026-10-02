"""FastAPI entrypoint — inicializa DI, banco, worker pool e rotas."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.v1.routers import clips, downloads, history, jobs, models, settings, templates, upload
from app.api.websocket import channels as ws_channels
from app.config import get_settings
from app.infrastructure.container import Container, set_container
from app.infrastructure.database.session import init_db
from app.infrastructure.logging.setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    cfg = get_settings()
    cfg.ensure_dirs()
    configure_logging(cfg)

    await init_db(cfg)

    container = await Container.create(cfg)
    set_container(container)
    await container.worker_pool.start()

    try:
        yield
    finally:
        await container.worker_pool.stop()
        await container.dispose()


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title="LocalTranscriber API",
        version="0.1.0",
        description="Transcrição local de vídeos com faster-whisper.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(downloads.router, prefix="/api/v1")
    app.include_router(history.router, prefix="/api/v1")
    app.include_router(settings.router, prefix="/api/v1")
    app.include_router(models.router, prefix="/api/v1")
    app.include_router(clips.router, prefix="/api/v1")
    app.include_router(templates.router, prefix="/api/v1")
    app.include_router(ws_channels.router)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"app": "LocalTranscriber", "version": "0.1.0"}

    return app


app = create_app()
