from app.normalize import normalize_llm_payload, parse_json_from_text


def test_parse_json_embedded_in_text():
    raw = """Here is the JSON:
    ```json
    {"title": "Test", "confidence": 0.9}
    ```
    End of text."""
    data = parse_json_from_text(raw)
    assert data is not None
    assert data["title"] == "Test"


def test_normalize_payload_defaults():
    result = normalize_llm_payload({})
    assert result.title == "Untitled"
    assert result.confidence == 0.5
