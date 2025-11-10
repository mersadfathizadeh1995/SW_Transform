r"""Native file assignment (offset/reverse) with optional legacy passthrough.

This implements the repeating decade pattern locally so the package can run
without the legacy `Previous\File_Assignment.py`. If the legacy module is
present, we can still import it transparently.
"""

from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def _legacy_path() -> str:
    here = os.path.dirname(__file__)
    # Go up to SW_Transform parent (…/4_Wave) then into Previous
    return os.path.abspath(os.path.join(here, "..", "..", "..", "..", "Previous"))


def _native_find_dat_files(inputs: Iterable[str], recursive: bool) -> List[str]:
    files: List[str] = []
    for raw in inputs:
        p = Path(raw).resolve()
        if p.is_file() and p.suffix.lower() == ".dat":
            files.append(str(p))
        elif p.is_dir():
            if recursive:
                files.extend([str(f.resolve()) for f in p.rglob("*.dat")])
                files.extend([str(f.resolve()) for f in p.rglob("*.DAT")])
            else:
                files.extend([str(f.resolve()) for f in p.glob("*.dat")])
                files.extend([str(f.resolve()) for f in p.glob("*.DAT")])
    # Deduplicate
    seen = set(); uniq: List[str] = []
    for f in files:
        if f not in seen:
            seen.add(f); uniq.append(f)
    return uniq


BASE_OFFSETS = {1: 66.0, 2: 56.0, 3: 51.0, 4: 48.0, 6: -2.0, 7: -5.0, 8: -10.0, 9: -20.0, 10: -30.0}


def _extract_shot_index_from_name(path: Path) -> Optional[int]:
    stem = path.stem
    m = re.search(r"(\d+)$", stem)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    m_any = re.search(r"(\d+)", stem)
    if m_any:
        try:
            return int(m_any.group(1))
        except ValueError:
            return None
    return None


def _infer_offset_from_index(shot_index: int) -> Tuple[Optional[float], str]:
    pos = shot_index % 10
    if pos == 0:
        pos = 10
    if pos == 5:
        return None, "Position 5/15/25 is unknown"
    if pos in BASE_OFFSETS:
        return BASE_OFFSETS[pos], f"Mapped by pattern (pos {pos})"
    return None, f"No mapping for position {pos}"


class _NativeRow:
    def __init__(self, file_path: Path, shot_index: Optional[int], offset_m: Optional[float], reverse: bool, reason: str):
        self.file_path = file_path
        self.shot_index = shot_index
        self.offset_m = offset_m
        self.reverse = reverse
        self.reason = reason
    def __repr__(self) -> str:
        return f"NativeAssign({self.file_path}, idx={self.shot_index}, off={self.offset_m}, rev={self.reverse})"


def assign_files(paths: Iterable[str], recursive: bool = True, include_unknown: bool = False):
    # Try legacy first
    try:
        base = _legacy_path()
        if base not in sys.path:
            sys.path.insert(0, base)
        import File_Assignment as FA  # type: ignore
        files = FA.find_dat_files(paths, recursive=recursive)
        rows = [FA.assign_file(p) for p in files]
        if not include_unknown:
            rows = [r for r in rows if getattr(r, 'offset_m', None) is not None]
        return rows
    except Exception:
        pass
    # Native fallback
    files = _native_find_dat_files(paths, recursive)
    rows = []
    for f in files:
        p = Path(f)
        idx = _extract_shot_index_from_name(p)
        if idx is None:
            rows.append(_NativeRow(p, None, None, False, "No number found in filename"))
            continue
        off, reason = _infer_offset_from_index(idx)
        rev = bool(off is not None and off > 0.0)
        rows.append(_NativeRow(p, idx, off, rev, reason))
    if not include_unknown:
        rows = [r for r in rows if r.offset_m is not None]
    return rows


def main(argv: Optional[List[str]] = None) -> int:
    base = _legacy_path()
    if base not in sys.path:
        sys.path.insert(0, base)
    import File_Assignment as FA  # type: ignore
    return FA.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())


