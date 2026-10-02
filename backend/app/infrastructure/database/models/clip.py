"""Modelo ORM de Clip (corte vertical gerado)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ClipModel(Base):
    __tablename__ = "clips"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("jobs.id", ondelete="CASCADE"), index=True
    )
    inicio: Mapped[float] = mapped_column(Float)
    fim: Mapped[float] = mapped_column(Float)
    hook_text: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    motivo: Mapped[str] = mapped_column(Text, default="")
    crop_mode: Mapped[str] = mapped_column(String(32), default="dynamic")
    status: Mapped[str] = mapped_column(String(32), index=True, default="pending")
    output_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
