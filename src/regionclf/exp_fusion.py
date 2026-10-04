"""
Exploitation round: combine what worked, and test the "two layers" hypothesis for mixing data.

1. honest   best single representation (multi-viewpoint n-gram TF-IDF + LR, from exp_seq_ngram) and theory+HGB
            under song-grouped vs channel-grouped folds (T15, T5). Channel grouping removes singer/channel/recording
            leakage but depletes regions dominated by one channel (Rhymoi = 50–83% of minority regions).
2. fusion   late fusion (mean of class probabilities) of n-gram LR + theory HGB, on every task.
3. dual     dual-view data mixing for transcriptions:
              surface view  = n-gram LR on *raw* transcriptions (target training fold only)
              skeleton view = n-gram LR on *reduced* (reduce.py L2) transcriptions of the training fold
                              + reduced external scores (anthology / essen), sources re-weighted to equal mass
              prediction    = mean of the two views' probabilities
            vs surface-only, and vs naive mixing (raw transcriptions + scores in one model).
Everything logged to results.csv (family "fusion").

Run (py312): python src/regionclf/exp_fusion.py [--which honest,fusion,dual]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import A5_REGIONS, folds, labels, load, log_result, task  # noqa: E402
from regionclf.exp_seq_tok import tokenize  # noqa: E402
from regionclf.features import theory_features  # noqa: E402
from regionclf.reduce import reduce  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import make_pipeline, make_union  # noqa: E402
from sklearn.preprocessing import FunctionTransformer  # noqa: E402

VOCABS = ["deg", "int", "degdur", "intdur", "dur", "degoct", "contour"]
_doc_cache, _feat_cache = {}, {}


def doc(r, level=0):
    key = (r["source"], r["item_id"], level)
    if key not in _doc_cache:
        notes = reduce(r["notes"], level) if level else r["notes"]
        _doc_cache[key] = tuple(" ".join(tokenize(notes, v)) for v in VOCABS)
    return _doc_cache[key]


def feat(r):
    key = (r["source"], r["item_id"])
    if key not in _feat_cache:
        _feat_cache[key] = theory_features(r["notes"])
    return _feat_cache[key]


def ngram_model():
    vecs = [make_pipeline(FunctionTransformer(lambda X, c=i: [x[c] for x in X]),
                          TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 4),
                                          sublinear_tf=True, min_df=2, max_features=200_000))
            for i in range(len(VOCABS))]
    return make_pipeline(make_union(*vecs), LogisticRegression(C=10, class_weight="balanced", max_iter=3000))


def hgb():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, class_weight="balanced", random_state=0)


def proba(model, classes):
    """Align predict_proba columns to a fixed class order."""
    def f(X):
        p = model.predict_proba(X)
        out = np.zeros((len(X), len(classes)))
        for j, c in enumerate(model.classes_):
            out[:, classes.index(c)] = p[:, j]
        return out
    return f


def fit_ngram(train, level=0, weights=None):
    m = ngram_model()
    kw = {"logisticregression__sample_weight": weights} if weights is not None else {}
    m.fit([doc(r, level) for r in train], labels(train), **kw)
    return m


def cv(name, family, task_name, recs, predict_fold, by="group", notes=""):
    y = labels(recs)
    pred = np.empty(len(recs), dtype=object)
    for tr, te in folds(recs, by=by):
        pred[te] = predict_fold([recs[i] for i in tr], [recs[i] for i in te])
    return log_result(name, family, task_name, y, pred, notes)


def ngram_fold(tr, te):
    return fit_ngram(tr).predict([doc(r) for r in te])


def theory_fold(tr, te):
    m = hgb().fit(np.vstack([feat(r) for r in tr]), labels(tr))
    return m.predict(np.vstack([feat(r) for r in te]))


def fusion_fold(tr, te):
    classes = sorted(set(labels(tr)))
    m1 = fit_ngram(tr)
    m2 = hgb().fit(np.vstack([feat(r) for r in tr]), labels(tr))
    p = proba(m1, classes)([doc(r) for r in te]) + proba(m2, classes)(np.vstack([feat(r) for r in te]))
    return np.array(classes)[p.argmax(1)]


def honest():
    for t in ["T15", "T5"]:
        recs = task(t)
        for by in ["group", "channel"]:
            cv(f"ngram7[1-4]/LR folds-by-{by}", "fusion", t, recs, ngram_fold, by, "multi-viewpoint n-gram")
            cv(f"theory/hgb folds-by-{by}", "fusion", t, recs, theory_fold, by)
            cv(f"ngram+theory late fusion folds-by-{by}", "fusion", t, recs, fusion_fold, by)


def fusion():
    for t in ["A5", "E"]:
        cv("ngram+theory late fusion", "fusion", t, task(t), fusion_fold)


def dual():
    A, E = load("anthology"), load("essen")
    setups = [("T5", task("T5"), [A, [r for r in E if r["region"] in A5_REGIONS]]),
              ("T15", task("T15"), [E])]
    for t, target, externals in setups:
        def surface_only(tr, te):
            return ngram_fold(tr, te)

        def naive(tr, te, externals=externals):
            tg, regs = {r["group"] for r in te}, set(labels(tr))
            ext = [r for e in externals for r in e if r["group"] not in tg and r["region"] in regs]
            return fit_ngram(tr + ext).predict([doc(r) for r in te])

        def dual_view(tr, te, externals=externals, skeleton_only=False):
            classes = sorted(set(labels(tr)))
            tg = {r["group"] for r in te}
            ext = [r for e in externals for r in e if r["group"] not in tg and r["region"] in set(classes)]
            sk_train = tr + ext
            n_t, n_e = len(tr), max(1, len(ext))
            w = np.array([1.0 if r["source"].startswith("trans") else n_t / n_e for r in sk_train])
            sk = fit_ngram(sk_train, level=2, weights=w)
            p_sk = proba(sk, classes)([doc(r, 2) for r in te])
            if skeleton_only:
                return np.array(classes)[p_sk.argmax(1)]
            sf = fit_ngram(tr)
            p_sf = proba(sf, classes)([doc(r) for r in te])
            return np.array(classes)[(p_sk + p_sf).argmax(1)]

        cv("surface only (raw transcriptions)", "fusion", t, target, surface_only)
        cv("naive mix (raw transcriptions + scores)", "fusion", t, target, naive)
        cv("skeleton view only (reduced trans + scores, balanced)", "fusion", t, target,
           lambda tr, te: dual_view(tr, te, skeleton_only=True))
        cv("dual-view (surface ⊕ skeleton+scores)", "fusion", t, target, dual_view)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="honest,fusion,dual")
    args = ap.parse_args()
    for w in args.which.split(","):
        globals()[w]()


if __name__ == "__main__":
    main()
