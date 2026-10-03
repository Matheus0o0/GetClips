"""Pipeline sequencial de steps."""
from __future__ import annotations

import logging
import time

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
        job_start = time.monotonic()
        for step in self._steps:
            if ctx.is_cancelled:
                raise JobCancelledError(ctx.job.id)
            name = step.__class__.__name__
            t0 = time.monotonic()
            logger.info("Iniciando step %s", name, extra={"job_id": ctx.job.id, "component": name})
            ctx = await step.run(ctx, self._reporter)
            elapsed = time.monotonic() - t0
            logger.info(
                "Step %s concluído em %.1fs",
                name,
                elapsed,
                extra={"job_id": ctx.job.id, "component": name, "elapsed_s": round(elapsed, 1)},
            )
        total = time.monotonic() - job_start
        logger.info("Pipeline concluído em %.1fs total", total, extra={"job_id": ctx.job.id})
        return ctx
