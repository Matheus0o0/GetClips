"""Schema validado do Editing Plan produzido pelo LLM.

O renderer nunca executa JSON bruto do LLM — sempre passa por aqui.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CameraEvent(BaseModel):
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    scale: float = Field(1.0, ge=1.0, le=2.0)

    @model_validator(mode="after")
    def end_after_start(self) -> "CameraEvent":
        if self.end <= self.start:
            raise ValueError("end deve ser maior que start")
        return self


class RemoveSegment(BaseModel):
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    reason: str = ""   # filler | silence | offtopic

    @model_validator(mode="after")
    def end_after_start(self) -> "RemoveSegment":
        if self.end <= self.start:
            raise ValueError("end deve ser maior que start")
        return self


class EmphasisWord(BaseModel):
    text: str
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)


class EditingPlan(BaseModel):
    clip_start: float = Field(ge=0.0)
    clip_end: float = Field(ge=0.0)
    hook_text: str = ""
    score: float = Field(0.0, ge=0.0, le=1.0)
    rationale: str = ""
    emphasis: list[EmphasisWord] = Field(default_factory=list)
    camera_events: list[CameraEvent] = Field(default_factory=list)
    remove: list[RemoveSegment] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_clip(self) -> "EditingPlan":
        if self.clip_end <= self.clip_start:
            raise ValueError("clip_end deve ser maior que clip_start")
        return self

    @property
    def duration(self) -> float:
        return self.clip_end - self.clip_start
