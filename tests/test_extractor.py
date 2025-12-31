import pytest

from app.ingest_files import extractor


def test_extract_text_plain(tmp_path):
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")
    result = extractor.extract_text(path, max_bytes=1024)
    assert result is not None
    text, metadata = result
    assert text == "hello"
    assert metadata["extension"] == ".txt"


def test_extract_text_unsupported(tmp_path):
    path = tmp_path / "note.bin"
    path.write_bytes(b"x")
    assert extractor.extract_text(path, max_bytes=1024) is None


def test_extract_pdf(tmp_path):
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as handle:
        writer.write(handle)

    result = extractor.extract_text(path, max_bytes=1024 * 1024)
    assert result is not None
    text, metadata = result
    assert metadata["extension"] == ".pdf"
    assert isinstance(text, str)


def test_extract_docx(tmp_path):
    pytest.importorskip("docx")
    import docx

    path = tmp_path / "sample.docx"
    document = docx.Document()
    document.add_paragraph("Hello Docx")
    document.save(path)

    result = extractor.extract_text(path, max_bytes=1024 * 1024)
    assert result is not None
    text, metadata = result
    assert metadata["extension"] == ".docx"
    assert "Hello Docx" in text
