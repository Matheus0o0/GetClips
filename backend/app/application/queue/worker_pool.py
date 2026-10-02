"""Pool de workers consumindo a fila e executando o orquestrador."""
from __future__ import annotations

import asyncio
import logging

from app.application.orchestrator.job_orchestrator import JobOrchestrator
from app.application.queue.job_queue import JobQueue

logger = logging.getLogger(__name__)


class WorkerPool:
    def __init__(
        self,
        queue: JobQueue,
        orchestrator: JobOrchestrator,
        max_concurrent: int = 1,
    ) -> None:
        self._queue = queue
        self._orchestrator = orchestrator
        self._max = max(1, max_concurrent)
        self._tasks: list[asyncio.Task] = []
        self._stopping = False

    async def start(self) -> None:
        for i in range(self._max):
            task = asyncio.create_task(self._worker_loop(i), name=f"worker-{i}")
            self._tasks.append(task)
        logger.info("WorkerPool iniciado com %d worker(s)", self._max)

    async def stop(self) -> None:
        self._stopping = True
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _worker_loop(self, idx: int) -> None:
        while not self._stopping:
            try:
                job_id = await self._queue.dequeue()
            except asyncio.CancelledError:
                break
            try:
                logger.info("Worker %d executando job %s", idx, job_id)
                await self._orchestrator.run(job_id)
            except Exception:
                logger.exception("Worker %d falhou no job %s", idx, job_id)
            finally:
                self._queue.task_done()
