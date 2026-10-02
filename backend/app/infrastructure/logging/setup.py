"""Bootstrap do logging."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import Settings
from app.infrastructure.logging.json_formatter import JsonFormatter


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    console = logging.StreamHandler()
    if settings.log_json:
        console.setFormatter(JsonFormatter())
    else:
        console.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    root.addHandler(console)

    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        settings.logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)
