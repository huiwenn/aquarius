"""
Family "data/reduction": does reducing transcriptions to skeleton melodies (reduce.py) help
(a) within-domain classification (T15, T5) and (b) score→performance transfer (A→T5, E→T14) and mixing (T5 + A)?
Representation: theory features + gradient boosting (as exp_mixing), so only the melodic reduction changes.

Run (py312): python src/regionclf/exp_reduce.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import A5_REGIONS, folds, labels, load, log_result, task  # noqa: E402
from regionclf.features import theory_features  # noqa: E402
from regionclf.reduce import reduce  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402


def with_reduction(recs, level):
    return [{**r, "notes": reduce(r["notes"], level)} for r in recs] if level else recs


def X(recs):
    return np.vstack([theory_features(r["notes"]) for r in recs])


def hgb():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, class_weight="balanced", random_state=0)


def cv(name, target, extra=()):
    y = labels(target)
    pred = np.empty(len(target), dtype=object)
    Xt = X(target)
    Xe = [X(e) for e in extra]
    for tr, te in folds(target):
        tg = {target[i]["group"] for i in te}
        Xtr, ytr = [Xt[tr]], [y[tr]]
        for e, xe in zip(extra, Xe):
            m = np.array([r["group"] not in tg and r["region"] in set(y) for r in e])
            Xtr.append(xe[m])
            ytr.append(labels(e)[m])
        m = hgb().fit(np.vstack(Xtr), np.concatenate(ytr))
        pred[te] = m.predict(Xt[te])
    return y, pred


def main() -> None:
    A = load("anthology")
    E = load("essen")
    for level in (0, 1, 2, 3):
        T15 = with_reduction(task("T15"), level)
        T5 = [r for r in T15 if r["region"] in A5_REGIONS]
        tag = f"reduce L{level}"
        y, p = cv(f"{tag} T15", T15)
        log_result(f"{tag} (transcriptions)", "data", "T15", y, p, "skeleton reduction of transcriptions")
        y, p = cv(f"{tag} T5", T5)
        log_result(f"{tag} (transcriptions)", "data", "T5", y, p, "skeleton reduction of transcriptions")
        # transfer: train on scores (A reduced at level 1 only, i.e. near-identity), test on reduced transcriptions
        Ared = with_reduction(A, min(level, 2))
        tg = {r["group"] for r in T5}
        src = [r for r in Ared if r["group"] not in tg]
        m = hgb().fit(X(src), labels(src))
        log_result(f"{tag} transfer A→T5", "data", "T5", labels(T5), m.predict(X(T5)),
                   "train anthology only, test reduced transcriptions")
        Ered = with_reduction(E, min(level, 2))
        TE = [r for r in T15 if r["region"] in {r["region"] for r in E}]
        tg = {r["group"] for r in TE}
        src = [r for r in Ered if r["group"] not in tg]
        m = hgb().fit(X(src), labels(src))
        log_result(f"{tag} transfer E→T14", "data", "T14", labels(TE), m.predict(X(TE)),
                   "train essen only, test reduced transcriptions")
        y, p = cv(f"{tag} T5+A", T5, [Ared])
        log_result(f"{tag} T5 + A (mixed)", "data", "T5", y, p, "reduced transcriptions + anthology")


if __name__ == "__main__":
    main()
