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
    from pypdf.errors import PdfReadError
except ImportError:  # pragma: no cover - optional dependency
    PdfReader = None
    PdfReadError = None

try:
    import docx
except ImportError:  # pragma: no cover - optional dependency
    docx = None


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> Optional[str]:
    try:
        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:
                _logger.warning("PDF page extract failed: %s (%s)", path, exc)
                continue
            if page_text:
                chunks.append(page_text)
        return "\n".join(chunks)
    except Exception as exc:
        _logger.warning("PDF read failed: %s (%s)", path, exc)
        return None


def _read_docx(path: Path) -> Optional[str]:
    try:
        document = docx.Document(str(path))
        try:
            chunks = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        except Exception as exc:
            _logger.warning("DOCX paragraph extract failed: %s (%s)", path, exc)
            return None
        return "\n".join(chunks)
    except Exception as exc:
        _logger.warning("DOCX read failed: %s (%s)", path, exc)
        return None


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
        try:
            text = _read_pdf(path)
        except Exception as exc:
            _logger.warning("PDF extract failed: %s (%s)", path, exc)
            return None
    elif extension == ".docx":
        if docx is None:
            _logger.warning("Skipping DOCX because python-docx is not available: %s", path)
            return None
        try:
            text = _read_docx(path)
        except Exception as exc:
            _logger.warning("DOCX extract failed: %s (%s)", path, exc)
            return None
    else:
        return None
    if text is None:
        return None
    metadata = {
        "extension": extension,
        "size_bytes": size,
    }
    return text, metadata
