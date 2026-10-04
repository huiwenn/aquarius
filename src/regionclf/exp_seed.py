"""
Selection-optimism check: the n-gram recipe (vocab mix, n, C) was chosen on the seed-0 folds. Re-evaluate the
fixed recipe, and the dual-view model, on fresh grouped folds (seeds 1 and 2) never used for selection.
A large drop would mean the headline numbers are overfit to the folds.

Run (py312): python src/regionclf/exp_seed.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import labels, load, log_result, task  # noqa: E402
from sklearn.model_selection import StratifiedGroupKFold  # noqa: E402


def run(name, t, recs, fold_fn, seed):
    y = labels(recs)
    g = np.array([r["group"] for r in recs])
    pred = np.empty(len(recs), dtype=object)
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, g):
        pred[te] = fold_fn([recs[i] for i in tr], [recs[i] for i in te])
    log_result(f"{name} [seed {seed} folds]", "fusion", t, y, pred, "fresh folds, recipe fixed")


def main() -> None:
    E = load("essen")
    for seed in (1, 2):
        for t in ["A5", "E", "T15", "T5"]:
            run("ngram7[1-4]/LR", t, task(t), F.ngram_fold, seed)
        recs = task("T15")

        def dual(tr, te):
            classes = sorted(set(labels(tr)))
            tg = {r["group"] for r in te}
            ext = [r for r in E if r["group"] not in tg and r["region"] in set(classes)]
            w = np.array([1.0] * len(tr) + [len(tr) / max(1, len(ext))] * len(ext))
            sk = F.fit_ngram(tr + ext, level=2, weights=w)
            sf = F.fit_ngram(tr)
            p = F.proba(sk, classes)([F.doc(r, 2) for r in te]) + F.proba(sf, classes)([F.doc(r) for r in te])
            return np.array(classes)[p.argmax(1)]
        run("dual-view (surface ⊕ skeleton+scores)", "T15", recs, dual, seed)


if __name__ == "__main__":
    main()
