import os
import sys
from pathlib import Path
from typing import Optional

APP_NAME = "photo_explorer"


def _get_app_root() -> Path:
    """Return application root for development or portable build.

    During development, prefer a .runtime directory inside the project.
    Design allows future portable builds to store data relative to the
    application directory (where the executable lives).
    """
    # For development: project root is parent of src/ (i.e. go up two levels from src/photo_explorer)
    project_root = Path(__file__).resolve().parent.parent.parent
    runtime_dev = project_root / ".runtime"
    return runtime_dev


def get_app_root() -> Path:
    """Return the application data root."""
    return _get_app_root()


def get_config_dir(app_root: Optional[Path] = None) -> Path:
    root = app_root or get_app_root()
    return root / "config"


def get_logs_dir(app_root: Optional[Path] = None) -> Path:
    root = app_root or get_app_root()
    return root / "logs"


def get_thumbnails_dir(app_root: Optional[Path] = None) -> Path:
    root = app_root or get_app_root()
    return root / "thumbnails"


def get_cache_dir(app_root: Optional[Path] = None) -> Path:
    root = app_root or get_app_root()
    return root / "cache"


def get_data_dir(app_root: Optional[Path] = None) -> Path:
    root = app_root or get_app_root()
    return root / "data"


def ensure_directories(app_root: Optional[Path] = None) -> Path:
    """Create required directories. Raises OSError if creation fails."""
    root = app_root or get_app_root()
    dirs = [
        root,
        get_config_dir(root),
        get_logs_dir(root),
        get_thumbnails_dir(root),
        get_cache_dir(root),
        get_data_dir(root),
    ]
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Failed to create directory {d}: {e}") from e
    return root
