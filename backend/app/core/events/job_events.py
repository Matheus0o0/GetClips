"""Eventos de domínio relacionados a Jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(slots=True)
class DomainEvent:
    job_id: str
    timestamp: datetime = field(default_factory=_now)

    @property
    def type(self) -> str:
        return self.__class__.__name__


@dataclass(slots=True)
class JobCreatedEvent(DomainEvent):
    source: str = ""


@dataclass(slots=True)
class JobStageChangedEvent(DomainEvent):
    stage: str = ""
    message: str = ""


@dataclass(slots=True)
class JobProgressEvent(DomainEvent):
    stage: str = ""
    progress: float = 0.0
    message: str = ""
    eta_seconds: float | None = None


@dataclass(slots=True)
class JobCompletedEvent(DomainEvent):
    outputs: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class JobFailedEvent(DomainEvent):
    error: str = ""
    stage: str = ""


@dataclass(slots=True)
class JobCancelledEvent(DomainEvent):
    pass


def event_to_dict(event: DomainEvent) -> dict[str, Any]:
    """Serializa qualquer DomainEvent para JSON."""
    from dataclasses import asdict

    d = asdict(event)
    d["type"] = event.type
    d["timestamp"] = event.timestamp.isoformat()
    return d
