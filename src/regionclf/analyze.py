"""
Analysis of the best models, for the computational-musicology reading in docs/region_classification.md.

1. dual-view (exp_fusion.dual) under channel-grouped folds (honest estimate for transcriptions)
2. out-of-fold predictions of the multi-viewpoint n-gram model on A5, E, T15 (+ dual-view on T15)
   → per-region F1, confusion matrices (saved as CSV)
3. "does confusion follow geography?": Spearman correlation between the symmetric confusion rate of each
   region pair and the great-circle distance between approximate region centroids, with a permutation
   (Mantel-style) p-value over region labels. Also: Han vs minority block structure.

Run (py312): python src/regionclf/analyze.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import D, folds, labels, load, log_result, task  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402

CENTROIDS = {  # approximate lat, lon of each 色彩区's core area
    "东北部平原": (37.5, 116.5), "西北部高原": (37.5, 109.5), "江淮": (33.0, 117.5), "江浙平原": (30.8, 120.3),
    "闽台": (25.3, 118.5), "粤": (22.8, 113.3), "客家特区": (24.5, 116.0), "江汉": (30.5, 113.5),
    "湘": (27.5, 112.0), "赣": (27.3, 115.5), "西南高原": (29.5, 105.0),
    "西南多民族古老原始文化民歌区": (25.0, 106.0), "藏族民歌区": (30.5, 91.0), "新疆民歌区": (42.0, 84.0),
    "北方草原文化民歌区": (43.5, 113.0)}
MINORITY = {"西南多民族古老原始文化民歌区", "藏族民歌区", "新疆民歌区", "北方草原文化民歌区"}
OUT = D / "analysis"


def haversine(a, b):
    la1, lo1, la2, lo2 = map(np.radians, (*a, *b))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(h))


def oof(recs, predict_fold, by="group"):
    y = labels(recs)
    pred = np.empty(len(recs), dtype=object)
    for tr, te in folds(recs, by=by):
        pred[te] = predict_fold([recs[i] for i in tr], [recs[i] for i in te])
    return y, pred


def geography(name, y, pred, n_perm=5000, seed=0):
    regs = sorted(set(y))
    cm = confusion_matrix(y, pred, labels=regs).astype(float)
    rate = cm / cm.sum(1, keepdims=True)
    sym = (rate + rate.T) / 2
    pd.DataFrame(cm.astype(int), index=regs, columns=regs).to_csv(OUT / f"confusion_{name}.csv")
    pairs = [(i, j) for i in range(len(regs)) for j in range(i + 1, len(regs))]
    dist = np.array([haversine(CENTROIDS[regs[i]], CENTROIDS[regs[j]]) for i, j in pairs])
    conf = np.array([sym[i, j] for i, j in pairs])
    rho = spearmanr(dist, conf).correlation
    rng = np.random.RandomState(seed)
    null = []
    for _ in range(n_perm):
        perm = rng.permutation(len(regs))
        d = np.array([haversine(CENTROIDS[regs[perm[i]]], CENTROIDS[regs[perm[j]]]) for i, j in pairs])
        null.append(spearmanr(d, conf).correlation)
    p = (np.sum(np.array(null) <= rho) + 1) / (n_perm + 1)
    top = sorted(((sym[i, j], regs[i], regs[j]) for i, j in pairs), reverse=True)[:6]
    print(f"\n[{name}] confusion vs distance: Spearman rho = {rho:.3f}, permutation p = {p:.4f}")
    print("  most confused pairs:", "; ".join(f"{a}–{b} {s:.2f}" for s, a, b in top))
    if any(r in MINORITY for r in regs):
        han = [r not in MINORITY for r in regs]
        hv = np.array(han)
        cross = (cm[np.ix_(hv, ~hv)].sum() + cm[np.ix_(~hv, hv)].sum()) / cm.sum()
        print(f"  Han↔minority confusion mass: {cross:.3f} of all predictions")
    rep = classification_report(y, pred, labels=regs, output_dict=True, zero_division=0)
    f1 = pd.Series({r: rep[r]["f1-score"] for r in regs}).sort_values(ascending=False)
    f1.to_csv(OUT / f"f1_{name}.csv")
    print("  per-region F1:", ", ".join(f"{k} {v:.2f}" for k, v in f1.items()))
    return rho, p


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    A, E = load("anthology"), load("essen")

    # 1. dual-view, channel-grouped
    for t, externals in [("T15", [E]), ("T5", [A, [r for r in E if r["region"] in F.A5_REGIONS]])]:
        recs = task(t)

        def dual(tr, te, externals=externals):
            classes = sorted(set(labels(tr)))
            tg = {r["group"] for r in te}
            ext = [r for e in externals for r in e if r["group"] not in tg and r["region"] in set(classes)]
            w = np.array([1.0] * len(tr) + [len(tr) / max(1, len(ext))] * len(ext))
            sk = F.fit_ngram(tr + ext, level=2, weights=w)
            sf = F.fit_ngram(tr)
            p = F.proba(sk, classes)([F.doc(r, 2) for r in te]) + F.proba(sf, classes)([F.doc(r) for r in te])
            return np.array(classes)[p.argmax(1)]
        y, pred = oof(recs, dual, by="channel")
        log_result("dual-view (surface ⊕ skeleton+scores) folds-by-channel", "fusion", t, y, pred)
        if t == "T15":
            yg, pg = oof(recs, dual, by="group")
            geography("T15_dualview", yg, pg)

    # 2–3. n-gram model on each task
    for t in ["A5", "E", "T15"]:
        y, pred = oof(task(t), F.ngram_fold)
        geography(f"{t}_ngram", y, pred)


if __name__ == "__main__":
    main()
