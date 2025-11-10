"""Unified preprocessing cache service (native, no legacy dependency)."""

from __future__ import annotations

import os
import json
import hashlib
import tempfile
from typing import Any, Dict

import numpy as np


def _cache_dir() -> str:
    d = os.path.join(tempfile.gettempdir(), "masw_preproc_cache")
    os.makedirs(d, exist_ok=True)
    return d


def make_key(path: str, mtime: float, reverse: bool, start: float, end: float,
             downsample: bool, dfac: int, numf: int) -> str:
    payload = {
        "v": "v1",
        "p": os.path.abspath(path),
        "m": round(float(mtime), 3),
        "r": bool(reverse),
        "s": float(start),
        "e": float(end),
        "d": bool(downsample),
        "df": int(dfac),
        "nf": int(numf),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _path_for_key(key: str) -> str:
    return os.path.join(_cache_dir(), f"{key}.npz")


def load_preprocessed(key: str) -> Dict[str, Any] | None:
    fp = _path_for_key(key)
    if not os.path.isfile(fp):
        return None
    try:
        data = np.load(fp)
        return {"Tpre": data["Tpre"], "dt2": float(data["dt2"]) }
    except Exception:
        try:
            os.remove(fp)
        except Exception:
            pass
        return None


def save_preprocessed(key: str, Tpre, dt2: float) -> None:
    fp = _path_for_key(key)
    try:
        np.savez_compressed(fp, Tpre=np.asarray(Tpre, dtype=np.float32), dt2=np.array(dt2))
    except Exception:
        pass


def clear_cache() -> None:
    d = _cache_dir()
    try:
        for name in os.listdir(d):
            try:
                os.remove(os.path.join(d, name))
            except Exception:
                pass
    except Exception:
        pass


