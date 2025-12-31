from pathlib import Path

from app.obsidian_writer import safe_filename, write_markdown


def test_safe_filename_sanitizes():
    name = safe_filename("a<>:\\/?*\"|b", "fallback")
    assert "<" not in name
    assert ">" not in name
    assert "?" not in name
    assert name


def test_write_markdown_idempotent(tmp_path):
    vault = tmp_path / "vault"
    rel_path = Path("notes/test.md")
    content = "hello"

    first_path = write_markdown(vault, rel_path, content)
    assert first_path.exists()
    assert first_path.read_text(encoding="utf-8") == content

    second_path = write_markdown(vault, rel_path, content)
    assert second_path == first_path
