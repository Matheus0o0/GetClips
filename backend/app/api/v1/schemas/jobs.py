"""DTOs de Jobs."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.entities import Job, MediaFile
from app.core.entities.job import JobParams
from app.core.value_objects import Language, ModelType


class JobParamsDTO(BaseModel):
    model: ModelType = ModelType.DISTIL_LARGE_V3
    language: Language = Language.AUTO
    beam_size: int = Field(5, ge=1, le=10)
    output_formats: list[str] = Field(default_factory=lambda: ["srt", "vtt", "txt", "md"])
    audio_only: bool = False
    keep_source_video: bool = True

    def to_entity(self) -> JobParams:
        return JobParams(
            model=self.model,
            language=self.language,
            beam_size=self.beam_size,
            output_formats=tuple(self.output_formats),
            audio_only=self.audio_only,
            keep_source_video=self.keep_source_video,
        )


class CreateJobRequest(BaseModel):
    url: str | None = None
    file_path: str | None = None
    params: JobParamsDTO = Field(default_factory=JobParamsDTO)


class JobDTO(BaseModel):
    id: str
    source_url: str | None
    source_file: str | None
    title: str | None
    status: str
    stage: str
    progress: float
    message: str
    error_message: str | None
    params: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    elapsed_seconds: float | None

    @classmethod
    def from_entity(cls, j: Job) -> "JobDTO":
        return cls(
            id=j.id,
            source_url=j.source_url,
            source_file=j.source_file,
            title=j.title,
            status=j.status.value,
            stage=j.stage.value,
            progress=j.progress,
            message=j.message,
            error_message=j.error_message,
            params={
                "model": j.params.model.value,
                "language": j.params.language.value,
                "beam_size": j.params.beam_size,
                "output_formats": list(j.params.output_formats),
                "audio_only": j.params.audio_only,
                "keep_source_video": j.params.keep_source_video,
            },
            metadata=j.metadata,
            created_at=j.created_at,
            started_at=j.started_at,
            finished_at=j.finished_at,
            elapsed_seconds=j.elapsed_seconds,
        )


class MediaFileDTO(BaseModel):
    path: str
    name: str
    kind: str
    format: str
    size_bytes: int
    duration_seconds: float | None

    @classmethod
    def from_entity(cls, m: MediaFile) -> "MediaFileDTO":
        return cls(
            path=str(m.path),
            name=m.name,
            kind=m.kind.value,
            format=m.format,
            size_bytes=m.size_bytes,
            duration_seconds=m.duration_seconds,
        )


class JobDetailDTO(BaseModel):
    job: JobDTO
    media: list[MediaFileDTO]
    transcription_available: bool


class SegmentDTO(BaseModel):
    index: int
    start_ms: int
    end_ms: int
    text: str
    confidence: float


class TranscriptionDTO(BaseModel):
    full_text: str
    language_detected: str
    language_probability: float
    model_used: str
    duration_seconds: float
    segments: list[SegmentDTO]


class RerunRequest(BaseModel):
    model: ModelType | None = None
    language: Language | None = None
    beam_size: int | None = Field(None, ge=1, le=10)
    output_formats: list[str] | None = None
    audio_only: bool | None = None
