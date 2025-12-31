from app.config import load_config


def test_load_config_from_env(tmp_path, monkeypatch):
    vault_path = tmp_path / "vault"
    data_lake_path = tmp_path / "data_lake"
    watch_path = tmp_path / "input"

    monkeypatch.setenv("VAULT_PATH", str(vault_path))
    monkeypatch.setenv("DATA_LAKE_PATH", str(data_lake_path))
    monkeypatch.setenv("META_DB_PATH", str(tmp_path / "meta.db"))
    monkeypatch.setenv("WATCH_PATHS", str(watch_path))
    monkeypatch.setenv("WATCH_RECURSIVE", "false")
    monkeypatch.setenv("SCAN_INTERVAL_SEC", "10")
    monkeypatch.setenv("DEBOUNCE_SEC", "1")
    monkeypatch.setenv("MAX_FILE_MB", "1")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("LLM_MODEL", "local-model")
    monkeypatch.setenv("LLM_TIMEOUT_SEC", "5")
    monkeypatch.setenv("LLM_MAX_RETRIES", "1")
    monkeypatch.setenv("LLM_MAX_INPUT_CHARS", "100")
    monkeypatch.setenv("LLM_LANGUAGE", "ja")
    monkeypatch.setenv("OBSIDIAN_SOURCES_SUBDIR", "90_Sources/file")
    monkeypatch.setenv("LOG_EVENTS", "false")

    config = load_config()
    assert config.vault_path == vault_path
    assert config.data_lake_path == data_lake_path
    assert config.watch_paths == [watch_path]
    assert config.watch_recursive is False
    assert config.scan_interval_sec == 10
    assert config.debounce_sec == 1.0
    assert config.max_file_bytes == 1024 * 1024
    assert config.llm_max_input_chars == 100
    assert config.log_events is False
