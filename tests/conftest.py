import pytest
from app.config import AppConfig
from app.db import MetadataDB


@pytest.fixture
def mock_config(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    return AppConfig(
        vault_path=tmp_path / "vault",
        data_lake_path=tmp_path / "data_lake",
        watch_paths=[input_dir],
        watch_recursive=True,
        exclude_dirs=[],
        exclude_globs=[],
        scan_interval_sec=60,
        debounce_sec=1.0,
        max_file_bytes=5 * 1024 * 1024,
        llm_base_url="http://127.0.0.1:1234/v1",
        llm_model="local-model",
        llm_timeout_sec=5.0,
        llm_max_retries=0,
        llm_max_input_chars=8000,
        llm_language="ja",
        llm_json_mode=True,
        obsidian_sources_subdir="90_Sources/file",
        db_path=tmp_path / "meta.db",
        log_events=True,
    )


@pytest.fixture
def db(mock_config):
    db = MetadataDB(mock_config.db_path, log_events=True)
    yield db
    db.close()
