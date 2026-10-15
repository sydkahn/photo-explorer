from pathlib import Path

import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from photo_explorer import metadata  # noqa: E402


TAG_MAKE = 0x010F
TAG_MODEL = 0x0110
TAG_DATETIME = 0x0132
TAG_DATETIME_ORIGINAL = 0x9003
TAG_DATETIME_DIGITIZED = 0x9004
TAG_EXIF_IFD = 0x8769


def _make_jpeg(
    path: Path,
    *,
    make: str | None = None,
    model: str | None = None,
    datetime: str | None = None,
    datetime_original: str | None = None,
    datetime_digitized: str | None = None,
) -> Path:
    image = Image.new("RGB", (4, 4), "white")
    if any((make, model, datetime, datetime_original, datetime_digitized)):
        exif = Image.Exif()
        if make:
            exif[TAG_MAKE] = make
        if model:
            exif[TAG_MODEL] = model
        if datetime:
            exif[TAG_DATETIME] = datetime
        sub = exif.get_ifd(TAG_EXIF_IFD)
        if datetime_original:
            sub[TAG_DATETIME_ORIGINAL] = datetime_original
        if datetime_digitized:
            sub[TAG_DATETIME_DIGITIZED] = datetime_digitized
        image.save(path, exif=exif)
    else:
        image.save(path)
    return path


def test_datetime_original_extracted_and_normalized(tmp_path):
    p = _make_jpeg(tmp_path / "a.jpg", datetime_original="2021:07:04 12:34:56")
    meta = metadata.extract_exif(p)
    assert meta["capture_datetime"] == "2021-07-04T12:34:56"
    assert meta["capture_datetime_source"] == "exif:DateTimeOriginal"
    assert meta["exif_datetime_original"] == "2021:07:04 12:34:56"


def test_datetime_digitized_fallback(tmp_path):
    p = _make_jpeg(tmp_path / "b.jpg", datetime_digitized="2019:02:03 04:05:06")
    meta = metadata.extract_exif(p)
    assert meta["capture_datetime"] == "2019-02-03T04:05:06"
    assert meta["capture_datetime_source"] == "exif:DateTimeDigitized"


def test_datetime_fallback(tmp_path):
    p = _make_jpeg(tmp_path / "c.jpg", datetime="2018:11:12 13:14:15")
    meta = metadata.extract_exif(p)
    assert meta["capture_datetime"] == "2018-11-12T13:14:15"
    assert meta["capture_datetime_source"] == "exif:DateTime"
    assert meta["exif_datetime"] == "2018:11:12 13:14:15"


def test_priority_original_over_digitized_over_datetime(tmp_path):
    p = _make_jpeg(
        tmp_path / "d.jpg",
        datetime="2018:11:12 13:14:15",
        datetime_digitized="2019:02:03 04:05:06",
        datetime_original="2021:07:04 12:34:56",
    )
    meta = metadata.extract_exif(p)
    assert meta["capture_datetime"] == "2021-07-04T12:34:56"
    assert meta["capture_datetime_source"] == "exif:DateTimeOriginal"


def test_camera_make_and_model(tmp_path):
    p = _make_jpeg(tmp_path / "e.jpg", make="Canon", model="EOS 5D")
    meta = metadata.extract_exif(p)
    assert meta["camera_make"] == "Canon"
    assert meta["camera_model"] == "EOS 5D"


def test_invalid_datetime_not_normalized_but_raw_preserved(tmp_path):
    p = _make_jpeg(tmp_path / "f.jpg", datetime_original="0000:00:00 00:00:00")
    meta = metadata.extract_exif(p)
    assert meta["capture_datetime"] is None
    assert meta["capture_datetime_source"] is None
    assert meta["exif_datetime_original"] == "0000:00:00 00:00:00"


def test_missing_exif_returns_all_none(tmp_path):
    p = tmp_path / "plain.png"
    Image.new("RGB", (4, 4), "black").save(p)
    meta = metadata.extract_exif(p)
    assert all(value is None for value in meta.values())


def test_corrupt_file_returns_all_none(tmp_path):
    p = tmp_path / "corrupt.jpg"
    p.write_bytes(b"this is not a valid image")
    meta = metadata.extract_exif(p)
    assert all(value is None for value in meta.values())


def test_missing_file_returns_all_none(tmp_path):
    meta = metadata.extract_exif(tmp_path / "nope.jpg")
    assert all(value is None for value in meta.values())


def test_source_file_unchanged_after_extraction(tmp_path):
    p = _make_jpeg(tmp_path / "g.jpg", make="Nikon", datetime_original="2020:03:04 05:06:07")
    before = p.stat()
    metadata.extract_exif(p)
    after = p.stat()
    assert after.st_size == before.st_size
    assert after.st_mtime == before.st_mtime


def test_normalize_exif_datetime_unit():
    assert metadata.normalize_exif_datetime("2021:07:04 12:34:56") == "2021-07-04T12:34:56"
    assert metadata.normalize_exif_datetime("") is None
    assert metadata.normalize_exif_datetime(None) is None
    assert metadata.normalize_exif_datetime("not a date") is None
