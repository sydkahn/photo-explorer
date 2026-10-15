import os
import sqlite3
import time

import pytest

from photo_explorer import catalog, scanner


def _meta(path):
    return scanner.get_file_metadata(path)


def test_init_db_creates_tables_and_sets_version(tmp_path):
    db_path = tmp_path / "data" / "catalog.db"
    conn = catalog.init_db(db_path=db_path)
    try:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "files" in tables
        assert conn.execute("PRAGMA user_version").fetchone()[0] == catalog.CURRENT_SCHEMA_VERSION
    finally:
        catalog.close_db(conn)


def test_init_db_is_idempotent(tmp_path):
    db_path = tmp_path / "catalog.db"
    catalog.close_db(catalog.init_db(db_path=db_path))
    conn = catalog.init_db(db_path=db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == catalog.CURRENT_SCHEMA_VERSION
    finally:
        catalog.close_db(conn)


def test_unsupported_newer_schema_version_raises_clear_error(tmp_path):
    db_path = tmp_path / "catalog.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(f"PRAGMA user_version = {catalog.CURRENT_SCHEMA_VERSION + 1}")
    conn.commit()
    conn.close()

    with pytest.raises(catalog.SchemaVersionError) as excinfo:
        catalog.init_db(db_path=db_path)
    assert "schema version" in str(excinfo.value).lower()


def test_rescan_same_path_does_not_create_duplicate_rows(tmp_path):
    db_path = tmp_path / "catalog.db"
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    with catalog.connect(db_path=db_path) as conn:
        catalog.add_file(conn, _meta(f))
        catalog.add_file(conn, _meta(f))
        assert len(catalog.list_files(conn)) == 1


def test_rescan_updates_metadata_and_preserves_row_id(tmp_path):
    db_path = tmp_path / "catalog.db"
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    with catalog.connect(db_path=db_path) as conn:
        first = catalog.add_file(conn, _meta(f))
        assert first.inserted is True

        f.write_bytes(b"abcdef")
        os.utime(f, (time.time() + 10, time.time() + 10))

        second = catalog.add_file(conn, _meta(f))
        assert second.inserted is False
        assert second.file_id == first.file_id

        items = catalog.list_files(conn)
        assert len(items) == 1
        assert items[0]["size_bytes"] == 6


def test_reopening_database_preserves_data(tmp_path):
    db_path = tmp_path / "catalog.db"
    f = tmp_path / "img.png"
    f.write_bytes(b"1234")
    with catalog.connect(db_path=db_path) as conn:
        catalog.add_file(conn, _meta(f))

    conn2 = catalog.init_db(db_path=db_path)
    try:
        items = catalog.list_files(conn2)
        assert len(items) == 1
        assert items[0]["abs_path"] == str(f.resolve())
    finally:
        catalog.close_db(conn2)


def test_connect_closes_connection_on_error(tmp_path):
    db_path = tmp_path / "catalog.db"
    captured = {}

    with pytest.raises(RuntimeError):
        with catalog.connect(db_path=db_path) as conn:
            captured["conn"] = conn
            conn.execute("SELECT 1")
            raise RuntimeError("simulated scan error")

    with pytest.raises(sqlite3.ProgrammingError):
        captured["conn"].execute("SELECT 1")


def test_unrelated_constraint_error_is_not_silently_ignored(tmp_path):
    db_path = tmp_path / "catalog.db"
    bad_meta = {
        "abs_path": str(tmp_path / "x.jpg"),
        "folder": str(tmp_path),
        "filename": None,  # violates NOT NULL
        "ext": ".jpg",
        "size_bytes": 1,
        "mtime": None,
        "ctime": None,
        "birthtime": None,
    }
    with catalog.connect(db_path=db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            catalog.add_file(conn, bad_meta)
        assert catalog.list_files(conn) == []


def test_ingest_files_reports_inserted_and_updated(tmp_path):
    db_path = tmp_path / "catalog.db"
    good = tmp_path / "good.jpg"
    good.write_bytes(b"x")
    with catalog.connect(db_path=db_path) as conn:
        first = catalog.ingest_files(conn, [good], _meta)
        assert (first.inserted, first.updated, first.failed) == (1, 0, 0)
        second = catalog.ingest_files(conn, [good], _meta)
        assert (second.inserted, second.updated, second.failed) == (0, 1, 0)


def test_ingest_files_does_not_catalog_missing_files(tmp_path):
    db_path = tmp_path / "catalog.db"
    good = tmp_path / "good.jpg"
    good.write_bytes(b"x")
    missing = tmp_path / "missing.jpg"  # deliberately absent
    with catalog.connect(db_path=db_path) as conn:
        stats = catalog.ingest_files(conn, [good, missing], _meta)
        assert stats.inserted == 1
        assert stats.failed == 1
        assert stats.updated == 0
        assert len(catalog.list_files(conn)) == 1


def test_catalog_does_not_touch_source_files(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    img = src / "photo.jpg"
    img.write_bytes(b"hello")
    st_before = img.stat()

    db_path = tmp_path / "appdata" / "catalog.db"
    with catalog.connect(db_path=db_path) as conn:
        catalog.add_file(conn, _meta(img))

    st_after = img.stat()
    assert st_after.st_size == st_before.st_size
    assert st_after.st_mtime == st_before.st_mtime
    assert db_path.parent != src
    assert db_path.parent.name == "appdata"
