"""Pipeline sequencial de steps."""
from __future__ import annotations

import logging

from app.application.orchestrator.context import JobContext
from app.application.orchestrator.steps.base import IPipelineStep
from app.application.progress.progress_reporter import ProgressReporter
from app.core.exceptions import JobCancelledError

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, steps: list[IPipelineStep], reporter: ProgressReporter) -> None:
        self._steps = steps
        self._reporter = reporter

    async def execute(self, ctx: JobContext) -> JobContext:
        for step in self._steps:
            if ctx.is_cancelled:
                raise JobCancelledError(ctx.job.id)
            logger.info(
                "Executando step",
                extra={"job_id": ctx.job.id, "component": step.__class__.__name__},
            )
            ctx = await step.run(ctx, self._reporter)
        return ctx
