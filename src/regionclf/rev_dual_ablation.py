"""
R5: ablations of the dual-view model (surface n-gram on raw transcriptions ⊕ skeleton n-gram on reduced
transcriptions + reduced external scores). Every variant: 3 fold seeds pooled, compared to the plain n-gram
baseline with bootstrap CIs and a paired permutation test (rev_stats.compare).

Axes
  scores      none (skeleton view trained on reduced transcriptions only → pure two-view self-ensemble control) /
              Essen / Anthology / both
  level       skeleton reduction level 1, 2, 3
  weight      external-source mass relative to target: 0.25×, 1× (default: equal total), 4×
  alpha       fusion weight of the skeleton view: 0.25, 0.5 (default), 0.75
Results → data/regionclf/review_dual_ablation.csv

Run (py312): OMP_NUM_THREADS=2 python src/regionclf/rev_dual_ablation.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import A5_REGIONS, D, labels, load, task  # noqa: E402
from regionclf.rev_stats import compare, oof  # noqa: E402

SEEDS = (0, 1, 2)


def dual(externals, level=2, mass=1.0, alpha=0.5):
    def fn(tr, te):
        classes = sorted(set(labels(tr)))
        tg = {r["group"] for r in te}
        ext = [r for e in externals for r in e if r["group"] not in tg and r["region"] in set(classes)]
        w = np.array([1.0] * len(tr) + [mass * len(tr) / max(1, len(ext))] * len(ext))
        sk = F.fit_ngram(tr + ext, level=level, weights=w)
        sf = F.fit_ngram(tr)
        p = alpha * F.proba(sk, classes)([F.doc(r, level) for r in te]) + \
            (1 - alpha) * F.proba(sf, classes)([F.doc(r) for r in te])
        return np.array(classes)[p.argmax(1)]
    return fn


def main() -> None:
    A, E = load("anthology"), load("essen")
    E5 = [r for r in E if r["region"] in A5_REGIONS]
    rows = []
    for tname, recs, srcs in [("T15", task("T15"), {"none": [], "E": [E], "E+A": [E, A]}),
                              ("T5", task("T5"), {"none": [], "E5": [E5], "A": [A], "A+E5": [A, E5]})]:
        base = [oof(f"{tname}_ngram", recs, F.ngram_fold, s) for s in SEEDS]
        default_src = "E" if tname == "T15" else "A+E5"
        configs = [(f"scores={k}", dict(externals=v)) for k, v in srcs.items()]
        configs += [(f"level={L} (scores={default_src})", dict(externals=srcs[default_src], level=L)) for L in (1, 3)]
        configs += [(f"mass={m}× (scores={default_src})", dict(externals=srcs[default_src], mass=m))
                    for m in (0.25, 4.0)]
        configs += [(f"alpha={a} (scores={default_src})", dict(externals=srcs[default_src], alpha=a))
                    for a in (0.25, 0.75)]
        for label, kw in configs:
            key = f"{tname}_dualabl_" + label.replace(" ", "").replace("=", "").replace("(", "_").replace(")", "")\
                .replace("+", "p").replace("×", "x").replace(".", "")
            runs = [oof(key, recs, dual(**kw), s) for s in SEEDS]
            r = compare(f"{tname} dual-view [{label}] vs n-gram", runs, base, n_boot=1000, n_perm=5000)
            rows.append({"task": tname, "variant": label, **r})
            pd.DataFrame(rows).round(4).to_csv(D / "review_dual_ablation.csv", index=False)


if __name__ == "__main__":
    main()
