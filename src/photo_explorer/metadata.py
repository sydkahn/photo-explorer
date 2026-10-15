from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is a declared dependency
    Image = None


# EXIF tag IDs (EXIF specification).
TAG_MAKE = 0x010F
TAG_MODEL = 0x0110
TAG_DATETIME = 0x0132  # File change date/time (IFD0)
TAG_DATETIME_ORIGINAL = 0x9003  # Exif sub-IFD
TAG_DATETIME_DIGITIZED = 0x9004  # Exif sub-IFD
TAG_EXIF_IFD = 0x8769

# Fields produced by this module (all EXIF-derived).
FIELD_NAMES = (
    "capture_datetime",
    "capture_datetime_source",
    "exif_datetime_original",
    "exif_datetime_digitized",
    "exif_datetime",
    "camera_make",
    "camera_model",
)


def empty_metadata() -> Dict[str, Optional[str]]:
    """Return a metadata dict with every field set to None."""
    return {name: None for name in FIELD_NAMES}


def _clean(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8", "ignore")
        except Exception:  # pragma: no cover - defensive
            return None
    text = str(value).strip().strip("\x00").strip()
    return text or None


def normalize_exif_datetime(raw: Optional[str]) -> Optional[str]:
    """Normalize an EXIF timestamp to ISO-8601, or None if unusable.

    EXIF timestamps look like "YYYY:MM:DD HH:MM:SS". No timezone is assumed
    or added and no local-to-UTC conversion is performed.
    """
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if dt.year < 1:
            return None
        return dt.isoformat(timespec="seconds")
    return None


def _get_tag(exif, tag: int) -> Optional[str]:
    """Look up an EXIF tag at the top level, then in the Exif sub-IFD."""
    value = _clean(exif.get(tag))
    if value is not None:
        return value
    try:
        sub = exif.get_ifd(TAG_EXIF_IFD)
    except Exception:
        return None
    if sub:
        return _clean(sub.get(tag))
    return None


def extract_exif(path: Union[str, Path]) -> Dict[str, Optional[str]]:
    """Read EXIF fields from an image without modifying it.

    Returns a dict with all fields set to None when EXIF is missing, the file
    is unreadable, corrupt, or not a supported image. All processing is local.
    """
    result = empty_metadata()
    if Image is None:  # pragma: no cover - Pillow is a declared dependency
        return result

    try:
        with Image.open(Path(path)) as image:
            exif = image.getexif()
            if not exif:
                return result

            make = _get_tag(exif, TAG_MAKE)
            model = _get_tag(exif, TAG_MODEL)
            raw_original = _get_tag(exif, TAG_DATETIME_ORIGINAL)
            raw_digitized = _get_tag(exif, TAG_DATETIME_DIGITIZED)
            raw_datetime = _get_tag(exif, TAG_DATETIME)
    except Exception:
        # Corrupt, unsupported, or inaccessible image: treat as no metadata.
        return result

    result["camera_make"] = make
    result["camera_model"] = model
    result["exif_datetime_original"] = raw_original
    result["exif_datetime_digitized"] = raw_digitized
    result["exif_datetime"] = raw_datetime

    for raw, source in (
        (raw_original, "exif:DateTimeOriginal"),
        (raw_digitized, "exif:DateTimeDigitized"),
        (raw_datetime, "exif:DateTime"),
    ):
        normalized = normalize_exif_datetime(raw)
        if normalized is not None:
            result["capture_datetime"] = normalized
            result["capture_datetime_source"] = source
            break

    return result
