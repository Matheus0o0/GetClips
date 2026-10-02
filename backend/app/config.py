"""Configurações da aplicação (Pydantic Settings)."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    storage_root: Path = Path("../storage")
    database_url: str = "sqlite+aiosqlite:///../storage/local_transcriber.db"

    default_model: str = "distil-large-v3"
    default_language: str = "pt"
    device: str = "auto"            # auto | cuda | cpu
    compute_type: str = "auto"      # auto | float16 | int8_float16 | int8
    beam_size: int = 5

    max_concurrent_jobs: int = 1
    auto_cleanup_temp_hours: int = 24

    # yt-dlp: opcional — usa sessão logada do navegador para evitar
    # "Video unavailable" (chrome, edge, firefox, brave, ...). Vazio desativa.
    ytdlp_cookies_from_browser: str = ""

    log_level: str = "INFO"
    log_json: bool = True

    # Seleção de cortes — provedor de LLM
    # Valores: ollama (local, padrão) | openai | anthropic | none (heurística local)
    highlight_provider: str = "ollama"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-sonnet-4-6"
    highlight_max_clips: int = 5
    highlight_clip_duration_min: int = 30
    highlight_clip_duration_max: int = 60

    # Ollama (LLM local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout: float = 120.0

    # Reenquadramento vertical (100% local)
    reframe_detection_stride: int = 5        # roda detecção a cada N frames
    reframe_smoothing: str = "kalman"  # moving_average | kalman
    reframe_output_resolution: str = "1080x1920"

    @field_validator("storage_root", mode="after")
    @classmethod
    def _resolve_storage(cls, v: Path) -> Path:
        return v.expanduser().resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def downloads_dir(self) -> Path:
        return self.storage_root / "downloads"

    @property
    def audio_dir(self) -> Path:
        return self.storage_root / "audio"

    @property
    def outputs_dir(self) -> Path:
        return self.storage_root / "outputs"

    @property
    def subtitles_dir(self) -> Path:
        return self.outputs_dir / "subtitles"

    @property
    def transcripts_dir(self) -> Path:
        return self.outputs_dir / "transcripts"

    @property
    def models_dir(self) -> Path:
        return self.storage_root / "models"

    @property
    def logs_dir(self) -> Path:
        return self.storage_root / "logs"

    @property
    def temp_dir(self) -> Path:
        return self.storage_root / "temp"

    @property
    def clips_dir(self) -> Path:
        return self.storage_root / "clips"

    @property
    def reframe_output_size(self) -> tuple[int, int]:
        w, h = self.reframe_output_resolution.lower().split("x")
        return int(w), int(h)

    def ensure_dirs(self) -> None:
        for d in (
            self.storage_root,
            self.downloads_dir,
            self.audio_dir,
            self.outputs_dir,
            self.subtitles_dir,
            self.transcripts_dir,
            self.models_dir,
            self.logs_dir,
            self.temp_dir,
            self.clips_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
