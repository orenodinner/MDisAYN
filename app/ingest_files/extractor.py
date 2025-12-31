from __future__ import annotations

import logging
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

BINARY_EXTENSIONS = {
    ".pdf",
    ".docx",
}

_logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    import docx
except ImportError:  # pragma: no cover - optional dependency
    docx = None


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            chunks.append(page_text)
    return "\n".join(chunks)


def _read_docx(path: Path) -> str:
    document = docx.Document(str(path))
    chunks = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    return "\n".join(chunks)


def extract_text(path: Path, max_bytes: int) -> Optional[Tuple[str, dict]]:
    if not path.exists() or not path.is_file():
        return None
    extension = path.suffix.lower()
    if extension not in TEXT_EXTENSIONS and extension not in BINARY_EXTENSIONS:
        return None
    size = path.stat().st_size
    if size > max_bytes:
        return None
    if extension in TEXT_EXTENSIONS:
        text = _read_text_file(path)
    elif extension == ".pdf":
        if PdfReader is None:
            _logger.warning("Skipping PDF because pypdf is not available: %s", path)
            return None
        text = _read_pdf(path)
    elif extension == ".docx":
        if docx is None:
            _logger.warning("Skipping DOCX because python-docx is not available: %s", path)
            return None
        text = _read_docx(path)
    else:
        return None
    metadata = {
        "extension": extension,
        "size_bytes": size,
    }
    return text, metadata
