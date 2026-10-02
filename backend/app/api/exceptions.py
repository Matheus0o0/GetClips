"""Handlers globais de exceção."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ClipNotFoundError,
    DomainError,
    HighlightSelectionError,
    JobNotFoundError,
    LLMNotConfiguredError,
    ModelNotAvailableError,
    ReframeError,
    SourceVideoUnavailableError,
    TemplateNotFoundError,
    UnsupportedSourceError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(JobNotFoundError)
    async def _job_not_found(_r: Request, exc: JobNotFoundError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "job_not_found"}, status_code=404)

    @app.exception_handler(UnsupportedSourceError)
    async def _bad_source(_r: Request, exc: UnsupportedSourceError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "unsupported_source"}, status_code=400)

    @app.exception_handler(ModelNotAvailableError)
    async def _bad_model(_r: Request, exc: ModelNotAvailableError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "model_unavailable"}, status_code=503)

    @app.exception_handler(ClipNotFoundError)
    async def _clip_not_found(_r: Request, exc: ClipNotFoundError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "clip_not_found"}, status_code=404)

    @app.exception_handler(LLMNotConfiguredError)
    async def _llm_missing(_r: Request, exc: LLMNotConfiguredError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "llm_not_configured"}, status_code=503)

    @app.exception_handler(HighlightSelectionError)
    async def _hl_err(_r: Request, exc: HighlightSelectionError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "highlight_selection_error"}, status_code=502)

    @app.exception_handler(TemplateNotFoundError)
    async def _template_not_found(_r: Request, exc: TemplateNotFoundError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "template_not_found"}, status_code=404)

    @app.exception_handler(SourceVideoUnavailableError)
    async def _no_src(_r: Request, exc: SourceVideoUnavailableError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "source_video_unavailable"}, status_code=409)

    @app.exception_handler(ReframeError)
    async def _reframe_err(_r: Request, exc: ReframeError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "reframe_error"}, status_code=500)

    @app.exception_handler(DomainError)
    async def _domain_err(_r: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse({"error": str(exc), "type": "domain_error"}, status_code=422)

    @app.exception_handler(Exception)
    async def _generic(_r: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro não tratado")
        return JSONResponse({"error": "internal_error", "detail": str(exc)}, status_code=500)
