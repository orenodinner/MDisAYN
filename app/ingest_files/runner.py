from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Iterable

from rich.progress import track

from ..config import AppConfig
from ..db import MetadataDB
from ..llm_client import LLMClient
from .processor import process_file
from .scanner import scan_paths
from .watcher import DebounceQueue, Worker, start_periodic_scan, start_watcher


def _make_worker(config: AppConfig) -> tuple[MetadataDB, LLMClient, Worker]:
    db = MetadataDB(config.db_path, log_events=config.log_events)
    llm = LLMClient(
        base_url=config.llm_base_url,
        model=config.llm_model,
        timeout_sec=config.llm_timeout_sec,
        max_retries=config.llm_max_retries,
        language=config.llm_language,
    )

    def _processor(path: Path) -> None:
        try:
            process_file(path, config, db, llm)
        except Exception as exc:
            db.log_event("file_failed", {"path": str(path), "error": str(exc)})

    worker = Worker(_processor)
    return db, llm, worker


def run_watch_loop(config: AppConfig) -> None:
    db, _, worker = _make_worker(config)
    worker.start()

    debouncer = DebounceQueue(config.debounce_sec, worker.submit)
    debouncer.start()

    observer = start_watcher(config.watch_paths, debouncer.submit, config.watch_recursive)

    stop_event = threading.Event()
    scanner_thread = start_periodic_scan(
        config.watch_paths,
        config.watch_recursive,
        config.exclude_dirs,
        config.exclude_globs,
        debouncer.submit,
        config.scan_interval_sec,
        stop_event,
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        scanner_thread.join(timeout=2)
        observer.stop()
        observer.join(timeout=2)
        debouncer.stop()
        worker.stop()
        db.close()


def run_backfill(config: AppConfig, force: bool = False) -> None:
    db = MetadataDB(config.db_path, log_events=config.log_events)
    llm = LLMClient(
        base_url=config.llm_base_url,
        model=config.llm_model,
        timeout_sec=config.llm_timeout_sec,
        max_retries=config.llm_max_retries,
        language=config.llm_language,
    )

    paths = list(
        scan_paths(
            config.watch_paths,
            config.watch_recursive,
            config.exclude_dirs,
            config.exclude_globs,
        )
    )
    for path in track(paths, description="一括処理", total=len(paths)):
        try:
            process_file(path, config, db, llm, force=force)
        except Exception as exc:
            db.log_event("file_failed", {"path": str(path), "error": str(exc)})

    db.close()
