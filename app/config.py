from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _split_list(value: str) -> List[str]:
    if not value:
        return []
    parts = [p.strip() for p in value.replace(";", ",").split(",")]
    return [p for p in parts if p]


@dataclass(frozen=True)
class AppConfig:
    vault_path: Path
    data_lake_path: Path
    watch_paths: List[Path]
    watch_recursive: bool
    exclude_dirs: List[str]
    exclude_globs: List[str]
    scan_interval_sec: int
    debounce_sec: float
    max_file_bytes: int
    llm_base_url: str
    llm_model: str
    llm_timeout_sec: float
    llm_max_retries: int
    llm_max_input_chars: int
    llm_language: str
    obsidian_sources_subdir: str
    db_path: Path
    log_events: bool

    @property
    def raw_dir(self) -> Path:
        return self.data_lake_path / "raw"

    @property
    def extracted_dir(self) -> Path:
        return self.data_lake_path / "extracted"


def load_config() -> AppConfig:
    cwd = Path.cwd()
    _load_dotenv(cwd / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", "./vault")).expanduser()
    data_lake_path = Path(os.getenv("DATA_LAKE_PATH", "./data_lake")).expanduser()

    watch_paths_raw = os.getenv("WATCH_PATHS", "")
    if watch_paths_raw:
        watch_paths = [Path(p).expanduser() for p in _split_list(watch_paths_raw)]
    else:
        watch_paths = [Path.home() / "Documents"]

    watch_recursive = os.getenv("WATCH_RECURSIVE", "true").lower() in {"1", "true", "yes"}
    exclude_dirs = _split_list(os.getenv("WATCH_EXCLUDE_DIRS", ".git,node_modules,.venv,__pycache__,.obsidian"))
    exclude_globs = _split_list(
        os.getenv(
            "WATCH_EXCLUDE_GLOBS",
            "*.tmp,*.log,*.exe,*.dll,*.zip,*.7z,*.rar,*.png,*.jpg,*.jpeg,*.gif,*.mp4,*.mov",
        )
    )
    scan_interval_sec = int(os.getenv("SCAN_INTERVAL_SEC", "60"))
    debounce_sec = float(os.getenv("DEBOUNCE_SEC", "2"))
    max_file_mb = int(os.getenv("MAX_FILE_MB", "5"))
    max_file_bytes = max_file_mb * 1024 * 1024

    llm_base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    llm_model = os.getenv("LLM_MODEL", "local-model")
    llm_timeout_sec = float(os.getenv("LLM_TIMEOUT_SEC", "30"))
    llm_max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    llm_max_input_chars = int(os.getenv("LLM_MAX_INPUT_CHARS", "8000"))
    llm_language = os.getenv("LLM_LANGUAGE", "ja")

    obsidian_sources_subdir = os.getenv("OBSIDIAN_SOURCES_SUBDIR", "90_Sources/file")
    db_path = Path(os.getenv("META_DB_PATH", str(data_lake_path / "meta.db")))
    log_events = os.getenv("LOG_EVENTS", "true").lower() in {"1", "true", "yes"}

    return AppConfig(
        vault_path=vault_path,
        data_lake_path=data_lake_path,
        watch_paths=watch_paths,
        watch_recursive=watch_recursive,
        exclude_dirs=[d.lower() for d in exclude_dirs],
        exclude_globs=exclude_globs,
        scan_interval_sec=scan_interval_sec,
        debounce_sec=debounce_sec,
        max_file_bytes=max_file_bytes,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_timeout_sec=llm_timeout_sec,
        llm_max_retries=llm_max_retries,
        llm_max_input_chars=llm_max_input_chars,
        llm_language=llm_language,
        obsidian_sources_subdir=obsidian_sources_subdir,
        db_path=db_path,
        log_events=log_events,
    )
