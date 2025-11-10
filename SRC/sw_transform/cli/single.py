from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from sw_transform.core.service import run_single


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run single-method processing for one file")
    p.add_argument("path", help="SEG-2 .dat file path")
    p.add_argument("--key", default="fk", choices=["fk","fdbf","ps","ss"], help="method key")
    p.add_argument("--outdir", required=True, help="output directory")
    p.add_argument("--offset", default="+0", help="offset label for plots")
    p.add_argument("--params", default="{}", help="JSON dict of additional parameters")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    a = p.parse_args(argv)
    extra: Dict[str, Any] = json.loads(a.params)
    # reasonable defaults; caller can override via --params
    params: Dict[str, Any] = dict(
        path=a.path,
        base=a.path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1].split(".")[0],
        key=a.key,
        offset=a.offset,
        outdir=a.outdir,
        pick_vmin=0.0, pick_vmax=5000.0,
        pick_fmin=0.0, pick_fmax=100.0,
        st=0.0, en=1.0,
        downsample=True, dfac=16, numf=4000,
        grid_n=4000 if a.key in ("fk","fdbf") else 1200,
        tol=0.0, vspace="log",
        dpi=200, rev=False,
        topic="",
    )
    params.update(extra)
    base, ok, out = run_single(params)
    print(json.dumps({"base": base, "ok": ok, "out": out}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

