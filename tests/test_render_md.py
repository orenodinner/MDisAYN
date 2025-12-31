import yaml
from datetime import datetime

from app.render_md import render_source_card


def test_render_source_card_basic(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "test.md.j2"
    template_path.write_text(
        """---
"""
        "title: \"{{ title }}\"\n"
        "tags:\n"
        "{% for tag in tags %}\n"
        "  - {{ tag }}\n"
        "{% endfor %}\n"
        "---\n"
        "# {{ title }}\n"
        "People: {% for p in people %}{{ p|wikilink }} {% endfor %}\n",
        encoding="utf-8",
    )

    payload = {
        "title": "Test Note",
        "tags": ["tag1", "tag2"],
        "people": ["Alice"],
        "summary": [],
        "decisions": [],
        "actions": [],
        "projects": [],
        "confidence": 0.9,
    }

    output = render_source_card(
        payload=payload,
        source_links=[],
        source_type="file",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        entities=[],
        template_path=template_path,
    )

    assert "# Test Note" in output
    assert "[[Alice]]" in output

    parts = output.split("---")
    assert len(parts) >= 3
    fm_content = parts[1]
    fm_data = yaml.safe_load(fm_content)
    assert fm_data["title"] == "Test Note"
    assert "tag1" in fm_data["tags"]
    assert "tag2" in fm_data["tags"]
