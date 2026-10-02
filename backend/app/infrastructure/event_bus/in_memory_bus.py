"""Barramento de eventos em memória (async pub/sub)."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from app.core.events.job_events import DomainEvent

logger = logging.getLogger(__name__)


class InMemoryEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Any]] = defaultdict(list)
        self._wildcard: list[Any] = []

    def subscribe(self, event_type: type[DomainEvent], handler: Any) -> None:
        if event_type is DomainEvent:
            self._wildcard.append(handler)
        else:
            self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = list(self._handlers.get(type(event), []))
        handlers.extend(self._wildcard)
        if not handlers:
            return

        results = await asyncio.gather(
            *(self._run(h, event) for h in handlers), return_exceptions=True
        )
        for res in results:
            if isinstance(res, Exception):
                logger.warning("Handler falhou: %s", res)

    @staticmethod
    async def _run(handler: Any, event: DomainEvent) -> None:
        await handler(event)
