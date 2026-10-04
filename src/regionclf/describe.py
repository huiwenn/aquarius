"""
Descriptive computational musicology per source × region, to check learned signal against the literature.

Per song (tonic-relative via estimate_gong):
  mode      final note's degree mapped to 宫(0) 商(2) 角(4) 徵(7) 羽(9), else "other"
  pianyin   duration share of 偏音 (清角 fa=5, 变宫 ti=11; also 变徵 6, 闰 10)
  fourth    share of melodic intervals that are ±5 semitones (纯四度: 西北 信天游/花儿 hallmark)
  step      share of intervals of 1–2 semitones (stepwise)
  leap      share of |interval| ≥ 7 (fifth or more)
  range     p95 − p5 semitones
  n_degrees scale degrees with ≥3% duration (5 = pentatonic, 6–7 = hexa/heptatonic)
Output: data/regionclf/describe.csv (per region × source aggregates) and a printed table.
Literature reference strings come from secaiqu.mapping.SECAIQU_METADATA['style'].

Run (py312): python src/regionclf/describe.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import load  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MODE = {0: "宫", 2: "商", 4: "角", 7: "徵", 9: "羽"}


def song_stats(notes):
    p = notes[:, 2].astype(int)
    g = estimate_gong(notes)
    rel = (p - g) % 12
    w = np.bincount(rel, weights=notes[:, 1], minlength=12)
    w = w / w.sum()
    iv = np.diff(p)
    return {"mode": MODE.get(int(rel[-1]), "other"), "pianyin": w[[5, 11, 6, 10]].sum(),
            "fourth": np.mean(np.abs(iv) == 5), "step": np.mean((np.abs(iv) >= 1) & (np.abs(iv) <= 2)),
            "leap": np.mean(np.abs(iv) >= 7), "range": np.percentile(p, 95) - np.percentile(p, 5),
            "n_degrees": int((w >= 0.03).sum())}


def main() -> None:
    rows = []
    for src in ["anthology", "essen", "trans_primary"]:
        for r in load(src):
            rows.append({"source": src, "region": r["region"], **song_stats(r["notes"])})
    d = pd.DataFrame(rows)
    num = d.groupby(["region", "source"])[["pianyin", "fourth", "step", "leap", "range", "n_degrees"]].mean()
    modes = pd.crosstab([d.region, d.source], d["mode"], normalize="index")[["宫", "商", "角", "徵", "羽", "other"]]
    out = num.join(modes).round(3)
    out["n"] = d.groupby(["region", "source"]).size()
    out.to_csv(ROOT / "data" / "regionclf" / "describe.csv")
    pd.set_option("display.width", 200)
    print(out.to_string())


if __name__ == "__main__":
    main()
