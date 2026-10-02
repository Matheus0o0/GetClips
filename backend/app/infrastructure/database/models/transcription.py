"""Modelo ORM de Transcription."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class TranscriptionModel(Base):
    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True
    )
    language_detected: Mapped[str] = mapped_column(String(16), default="unknown")
    language_probability: Mapped[float] = mapped_column(Float, default=0.0)
    model_used: Mapped[str] = mapped_column(String(64), default="")
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
