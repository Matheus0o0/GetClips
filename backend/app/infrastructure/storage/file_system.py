"""Helpers de sistema de arquivos."""
from __future__ import annotations

import shutil
from pathlib import Path


def safe_delete(path: Path) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink(missing_ok=True)
    except OSError:
        pass


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
