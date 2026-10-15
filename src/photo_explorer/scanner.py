from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union


# Supported image extensions (case-insensitive). Start minimal and conservative.
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}


@dataclass
class ScanOutcome:
    """Result of a folder scan: discovered files plus non-fatal errors."""

    files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _is_supported_ext(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTS


def scan_folder(root: Union[str, Path], recursive: bool = True) -> ScanOutcome:
    """Discover supported image files, collecting filesystem errors.

    Read-only: only listings and stat() are used. Inaccessible or
    disappearing paths are recorded in ``errors`` and skipped rather than
    aborting the whole scan.
    """
    outcome = ScanOutcome()

    try:
        root_path = Path(root).resolve()
    except OSError as e:
        outcome.errors.append(f"{root}: {e}")
        return outcome

    try:
        if not root_path.exists() or not root_path.is_dir():
            outcome.errors.append(f"Not a readable folder: {root_path}")
            return outcome
    except OSError as e:
        outcome.errors.append(f"{root_path}: {e}")
        return outcome

    try:
        entries = root_path.rglob("*") if recursive else root_path.iterdir()
        for p in entries:
            try:
                if p.is_file() and not p.is_symlink() and _is_supported_ext(p):
                    outcome.files.append(p.resolve())
            except OSError as e:
                outcome.errors.append(f"{p}: {e}")
    except OSError as e:
        # Error while iterating a directory (e.g. permission denied).
        outcome.errors.append(f"{root_path}: {e}")

    outcome.files.sort(key=lambda x: str(x))
    return outcome


def discover_images(root: Union[str, Path], recursive: bool = True) -> List[Path]:
    """Return supported image files under root. Read-only; does not modify files."""
    return scan_folder(root, recursive=recursive).files


def get_file_metadata(path: Union[str, Path]) -> Dict[str, object]:
    """Return filesystem metadata for a file.

    Never opens or modifies file content; uses stat() only. Raises OSError
    (including FileNotFoundError) if the file cannot be accessed.
    """
    p = Path(path).resolve()
    st = p.stat()

    mtime = float(st.st_mtime) if st.st_mtime else None
    ctime = float(st.st_ctime) if st.st_ctime else None

    birthtime = None
    birthtime_raw = getattr(st, "st_birthtime", None)
    if birthtime_raw:
        birthtime = float(birthtime_raw)

    return {
        "abs_path": str(p),
        "folder": str(p.parent),
        "filename": p.name,
        "ext": p.suffix.lower(),
        "size_bytes": int(st.st_size),
        "mtime": mtime,
        "ctime": ctime,
        "birthtime": birthtime,
    }
