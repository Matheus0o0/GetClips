"""Modelos Pydantic para configuração de templates de edição."""
from __future__ import annotations

from pydantic import BaseModel, Field


class VideoConfig(BaseModel):
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"


class TrackingConfig(BaseModel):
    enabled: bool = True
    target: str = "primary_person"   # primary_person | center
    smoothing: float = Field(0.8, ge=0.0, le=1.0)
    dead_zone_px: int = Field(30, ge=0)


class CaptionConfig(BaseModel):
    enabled: bool = True
    words_per_block: int = Field(3, ge=1, le=8)
    max_chars_per_block: int = Field(25, ge=5, le=80)
    style: str = "bold_dynamic"      # bold_dynamic | minimal | karaoke | podcast | clean
    font_family: str = "Inter"
    font_size: int = Field(72, ge=20, le=200)
    font_weight: int = Field(800, ge=100, le=900)
    position_y: float = Field(0.75, ge=0.0, le=1.0)  # 0 = topo, 1 = rodapé
    position_x: float = Field(0.5, ge=0.0, le=1.0)   # 0 = esq, 1 = dir
    text_align: str = "center"
    color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_width: int = Field(4, ge=0, le=20)
    background_color: str = "transparent"
    animation: str = "pop"           # none | pop | fade | word_by_word | karaoke
    highlight_emphasis: bool = True
    highlight_color: str = "#FFE000"


class CameraConfig(BaseModel):
    dynamic_zoom: bool = True
    max_zoom: float = Field(1.12, ge=1.0, le=2.0)
    zoom_smoothing: float = Field(0.9, ge=0.0, le=1.0)


class CutsConfig(BaseModel):
    jump_cuts: bool = True
    remove_silence: bool = True
    silence_threshold_db: float = Field(-35.0, le=0.0)
    min_silence_duration_ms: int = Field(400, ge=50)


class AnalysisConfig(BaseModel):
    max_clips: int = Field(5, ge=1, le=20)
    duration_min: int = Field(30, ge=5)
    duration_max: int = Field(60, ge=10)


class EditingTemplateConfig(BaseModel):
    video: VideoConfig = Field(default_factory=VideoConfig)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    captions: CaptionConfig = Field(default_factory=CaptionConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    cuts: CutsConfig = Field(default_factory=CutsConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
