"""
Family "theory": music-theory features (features.py) × {logistic regression, random forest, gradient boosting}
on every task, plus the absolute-pitch variant (confound probe) and per-block ablations.

Run (py312): python src/regionclf/exp_theory.py [--tasks A5,E,T15,T5]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, task  # noqa: E402
from regionclf.features import FEATURE_BLOCKS, matrix  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

MODELS = {
    "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000,
                                                                         class_weight="balanced")),
    "rf": lambda: RandomForestClassifier(n_estimators=500, class_weight="balanced_subsample", n_jobs=-1,
                                         random_state=0),
    "hgb": lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, class_weight="balanced",
                                                  random_state=0),
}


def run(task_name: str, X: np.ndarray, recs, model: str, exp: str, notes: str = ""):
    idx = {id(r): i for i, r in enumerate(recs)}

    def fp(tr, te):
        m = MODELS[model]()
        m.fit(X[[idx[id(r)] for r in tr]], labels(tr))
        return m.predict(X[[idx[id(r)] for r in te]])

    y, pred = cv_predict(recs, fp)
    return log_result(exp, "theory", task_name, y, pred, notes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="A5,E,T15,T5")
    ap.add_argument("--ablate", action="store_true")
    args = ap.parse_args()
    for t in args.tasks.split(","):
        recs = task(t)
        X = matrix(recs)
        for m in MODELS:
            run(t, X, recs, m, f"theory/{m}")
        Xa = matrix(recs, absolute=True)
        run(t, Xa, recs, "logreg", "theory+abs_pitch/logreg", "adds absolute pitch-class histogram + mean pitch")
        if args.ablate:
            start = 0
            for name, size in FEATURE_BLOCKS.items():
                run(t, X[:, start:start + size], recs, "logreg", f"theory[{name}]/logreg", "single block")
                start += size


if __name__ == "__main__":
    main()
