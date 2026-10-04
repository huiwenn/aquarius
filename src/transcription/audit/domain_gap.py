"""
In-domain check A: how different is the collected dataset from the transcription benchmark?

Same F0 evidence (RMVPE + PESTO on separated vocals) for both:
  benchmark  data/transcription/critic/bench_{rmvpe,pesto}  (160 clips: separated vocals of the synthetic mixes)
  dataset    data/transcription/critic/f0_{rmvpe,pesto}/<region>  (600 recordings)
Per item:
  tuning_abs      |global tuning offset from A440| (st)
  wobble_st       std of (pitch − 150 ms running median) on confident frames: vibrato/ornament depth
  glide_frac      fraction of confident frames moving faster than 8 st/s (50 ms smoothed): 滑音/portamento share
  jump_frac       fraction of confident frames ≥ 6 st off their 150 ms neighbourhood (octave slips, bleed)
  tracker_agree   confident frames / frames voiced by either tracker: how unambiguous the vocal pitch is
                  (low = noise, bleed, polyphony, breathy/falsetto; it also bounds the critic's own reliability)
  voiced_frac     RMVPE-voiced fraction of the item
  range_st        p95 − p5 pitch (st)
Reports medians per group and a KS statistic dataset-vs-benchmark per property.

Run (py312): python src/transcription/audit/domain_gap.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "critic"))
from critic import Evidence, tuning_offset  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
C = ROOT / "data" / "transcription" / "critic"
OUT = ROOT / "data" / "transcription" / "audit"
PROPS = ["tuning_abs", "wobble_st", "jump_frac", "glide_frac", "tracker_agree", "voiced_frac", "range_st"]


def props(ev: Evidence) -> dict:
    c = ev.confident
    rv, pv = ev.rmvpe > 0, ev.conf > 0.5
    s = ev.semis
    out = {"tuning_abs": abs(tuning_offset(ev)), "voiced_frac": rv.mean(),
           "tracker_agree": c.sum() / max(1, (rv | pv).sum())}
    if c.sum() > 50:
        sm = s.copy()
        sm[~c] = np.nan
        filled = pd.Series(sm).interpolate(limit=5, limit_area="inside").to_numpy()
        med = pd.Series(sm).rolling(15, center=True, min_periods=5).median().to_numpy()  # NaN-aware
        dev = (s - med)[c]
        out["wobble_st"] = float(np.nanstd(dev[np.abs(dev) < 6]))     # exclude octave/bleed jumps
        out["jump_frac"] = float(np.nanmean(np.abs(dev) >= 6))        # frames ≥ 6 st off their neighbourhood
        sm5 = pd.Series(filled).rolling(5, center=True, min_periods=3).mean().to_numpy()  # 50 ms smoothing
        vel = np.abs(np.diff(sm5)) / 0.01
        both = c[1:] & c[:-1]
        out["glide_frac"] = float(np.nanmean(vel[both] > 8)) if both.any() else np.nan
        out["range_st"] = float(np.percentile(s[c], 95) - np.percentile(s[c], 5))
    return out


def main() -> None:
    rows = []
    for f in sorted((C / "bench_rmvpe").glob("*.npz")):
        p = C / "bench_pesto" / f.name
        if p.exists():
            rows.append({"group": "benchmark:" + f.stem.split("_")[0], "item": f.stem,
                         **props(Evidence.load(f, p))})
    for f in sorted((C / "f0_rmvpe").glob("*/*.npz")):
        p = C / "f0_pesto" / f.parent.name / f.name
        if p.exists():
            rows.append({"group": f.parent.name, "item": f.stem, **props(Evidence.load(f, p))})
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "domain_gap.csv", index=False)
    print(d.groupby("group")[PROPS].median().round(3).to_string())
    bench = d[d.group.str.startswith("benchmark")]
    data = d[~d.group.str.startswith("benchmark")]
    print(f"\nall benchmark (n={len(bench)}) vs all dataset (n={len(data)}):")
    for k in PROPS:
        a, b = bench[k].dropna(), data[k].dropna()
        if len(a) and len(b):
            print(f"  {k:14s} bench {a.median():.3f}  dataset {b.median():.3f}  KS {ks_2samp(a, b).statistic:.2f}")


if __name__ == "__main__":
    main()
