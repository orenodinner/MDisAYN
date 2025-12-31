from app.db import MetadataDB


def test_upsert_source(tmp_path):
    db_path = tmp_path / "test.db"
    db = MetadataDB(db_path)

    db.upsert_source("file", "path/to/A", "hash1", "raw", "ext", "obs")
    assert db.count_sources("file") == 1

    db.upsert_source("file", "path/to/A", "hash2", "raw", "ext", "obs_new")
    assert db.count_sources("file") == 1

    row = db.get_source("file", "path/to/A")
    assert row["content_hash"] == "hash2"

    db.close()
