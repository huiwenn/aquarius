"""
Scale-degree intonation profiles: where sung pitch leaves the equal-tempered grid, per scale degree.

Thesis test (paper §"Friction"): regional style should show up in WHERE a performance departs from the 12-tone
equal-tempered (12-TET) grid that note transcribers assume, e.g. raised/lowered degrees of the northwestern 苦音 or
Cantonese 乙反 modes. Aggregate friction (tracker or transcriber disagreement) did not separate regions; this
measures the musically specific version.

Per recording (RMVPE F0 of the separated voice, 10 ms):
  1. steady frames: voiced, local slope < 3 st/s over 50 ms (excludes glides and attacks)
  2. global tuning: circular mean of the fractional semitone of steady frames (removed)
  3. tonic (宫): pentatonic template fit (gong, shang, jue, zhi, yu = 0,2,4,7,9) on the 12-bin pitch-class histogram
  4. per degree d = 0..11 relative to gong: occupancy (share of steady frames), median deviation from the tuned
     12-TET grid (cents), and spread (IQR, cents)
Output: data/regionclf/intonation_<source>.csv  (one row per recording, 36 profile features + metadata)
Run (py312): python src/regionclf/intonation.py [--source v1|v2]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PENTA = np.array([0, 2, 4, 7, 9])


def profile(f0: np.ndarray) -> dict | None:
    v = f0 > 0
    if v.sum() < 300:
        return None
    st = np.full(len(f0), np.nan)
    st[v] = 12 * np.log2(f0[v] / 440.0) + 69
    # local slope over 50 ms (5 frames), st/s
    slope = np.abs(np.gradient(pd.Series(st).rolling(5, center=True, min_periods=3).mean().to_numpy())) * 100
    steady = v & (slope < 3)
    s = st[steady]
    if len(s) < 200:
        return None
    frac = s - np.round(s)
    tune = np.angle(np.mean(np.exp(2j * np.pi * frac))) / (2 * np.pi)  # semitones, (-0.5, 0.5]
    s = s - tune
    pc = np.round(s).astype(int) % 12
    dev = (s - np.round(s)) * 100  # cents from the tuned 12-TET grid
    hist = np.bincount(pc, minlength=12) / len(pc)
    gong = int(np.argmax([hist[(PENTA + k) % 12].sum() for k in range(12)]))
    deg = (pc - gong) % 12
    out = {"tuning_cents": tune * 100, "n_steady": int(len(s)), "steady_share": float(steady.sum() / v.sum())}
    for d in range(12):
        m = deg == d
        out[f"occ_{d}"] = float(m.mean())
        out[f"dev_{d}"] = float(np.median(dev[m])) if m.sum() >= 30 else np.nan
        out[f"iqr_{d}"] = float(np.subtract(*np.percentile(dev[m], [75, 25]))) if m.sum() >= 30 else np.nan
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="v1", choices=["v1", "v2"])
    args = ap.parse_args()
    f0dir = (ROOT / "data" / "transcription" / "critic" / "f0_rmvpe" if args.source == "v1"
             else ROOT / "data" / "regions_v2" / "transcription" / "f0_rmvpe")
    rows = []
    for f in sorted(f0dir.glob("*/*.npz")):
        p = profile(np.load(f)["f0"])
        if p:
            rows.append({"video_id": f.stem, "region": f.parent.name, **p})
    out = ROOT / "data" / "regionclf" / f"intonation_{args.source}.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(len(rows), "recordings →", out)


if __name__ == "__main__":
    main()
