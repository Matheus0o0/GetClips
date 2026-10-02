"""ConnectionManager — mantém sockets abertos por job_id + broadcast global."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket

from app.core.events.job_events import DomainEvent, event_to_dict
from app.core.interfaces.event_bus import IEventBus

logger = logging.getLogger(__name__)

GLOBAL_CHANNEL = "*"


class WebSocketManager:
    def __init__(self) -> None:
        self._by_job: dict[str, set[WebSocket]] = defaultdict(set)
        self._global: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect_job(self, job_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._by_job[job_id].add(ws)

    async def connect_global(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._global.add(ws)

    async def disconnect(self, ws: WebSocket, job_id: str | None = None) -> None:
        async with self._lock:
            if job_id:
                self._by_job.get(job_id, set()).discard(ws)
            self._global.discard(ws)

    def bind_to_bus(self, bus: IEventBus) -> None:
        bus.subscribe(DomainEvent, self._on_event)

    async def _on_event(self, event: DomainEvent) -> None:
        payload = event_to_dict(event)
        targets: list[WebSocket] = []
        async with self._lock:
            targets.extend(self._by_job.get(event.job_id, set()))
            targets.extend(self._global)

        if not targets:
            return

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._global.discard(ws)
                    for peers in self._by_job.values():
                        peers.discard(ws)
