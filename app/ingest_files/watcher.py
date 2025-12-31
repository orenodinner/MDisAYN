from __future__ import annotations

import threading
import time
from pathlib import Path
from queue import Queue, Empty
from typing import Callable, Iterable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .scanner import scan_paths


class DebounceQueue:
    def __init__(self, debounce_sec: float, on_ready: Callable[[Path], None]) -> None:
        self.debounce_sec = debounce_sec
        self.on_ready = on_ready
        self._lock = threading.Lock()
        self._pending: dict[str, float] = {}
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2)

    def submit(self, path: Path) -> None:
        with self._lock:
            self._pending[str(path)] = time.time()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            ready: list[str] = []
            with self._lock:
                for path_str, ts in list(self._pending.items()):
                    if now - ts >= self.debounce_sec:
                        ready.append(path_str)
                        self._pending.pop(path_str, None)
            for path_str in ready:
                self.on_ready(Path(path_str))
            time.sleep(0.5)


class WatchHandler(FileSystemEventHandler):
    def __init__(self, enqueue: Callable[[Path], None]) -> None:
        super().__init__()
        self.enqueue = enqueue

    def on_created(self, event) -> None:
        if not event.is_directory:
            self.enqueue(Path(event.src_path))

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self.enqueue(Path(event.src_path))

    def on_moved(self, event) -> None:
        if not event.is_directory:
            self.enqueue(Path(event.dest_path))


class Worker:
    def __init__(self, processor: Callable[[Path], None]) -> None:
        self.processor = processor
        self.queue: Queue[Path] = Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2)

    def submit(self, path: Path) -> None:
        self.queue.put(path)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                path = self.queue.get(timeout=0.5)
            except Empty:
                continue
            try:
                self.processor(path)
            finally:
                self.queue.task_done()


def start_watcher(
    roots: Iterable[Path], enqueue: Callable[[Path], None], recursive: bool
) -> Observer:
    observer = Observer()
    handler = WatchHandler(enqueue)
    for root in roots:
        if root.exists():
            observer.schedule(handler, str(root), recursive=recursive)
    observer.start()
    return observer


def start_periodic_scan(
    roots: Iterable[Path],
    recursive: bool,
    exclude_dirs: list[str],
    exclude_globs: list[str],
    enqueue: Callable[[Path], None],
    interval_sec: int,
    stop_event: threading.Event,
) -> threading.Thread:
    def _loop() -> None:
        while not stop_event.is_set():
            for path in scan_paths(roots, recursive, exclude_dirs, exclude_globs):
                enqueue(path)
            stop_event.wait(interval_sec)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread
