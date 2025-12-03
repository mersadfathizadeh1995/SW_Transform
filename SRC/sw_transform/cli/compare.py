from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from sw_transform.core.service import run_compare


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run 4-method comparison for one file")
    p.add_argument("path", help="SEG-2 .dat file path")
    p.add_argument("--outdir", required=True, help="output directory")
    p.add_argument("--offset", default="+0", help="offset label for plots")
    p.add_argument("--source-type", default="hammer", choices=["hammer","vibrosis"],
                   help="source type: 'hammer' (default) or 'vibrosis' (applies frequency compensation for FDBF)")
    p.add_argument("--no-export-spectra", dest="export_spectra", action="store_false", default=True,
                   help="disable power spectrum export to .npz files (enabled by default)")
    p.add_argument("--params", default="{}", help="JSON dict of additional parameters")
    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    a = p.parse_args(argv)
    extra: Dict[str, Any] = json.loads(a.params)
    params: Dict[str, Any] = dict(
        path=a.path,
        base=a.path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1].split(".")[0],
        outdir=a.outdir,
        offset=a.offset,
        pick_vmin=0.0, pick_vmax=5000.0,
        pick_fmin=0.0, pick_fmax=100.0,
        st=0.0, en=1.0,
        downsample=True, dfac=16, numf=4000,
        n_fk=4000, tol_fk=0.0, n_ps=1200, vspace_ps="log",
        rev_fk=False, rev_ps=False, rev_fdbf=False, rev_ss=False,
        topic="",
        source_type=a.source_type,
        export_spectra=a.export_spectra,
    )
    params.update(extra)
    base, ok, out = run_compare(params)
    print(json.dumps({"base": base, "ok": ok, "out": out}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

