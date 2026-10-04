"""
R9: nested cross-validation for the main linear model (the n-gram recipe was chosen on the reported folds).
Outer: the shared grouped 5-fold (by song, and by channel for T15). Inner: grouped 3-fold on the outer training
set selects C ∈ {0.3, 1, 3, 10, 30} and (T15/T5 only) the vocabulary subset:
  all7 = deg int degdur intdur dur degoct contour | core4 = deg int degdur dur | robust3 = int intdur contour
Reports nested macro-F1 next to the fixed-recipe number.

Run (py312): OMP_NUM_THREADS=2 python src/regionclf/rev_nested.py
"""

import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline, make_union
from sklearn.preprocessing import FunctionTransformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import folds, labels, log_result, task  # noqa: E402

SUBSETS = {"all7": list(range(7)), "core4": [0, 1, 2, 4], "robust3": [1, 3, 6]}
CS = [0.3, 1, 3, 10, 30]


def model(cols, C):
    vecs = [make_pipeline(FunctionTransformer(lambda X, c=i: [x[c] for x in X]),
                          TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 4),
                                          sublinear_tf=True, min_df=2, max_features=200_000)) for i in cols]
    return make_pipeline(make_union(*vecs), LogisticRegression(C=C, class_weight="balanced", max_iter=3000))


def nested(tname, by, subsets):
    recs = task(tname)
    y = labels(recs)
    X = [F.doc(r) for r in recs]
    pred = np.empty(len(recs), dtype=object)
    chosen = []
    for tr, te in folds(recs, by=by):
        g = np.array([recs[i][by] for i in tr])
        inner = list(StratifiedGroupKFold(3, shuffle=True, random_state=1).split(np.zeros(len(tr)), y[tr], g))
        best, best_s = None, -1
        for sname in subsets:
            for C in CS:
                s = []
                for itr, ite in inner:
                    m = model(SUBSETS[sname], C).fit([X[tr[i]] for i in itr], y[tr][itr])
                    s.append(f1_score(y[tr][ite], m.predict([X[tr[i]] for i in ite]), average="macro"))
                if np.mean(s) > best_s:
                    best, best_s = (sname, C), np.mean(s)
        chosen.append(best)
        m = model(SUBSETS[best[0]], best[1]).fit([X[i] for i in tr], y[tr])
        pred[te] = m.predict([X[i] for i in te])
    log_result(f"n-gram LR, NESTED selection (folds by {by})", "review_nested", tname, y, pred,
               f"inner-selected per outer fold: {chosen}")


def main() -> None:
    nested("T15", "group", list(SUBSETS))
    nested("T15", "channel", list(SUBSETS))
    nested("T5", "group", list(SUBSETS))
    nested("E", "group", ["all7"])
    nested("A5", "group", ["all7"])


if __name__ == "__main__":
    main()
