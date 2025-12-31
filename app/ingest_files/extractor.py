from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".log",
    ".ini",
    ".cfg",
    ".toml",
}


def extract_text(path: Path, max_bytes: int) -> Optional[Tuple[str, dict]]:
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    size = path.stat().st_size
    if size > max_bytes:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata = {
        "extension": path.suffix.lower(),
        "size_bytes": size,
    }
    return text, metadata
