from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterator, List, NamedTuple, Optional, Union

from . import paths


# Bump this when the schema changes. Migrations are applied stepwise below;
# there is intentionally no general migration framework yet.
CURRENT_SCHEMA_VERSION = 2

# EXIF-derived columns added in schema version 2.
_EXIF_COLUMNS = (
    ("capture_datetime", "TEXT"),
    ("capture_datetime_source", "TEXT"),
    ("exif_datetime_original", "TEXT"),
    ("exif_datetime_digitized", "TEXT"),
    ("exif_datetime", "TEXT"),
    ("camera_make", "TEXT"),
    ("camera_model", "TEXT"),
)


class SchemaVersionError(RuntimeError):
    """Raised when a database has a schema version this build cannot use."""


class UpsertResult(NamedTuple):
    file_id: int
    inserted: bool


@dataclass
class IngestStats:
    inserted: int = 0
    updated: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    records: List[Dict] = field(default_factory=list)


def _get_db_path(app_root: Optional[Path] = None) -> Path:
    root = app_root or paths.get_app_root()
    paths.ensure_directories(root)  # ensure data dir exists
    return paths.get_data_dir(root) / "catalog.db"


def _read_user_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          abs_path TEXT NOT NULL UNIQUE,
          folder TEXT NOT NULL,
          filename TEXT NOT NULL,
          ext TEXT NOT NULL,
          size_bytes INTEGER NOT NULL,
          mtime REAL,
          ctime REAL,
          birthtime REAL,
          discovered_at REAL NOT NULL,
          scan_id INTEGER,
          capture_datetime TEXT,
          capture_datetime_source TEXT,
          exif_datetime_original TEXT,
          exif_datetime_digitized TEXT,
          exif_datetime TEXT,
          camera_make TEXT,
          camera_model TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_ext ON files(ext)")


def _existing_columns(conn: sqlite3.Connection) -> set:
    return {row["name"] for row in conn.execute("PRAGMA table_info(files)")}


def _ensure_exif_columns(conn: sqlite3.Connection) -> None:
    """Add any missing EXIF columns (schema v1 -> v2).

    Additive and idempotent; existing rows keep their IDs and get NULL for the
    new columns. Only called when the stored version is older than current.
    """
    existing = _existing_columns(conn)
    for name, decl in _EXIF_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE files ADD COLUMN {name} {decl}")


def init_db(
    db_path: Optional[Union[str, Path]] = None, app_root: Optional[Path] = None
) -> sqlite3.Connection:
    """Open (creating if needed) the catalog database.

    Initializes a new database at CURRENT_SCHEMA_VERSION, upgrades older
    schema versions stepwise (preserving rows and IDs), keeps current-version
    databases unchanged, and raises SchemaVersionError for unsupported
    versions. The connection is closed if initialization fails.
    """
    if db_path is None:
        db_path = _get_db_path(app_root)

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        version = _read_user_version(conn)
        supported = (0, 1, CURRENT_SCHEMA_VERSION)
        if version not in supported:
            raise SchemaVersionError(
                f"Unsupported database schema version {version}; this build "
                f"supports versions up to {CURRENT_SCHEMA_VERSION}."
            )

        # Create-if-absent, then bring older databases up to the current
        # version. The version marker is written only after migrations succeed,
        # so a failed migration does not mark the database as upgraded.
        _create_schema(conn)
        if version < CURRENT_SCHEMA_VERSION:
            if version < 2:
                _ensure_exif_columns(conn)
            conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
        conn.commit()
    except Exception:
        conn.close()
        raise
    return conn


@contextmanager
def connect(
    db_path: Optional[Union[str, Path]] = None, app_root: Optional[Path] = None
) -> Iterator[sqlite3.Connection]:
    """Context manager that always closes the connection.

    Note: a sqlite3 connection used directly as a context manager manages
    transactions only; it does not close the connection. This wrapper closes
    it on both success and failure.
    """
    conn = init_db(db_path=db_path, app_root=app_root)
    try:
        yield conn
    finally:
        close_db(conn)


def add_file(conn: sqlite3.Connection, meta: Dict) -> UpsertResult:
    """Insert or update a catalog row for a source file.

    Uses INSERT ... ON CONFLICT(abs_path) DO UPDATE so rescanning updates
    filesystem and EXIF metadata while preserving the existing row id. Other
    constraint errors are allowed to propagate rather than being ignored.
    """
    abs_path = meta.get("abs_path")
    row = conn.execute("SELECT id FROM files WHERE abs_path = ?", (abs_path,)).fetchone()
    existing_id = int(row["id"]) if row else None

    cur = conn.execute(
        """
        INSERT INTO files (
            abs_path, folder, filename, ext, size_bytes, mtime, ctime, birthtime, discovered_at,
            capture_datetime, capture_datetime_source, exif_datetime_original,
            exif_datetime_digitized, exif_datetime, camera_make, camera_model
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(abs_path) DO UPDATE SET
            folder = excluded.folder,
            filename = excluded.filename,
            ext = excluded.ext,
            size_bytes = excluded.size_bytes,
            mtime = excluded.mtime,
            ctime = excluded.ctime,
            birthtime = excluded.birthtime,
            discovered_at = excluded.discovered_at,
            capture_datetime = excluded.capture_datetime,
            capture_datetime_source = excluded.capture_datetime_source,
            exif_datetime_original = excluded.exif_datetime_original,
            exif_datetime_digitized = excluded.exif_datetime_digitized,
            exif_datetime = excluded.exif_datetime,
            camera_make = excluded.camera_make,
            camera_model = excluded.camera_model
        """,
        (
            abs_path,
            meta.get("folder"),
            meta.get("filename"),
            meta.get("ext"),
            int(meta.get("size_bytes", 0) or 0),
            meta.get("mtime"),
            meta.get("ctime"),
            meta.get("birthtime"),
            time.time(),
            meta.get("capture_datetime"),
            meta.get("capture_datetime_source"),
            meta.get("exif_datetime_original"),
            meta.get("exif_datetime_digitized"),
            meta.get("exif_datetime"),
            meta.get("camera_make"),
            meta.get("camera_model"),
        ),
    )
    conn.commit()

    if existing_id is not None:
        return UpsertResult(file_id=existing_id, inserted=False)
    return UpsertResult(file_id=int(cur.lastrowid), inserted=True)


def ingest_files(
    conn: sqlite3.Connection,
    files: List[Path],
    metadata_provider: Callable[[Path], Dict],
) -> IngestStats:
    """Add/update each file, counting new, updated, and failed records.

    Filesystem errors (missing/inaccessible files) are collected per file and
    do not abort the scan. Database errors are intentionally not caught here:
    they propagate so a genuine database failure is reported, not hidden.
    """
    stats = IngestStats()
    for f in files:
        try:
            meta = metadata_provider(f)
        except OSError as e:
            stats.failed += 1
            stats.errors.append(f"{f}: {e}")
            continue
        result = add_file(conn, meta)
        if result.inserted:
            stats.inserted += 1
        else:
            stats.updated += 1
        stats.records.append(meta)
    return stats


def list_files(
    conn: sqlite3.Connection, limit: Optional[int] = None, offset: Optional[int] = None
) -> List[Dict]:
    """List files from catalog."""
    q = "SELECT * FROM files ORDER BY abs_path"
    params: List = []
    if limit is not None:
        q += " LIMIT ?"
        params.append(int(limit))
    if offset is not None:
        q += " OFFSET ?"
        params.append(int(offset))
    rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def close_db(conn: sqlite3.Connection) -> None:
    """Close the connection. Closing an already-closed connection is a no-op."""
    conn.close()
