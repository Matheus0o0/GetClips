"""Contrato de barramento de eventos."""
from __future__ import annotations

from typing import Awaitable, Callable, Protocol, TypeVar, runtime_checkable

from app.core.events.job_events import DomainEvent

E = TypeVar("E", bound=DomainEvent)
Handler = Callable[[E], Awaitable[None]]


@runtime_checkable
class IEventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...

    def subscribe(self, event_type: type[E], handler: Handler) -> None: ...
