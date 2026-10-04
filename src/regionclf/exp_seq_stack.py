"""
Family "sequence": stacking the n-gram model with the music-theory features.

Inside each outer training fold: out-of-fold class probabilities of the TF-IDF n-gram logistic regression
(all 7 symbolic vocabularies, 1–4-grams, C=3; inner StratifiedGroupKFold(5)) are appended to the theory feature
vector (features.matrix) and a class-balanced HistGradientBoosting model is trained on the concatenation. At test
time the n-gram model is refit on the whole training fold. Also reports a simple late fusion (mean of n-gram
logreg and theory-HGB probabilities).

Run (regionseq env): python src/regionclf/exp_seq_stack.py [--tasks T5,T15,E,A5]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, task  # noqa: E402
from regionclf.exp_seq_ngram import ALL, docs, make_model  # noqa: E402
from regionclf.features import matrix  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.model_selection import StratifiedGroupKFold  # noqa: E402


def hgb():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, class_weight="balanced", random_state=0)


def ngram():
    return make_model(ALL, 1, 4, "logreg", 3.0)


def run(t):
    recs = task(t)
    X = docs(t, ALL, recs)
    Th = matrix(recs)
    idx = {id(r): i for i, r in enumerate(recs)}
    fused = {}

    def fp(tr, te):
        itr = np.array([idx[id(r)] for r in tr])
        ite = np.array([idx[id(r)] for r in te])
        y = labels(tr)
        g = np.array([r["group"] for r in tr])
        classes = np.unique(y)
        oof = np.zeros((len(tr), len(classes)))
        for a, b in StratifiedGroupKFold(5, shuffle=True, random_state=1).split(itr, y, g):
            m = ngram().fit([X[i] for i in itr[a]], y[a])
            oof[b] = m.predict_proba([X[i] for i in itr[b]])
        m = ngram().fit([X[i] for i in itr], y)
        pte = m.predict_proba([X[i] for i in ite])
        st = hgb().fit(np.hstack([Th[itr], oof]), y)
        h = hgb().fit(Th[itr], y)
        fused[tuple(ite)] = classes[(pte + h.predict_proba(Th[ite])).argmax(1)]
        return st.predict(np.hstack([Th[ite], pte]))

    y, pred = cv_predict(recs, fp)
    log_result("stack[theory+ngram_oof]/hgb", "sequence", t, y, pred,
               notes="theory feats + inner-OOF n-gram logreg probs (7 vocabs, 1-4) -> HGB")
    pf = np.empty(len(recs), dtype=object)
    for k, v in fused.items():
        pf[list(k)] = v
    log_result("latefusion[ngram_logreg+theory_hgb]", "sequence", t, y, pf, notes="mean of class probabilities")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="T5,T15,E,A5")
    for t in ap.parse_args().tasks.split(","):
        run(t)
