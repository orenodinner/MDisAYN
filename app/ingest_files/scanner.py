from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import fnmatch
import os


def _is_excluded_dir(name: str, exclude_dirs: List[str]) -> bool:
    return name.lower() in exclude_dirs


def _is_excluded_file(path: Path, exclude_globs: List[str]) -> bool:
    name = path.name
    return any(fnmatch.fnmatch(name, pattern) for pattern in exclude_globs)


def scan_paths(
    roots: Iterable[Path],
    recursive: bool,
    exclude_dirs: List[str],
    exclude_globs: List[str],
) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if not _is_excluded_file(root, exclude_globs):
                yield root
            continue
        if recursive:
            for current_root, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if not _is_excluded_dir(d, exclude_dirs)]
                for filename in files:
                    path = Path(current_root) / filename
                    if _is_excluded_file(path, exclude_globs):
                        continue
                    yield path
        else:
            for path in root.iterdir():
                if path.is_file() and not _is_excluded_file(path, exclude_globs):
                    yield path
