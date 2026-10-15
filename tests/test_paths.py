import pytest
from pathlib import Path

from photo_explorer import paths


def test_get_app_root_dev():
    root = paths.get_app_root()
    assert root is not None
    assert isinstance(root, Path)
    # Development runtime should be in project root .runtime
    assert root.name == ".runtime"
    assert root.parent == Path(__file__).resolve().parent.parent


def test_path_selection_with_temp_dir(tmp_path):
    root = tmp_path / "appdata"
    assert root != paths.get_app_root()

    config = paths.get_config_dir(app_root=root)
    logs = paths.get_logs_dir(app_root=root)
    thumbs = paths.get_thumbnails_dir(app_root=root)
    cache = paths.get_cache_dir(app_root=root)
    data = paths.get_data_dir(app_root=root)

    assert config == root / "config"
    assert logs == root / "logs"
    assert thumbs == root / "thumbnails"
    assert cache == root / "cache"
    assert data == root / "data"


def test_ensure_directories_creates_only_specified_root(tmp_path):
    root = tmp_path / "appdata"
    result = paths.ensure_directories(app_root=root)
    assert result == root
    assert (root / "config").is_dir()
    assert (root / "logs").is_dir()
    assert (root / "thumbnails").is_dir()
    assert (root / "cache").is_dir()
    assert (root / "data").is_dir()
    # Verify nothing under root is outside root (sanity)
    for p in root.rglob("*"):
        assert p.is_relative_to(root)


def test_ensure_directories_no_real_runtime_created(tmp_path, monkeypatch):
    root = tmp_path / "testapp"
    real_runtime = Path(__file__).resolve().parent.parent / ".runtime"
    before = real_runtime.exists()
    paths.ensure_directories(app_root=root)
    after = real_runtime.exists()
    assert before == after  # unchanged
    # Only tmp root touched
    assert root.exists()
    assert (root / "data").is_dir()
    assert all(p.is_relative_to(root) for p in root.rglob("*"))
