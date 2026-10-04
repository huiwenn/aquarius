"""
How trustworthy is the critic's evidence? Frame-level accuracy of the two pitch trackers
(RMVPE, PESTO) against benchmark ground-truth notes, on separated vocals of the benchmark mixtures.

  *_acc        fraction of voiced frames inside GT notes within ±0.5 st of the GT note pitch
  conf_acc     same, restricted to "confident" frames (both trackers voiced and within 0.5 st of each other)
  conf_frac    fraction of GT-note frames that are confident (coverage of the critic's evidence)
  agree        confident frames / frames voiced by either tracker
  rmvpe_fa     RMVPE voiced frames outside any GT note / frames outside GT notes

Run (py312): python src/transcription/critic/validate_f0.py [--pesto-conf 0.5]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / "data" / "transcription" / "benchmark"
C = ROOT / "data" / "transcription" / "critic"


def st(hz):
    return 12 * np.log2(np.maximum(hz, 1e-3) / 440) + 69


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pesto-conf", type=float, default=0.5)
    args = ap.parse_args()
    rows = []
    for r in pd.read_csv(B / "index.csv").itertuples():
        R, P = np.load(C / "bench_rmvpe" / f"{r.clip_id}.npz"), np.load(C / "bench_pesto" / f"{r.clip_id}.npz")
        n = min(len(R["f0"]), len(P["f0"]))
        fr, fp, cp = R["f0"][:n], P["f0"][:n], P["conf"][:n]
        t = np.arange(n) * 0.01
        ref = np.full(n, np.nan)
        for g in pd.read_csv(B / "gt" / f"{r.clip_id}.csv").itertuples():
            ref[(t >= g.onset) & (t < g.offset)] = g.pitch
        inn, rv, pv = ~np.isnan(ref), fr > 0, cp > args.pesto_conf
        both = rv & pv & (np.abs(st(fr) - st(fp)) < 0.5)

        def acc(mask, f):
            m = inn & mask
            return np.mean(np.abs(st(f[m]) - ref[m]) < 0.5) if m.any() else np.nan

        rows.append(dict(src=r.source, rmvpe_acc=acc(rv, fr), pesto_acc=acc(pv, fp), conf_acc=acc(both, fr),
                         conf_frac=(inn & both).sum() / max(1, inn.sum()),
                         agree=both.sum() / max(1, (rv | pv).sum()),
                         rmvpe_fa=(rv & ~inn).sum() / max(1, (~inn).sum())))
    print(pd.DataFrame(rows).groupby("src").mean().round(3).to_string())


if __name__ == "__main__":
    main()
