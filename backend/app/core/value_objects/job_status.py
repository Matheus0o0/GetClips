"""Máquina de estados de um Job."""
from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStage(StrEnum):
    QUEUED = "QUEUED"
    DOWNLOADING = "DOWNLOADING"
    EXTRACTING_AUDIO = "EXTRACTING_AUDIO"
    TRANSCRIBING = "TRANSCRIBING"
    GENERATING_SUBTITLES = "GENERATING_SUBTITLES"
    FINALIZING = "FINALIZING"
    DONE = "DONE"


TERMINAL_STATUSES: frozenset[JobStatus] = frozenset(
    {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
)


def is_terminal(status: JobStatus) -> bool:
    return status in TERMINAL_STATUSES
