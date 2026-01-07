"""Native preprocessing implementation and cache helpers."""

from __future__ import annotations

import os
import sys
from typing import Tuple


import numpy as np


def preprocess_data(Timematrix, time, deltat,
                    reverse_shot=False,
                    start_time=0.0,
                    end_time=1.0,
                    do_downsample=False,
                    down_factor=16,
                    numf=4000,
                    numchannels=None,
                    shot_index=1,
                    num_reverse_shots=4) -> Tuple:
    # Use all channels if not specified
    if numchannels is None:
        numchannels = Timematrix.shape[1]
    
    if reverse_shot and (shot_index <= num_reverse_shots):
        Timematrix = np.fliplr(Timematrix[:, :numchannels])
    else:
        Timematrix = Timematrix[:, :numchannels]

    start_idx = np.argmin(np.abs(time - start_time))
    end_idx = np.argmin(np.abs(time - end_time))
    Timematrix_win = Timematrix[start_idx:end_idx + 1, :]
    time_win = time[start_idx:end_idx + 1]

    if do_downsample and down_factor > 1:
        Timematrix_ds = Timematrix_win[::down_factor, :]
        time_ds = time_win[::down_factor]
        deltat_ds = deltat * down_factor
    else:
        Timematrix_ds = Timematrix_win
        time_ds = time_win
        deltat_ds = deltat

    desired_len = 2 * numf
    L_current = Timematrix_ds.shape[0]
    if L_current > desired_len:
        Timematrix_ds = Timematrix_ds[:desired_len, :]
        time_ds = time_ds[:desired_len]
    elif L_current < desired_len:
        Numzeros = desired_len - L_current
        pad = np.zeros((Numzeros, Timematrix_ds.shape[1]), dtype=Timematrix_ds.dtype)
        Timematrix_ds = np.vstack([Timematrix_ds, pad])
        extra_time = np.arange(time_ds[-1] + deltat_ds, time_ds[-1] + deltat_ds * (Numzeros + 1), deltat_ds)
        time_ds = np.concatenate([time_ds, extra_time])

    return Timematrix_ds, time_ds, deltat_ds


def cache_make_key(path: str, mtime: float, reverse: bool, start: float, end: float, downsample: bool, dfac: int, numf: int) -> str:
    from sw_transform.core.cache import make_key as _mk
    return _mk(path, mtime, reverse, start, end, downsample, dfac, numf)


def cache_load(key: str):
    from sw_transform.core.cache import load_preprocessed as _ld
    return _ld(key)


def cache_save(key: str, Tpre, dt2: float) -> None:
    from sw_transform.core.cache import save_preprocessed as _sv
    _sv(key, Tpre, dt2)


