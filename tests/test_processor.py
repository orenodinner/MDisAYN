from app.ingest_files.processor import process_file
from app.db import MetadataDB


def test_process_file_flow(mock_config, mocker):
    input_dir = mock_config.watch_paths[0]
    input_file = input_dir / "test.txt"
    input_file.write_text("Hello World", encoding="utf-8")

    mock_llm = mocker.Mock()
    mock_llm.normalize.return_value = {
        "title": "Hello Note",
        "summary": ["Greeting"],
        "decisions": [],
        "actions": [],
        "entities": [],
        "tags": [],
        "projects": [],
        "people": [],
        "confidence": 1.0,
    }

    db = MetadataDB(mock_config.db_path, log_events=True)
    result_path = process_file(input_file, mock_config, db, mock_llm)

    assert result_path is not None
    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert "# Hello Note" in content
    assert db.count_sources("file") == 1

    db.close()
