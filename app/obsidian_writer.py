from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


_INVALID_CHARS = re.compile(r"[<>:\\/?*\"|]")


def safe_filename(value: str, fallback: str) -> str:
    name = _INVALID_CHARS.sub("_", value).strip().strip(".")
    if not name:
        return fallback
    return name[:120]


def write_markdown(vault_path: Path, relative_path: Path, content: str) -> Path:
    target_path = vault_path / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        existing = target_path.read_text(encoding="utf-8")
        if existing == content:
            return target_path

    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, target_path)
    return target_path


def make_obsidian_path(
    vault_path: Path,
    sources_subdir: str,
    title: str,
    suffix: str,
    fallback: str,
) -> Path:
    safe = safe_filename(title, fallback)
    filename = f"{safe}_{suffix}.md"
    return Path(sources_subdir) / filename
