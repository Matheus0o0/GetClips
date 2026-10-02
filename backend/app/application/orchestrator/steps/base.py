"""Contrato base de step do pipeline."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.application.orchestrator.context import JobContext
from app.application.progress.progress_reporter import ProgressReporter


@runtime_checkable
class IPipelineStep(Protocol):
    async def run(self, ctx: JobContext, reporter: ProgressReporter) -> JobContext: ...
