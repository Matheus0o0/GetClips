"""Entidade Job."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.value_objects import JobStage, JobStatus, Language, ModelType


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass(slots=True)
class JobParams:
    model: ModelType = ModelType.DISTIL_LARGE_V3
    language: Language = Language.AUTO
    beam_size: int = 5
    output_formats: tuple[str, ...] = ("srt", "vtt", "txt", "md")
    audio_only: bool = False
    keep_source_video: bool = True


@dataclass(slots=True)
class Job:
    id: str = field(default_factory=_new_id)
    source_url: str | None = None
    source_file: str | None = None
    title: str | None = None

    status: JobStatus = JobStatus.PENDING
    stage: JobStage = JobStage.QUEUED
    progress: float = 0.0
    message: str = ""
    error_message: str | None = None

    params: JobParams = field(default_factory=JobParams)
    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=_utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def mark_started(self) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = _utcnow()

    def mark_completed(self) -> None:
        self.status = JobStatus.COMPLETED
        self.stage = JobStage.DONE
        self.progress = 1.0
        self.finished_at = _utcnow()

    def mark_failed(self, message: str) -> None:
        self.status = JobStatus.FAILED
        self.error_message = message
        self.finished_at = _utcnow()

    def mark_cancelled(self) -> None:
        self.status = JobStatus.CANCELLED
        self.finished_at = _utcnow()

    def update_progress(self, stage: JobStage, progress: float, message: str = "") -> None:
        self.stage = stage
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message

    @property
    def elapsed_seconds(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.finished_at or _utcnow()
        started = self.started_at
        # SQLite não persiste tzinfo; normaliza para UTC-aware antes da subtração
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return (end - started).total_seconds()
