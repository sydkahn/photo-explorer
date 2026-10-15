import pytest

from photo_explorer import scanner


def test_discover_images_finds_supported_recursive(tmp_path):
    d1 = tmp_path / "a" / "b"
    d1.mkdir(parents=True)
    (tmp_path / "root.jpg").write_bytes(b"")
    (tmp_path / "a" / "img.png").write_bytes(b"")
    (d1 / "deep.JPEG").write_bytes(b"")
    (tmp_path / "note.txt").write_bytes(b"text")
    (tmp_path / "skip.docx").write_bytes(b"doc")

    images = scanner.discover_images(tmp_path, recursive=True)
    assert len(images) == 3
    names = {p.name.lower() for p in images}
    assert names == {"root.jpg", "img.png", "deep.jpeg"}


def test_discover_images_case_insensitive(tmp_path):
    (tmp_path / "A.JPG").write_bytes(b"")
    (tmp_path / "B.PNG").write_bytes(b"")
    (tmp_path / "C.TIFF").write_bytes(b"")
    images = scanner.discover_images(tmp_path)
    assert len(images) == 3


def test_discover_images_ignores_unsupported(tmp_path):
    (tmp_path / "good.jpg").write_bytes(b"")
    (tmp_path / "bad.heic").write_bytes(b"")
    (tmp_path / "bad.raw").write_bytes(b"")
    images = scanner.discover_images(tmp_path)
    assert len(images) == 1
    assert images[0].name.lower() == "good.jpg"


def test_get_file_metadata_returns_expected_fields(tmp_path):
    f = tmp_path / "test.jpg"
    data = b"x" * 123
    f.write_bytes(data)
    meta = scanner.get_file_metadata(f)
    assert meta["abs_path"] == str(f.resolve())
    assert meta["filename"] == "test.jpg"
    assert meta["ext"] == ".jpg"
    assert meta["folder"] == str(tmp_path.resolve())
    assert meta["size_bytes"] == 123
    assert meta["mtime"] is not None


def test_discover_handles_nested_dirs_gracefully(tmp_path):
    (tmp_path / "x.jpg").write_bytes(b"")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "y.png").write_bytes(b"")
    images = scanner.discover_images(tmp_path, recursive=True)
    assert len(images) == 2


def test_scan_folder_happy_path_has_no_errors(tmp_path):
    (tmp_path / "x.jpg").write_bytes(b"")
    outcome = scanner.scan_folder(tmp_path)
    assert len(outcome.files) == 1
    assert outcome.errors == []


def test_scan_folder_missing_directory_reports_error(tmp_path):
    outcome = scanner.scan_folder(tmp_path / "does-not-exist")
    assert outcome.files == []
    assert outcome.errors


def test_scan_folder_on_file_reports_error(tmp_path):
    f = tmp_path / "not_a_dir.jpg"
    f.write_bytes(b"")
    outcome = scanner.scan_folder(f)
    assert outcome.files == []
    assert outcome.errors


def test_get_file_metadata_missing_file_raises(tmp_path):
    with pytest.raises(OSError):
        scanner.get_file_metadata(tmp_path / "missing.jpg")


def test_scan_folder_skips_disappearing_file(tmp_path, monkeypatch):
    f = tmp_path / "vanish.jpg"
    f.write_bytes(b"")
    original_resolve = scanner.Path.resolve

    def failing_resolve(self, *args, **kwargs):
        if self.name == "vanish.jpg":
            raise OSError("simulated disappearing file")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(scanner.Path, "resolve", failing_resolve)

    outcome = scanner.scan_folder(tmp_path)
    assert outcome.files == []
    assert any("vanish.jpg" in err for err in outcome.errors)
