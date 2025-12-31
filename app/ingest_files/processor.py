from __future__ import annotations

import fnmatch
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console

from ..config import AppConfig
from ..db import MetadataDB
from ..llm_client import LLMClient
from ..obsidian_writer import make_obsidian_path, write_markdown
from ..render_md import render_source_card
from .extractor import extract_text


_console = Console()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _hash_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _is_excluded(path: Path, config: AppConfig) -> bool:
    for part in path.parts:
        if part.lower() in config.exclude_dirs:
            return True
    name = path.name
    return any(fnmatch.fnmatch(name, pattern) for pattern in config.exclude_globs)


def process_file(
    path: Path,
    config: AppConfig,
    db: MetadataDB,
    llm: LLMClient,
    force: bool = False,
) -> Optional[Path]:
    if not path.exists() or not path.is_file():
        return None
    if _is_excluded(path, config):
        return None

    status = _console.status(f"抽出中: {path.name}", spinner="dots")
    status.start()
    try:
        extracted = extract_text(path, config.max_file_bytes)
        if not extracted:
            return None

        text, _ = extracted
        content_hash = _hash_text(text)

        existing = db.get_source("file", str(path))
        if not force and existing and existing.get("content_hash") == content_hash:
            return Path(existing.get("obsidian_path")) if existing.get("obsidian_path") else None

        same_hash = db.get_source_by_hash("file", content_hash)
        if not force and same_hash and same_hash.get("obsidian_path"):
            db.upsert_source(
                source_type="file",
                source_key=str(path),
                content_hash=content_hash,
                raw_path=same_hash.get("raw_path"),
                extracted_path=same_hash.get("extracted_path"),
                obsidian_path=same_hash.get("obsidian_path"),
                metadata={"note": "deduplicated"},
            )
            return Path(same_hash.get("obsidian_path"))

        raw_dir = config.raw_dir / "file"
        extracted_dir = config.extracted_dir / "file"
        raw_dir.mkdir(parents=True, exist_ok=True)
        extracted_dir.mkdir(parents=True, exist_ok=True)

        raw_bytes = path.read_bytes()
        raw_hash = _hash_bytes(raw_bytes)
        raw_filename = f"{raw_hash}{path.suffix.lower()}"
        raw_path = raw_dir / raw_filename
        if not raw_path.exists():
            raw_path.write_bytes(raw_bytes)

        extracted_path = extracted_dir / f"{content_hash}.txt"
        if not extracted_path.exists():
            extracted_path.write_text(text, encoding="utf-8")

        source_info: Dict[str, str] = {
            "path": str(path),
            "raw_path": str(raw_path),
            "size_bytes": str(path.stat().st_size),
            "mtime": str(path.stat().st_mtime),
        }
        truncated_text = text[: config.llm_max_input_chars]

        status.update(f"正規化中 (LLM待機): {path.name}")
        payload = llm.normalize(truncated_text, source_info)

        created_at = datetime.now(timezone.utc)
        source_links = [
            f"Original: {path.resolve().as_uri()}",
            f"Raw: {raw_path.resolve().as_uri()}",
        ]
        markdown = render_source_card(
            payload=payload,
            source_links=source_links,
            source_type="file",
            created_at=created_at,
            entities=payload.get("entities", []),
            template_path=config.obsidian_template_path,
        )

        suffix = content_hash[:8]
        obsidian_rel = make_obsidian_path(
            config.vault_path,
            config.obsidian_sources_subdir,
            payload.get("title", path.stem),
            suffix,
            fallback=path.stem or content_hash[:8],
        )

        status.update(f"書き込み中: {path.name}")
        obsidian_path = write_markdown(config.vault_path, obsidian_rel, markdown)

        db.upsert_source(
            source_type="file",
            source_key=str(path),
            content_hash=content_hash,
            raw_path=str(raw_path),
            extracted_path=str(extracted_path),
            obsidian_path=str(obsidian_path),
            metadata={"source": "file"},
        )
        db.log_event("file_processed", {"path": str(path), "hash": content_hash})
        _console.print(f"[bold green]完了[/bold green] [cyan]{obsidian_path}[/cyan]")
    finally:
        status.stop()

    return obsidian_path
