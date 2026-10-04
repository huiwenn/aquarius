"""
Family "sequence": bag-of-n-grams (TF-IDF, sublinear tf) over the token vocabularies of exp_seq_tok.py,
with a class-balanced linear SVM or logistic regression, on the shared grouped folds.

  sweep     vocab × n-gram range × {svm, logreg} on every task; results go to data/regionclf/tok/sweep_ngram.csv
            (not the shared results.csv, to keep that file readable)
  log       re-runs a chosen set of configurations and appends them to the shared results.csv
  tvar      T15/T5 only: train on both transcription variants (primary + rosvot) of the training recordings,
            predict with the mean probability over both variants of the test recording (train+test-time aug.)
  coef      fits logreg on all of A5 / E / T15 and prints the top-weighted n-grams per region

Run (py312 or regionseq env):
  python src/regionclf/exp_seq_ngram.py sweep  [--tasks A5,E,T15,T5]
  python src/regionclf/exp_seq_ngram.py log
  python src/regionclf/exp_seq_ngram.py tvar --tasks T15,T5
  python src/regionclf/exp_seq_ngram.py coef
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, scores, task  # noqa: E402
from regionclf.exp_seq_tok import TOK, task_tokens  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import make_pipeline, make_union  # noqa: E402
from sklearn.preprocessing import FunctionTransformer  # noqa: E402
from sklearn.svm import LinearSVC  # noqa: E402

TASKS = ["A5", "E", "T15", "T5"]


def vec(n_lo, n_hi, col):
    return make_pipeline(FunctionTransformer(lambda X, c=col: [x[c] for x in X]),
                         TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(n_lo, n_hi),
                                         sublinear_tf=True, min_df=2, max_features=200_000))


def clf(kind, C):
    if kind == "svm":
        return LinearSVC(C=C, class_weight="balanced", max_iter=20000)
    return LogisticRegression(C=C, class_weight="balanced", max_iter=3000)


def make_model(vocabs, n_lo, n_hi, kind, C):
    feats = make_union(*[vec(n_lo, n_hi, i) for i in range(len(vocabs))])
    return make_pipeline(feats, clf(kind, C))


def docs(task_name, vocabs, recs):
    per = [task_tokens(task_name, v, recs) for v in vocabs]
    return [tuple(" ".join(p[i]) for p in per) for i in range(len(recs))]


def run(task_name, vocabs, n_lo, n_hi, kind, C, log=False):
    recs = task(task_name)
    X = docs(task_name, vocabs, recs)
    idx = {id(r): i for i, r in enumerate(recs)}

    def fp(tr, te):
        m = make_model(vocabs, n_lo, n_hi, kind, C)
        m.fit([X[idx[id(r)]] for r in tr], labels(tr))
        return m.predict([X[idx[id(r)]] for r in te])

    y, pred = cv_predict(recs, fp)
    name = f"ngram[{'+'.join(vocabs)}|{n_lo}-{n_hi}]/{kind}"
    if log is True:
        log_result(name, "sequence", task_name, y, pred, notes=f"tfidf sublinear, C={C}")
    s = scores(y, pred)
    out = dict(task=task_name, vocab="+".join(vocabs), n=f"{n_lo}-{n_hi}", clf=kind, C=C, **s)
    if log == "defer":  # caller logs in the main process (safe concurrent appends)
        out.update(_name=name, _y=y, _pred=pred, _notes=f"tfidf sublinear, C={C}")
    return out


SWEEP_VOCABS = [["int"], ["deg"], ["degoct"], ["degdur"], ["intdur"], ["dur"], ["contour"], ["abs"],
                ["deg", "int"], ["deg", "int", "dur"], ["degdur", "intdur"], ["deg", "int", "degdur", "dur"]]
NRANGES = [(1, 1), (1, 2), (1, 3), (1, 4), (2, 4), (3, 5)]


def sweep(tasks):
    jobs = [(t, v, lo, hi, k, C) for t in tasks for v in SWEEP_VOCABS for lo, hi in NRANGES
            for k, C in [("svm", 0.1), ("logreg", 3.0)]]
    out = Parallel(n_jobs=8, verbose=5)(delayed(run)(*j) for j in jobs)
    df = pd.DataFrame(out)
    f = TOK / "sweep_ngram.csv"
    df.to_csv(f, mode="a", header=not f.exists(), index=False)
    for t in tasks:
        d = df[df.task == t].sort_values("macro_f1", ascending=False)
        print(f"\n== {t}\n", d.head(12).to_string(index=False))
        print(d.pivot_table(index="vocab", columns="n", values="macro_f1", aggfunc="max").round(3).to_string())


ALL = ["deg", "int", "degdur", "intdur", "dur", "degoct", "contour"]
LOG_CONFIGS = [  # chosen after the sweep: one per vocabulary (1-4-grams) + combinations; logreg C=3 throughout
    (["int"], 1, 4, "logreg", 3.0), (["deg"], 1, 4, "logreg", 3.0), (["degoct"], 1, 4, "logreg", 3.0),
    (["degdur"], 1, 4, "logreg", 3.0), (["intdur"], 1, 3, "logreg", 3.0), (["dur"], 1, 4, "logreg", 3.0),
    (["contour"], 1, 4, "logreg", 3.0), (["abs"], 1, 4, "logreg", 3.0),
    (["deg", "int", "degdur", "dur"], 1, 4, "logreg", 3.0), (["deg", "int", "degdur", "dur"], 1, 4, "svm", 0.1),
    (ALL, 1, 4, "logreg", 3.0),
]


def log_all(tasks):
    jobs = [(t, v, lo, hi, k, C, "defer") for t in tasks for v, lo, hi, k, C in LOG_CONFIGS]
    for o in Parallel(n_jobs=6)(delayed(run)(*j) for j in jobs):
        log_result(o["_name"], "sequence", o["task"], o["_y"], o["_pred"], notes=o["_notes"])


def tvar(tasks, vocabs=ALL):
    from regionclf.common import load
    ros = load("trans_rosvot")
    ros_docs = dict(zip([r["item_id"] for r in ros], docs("T15", vocabs, ros)))
    for t in tasks:
        recs = task(t)
        X = docs(t, vocabs, recs)
        idx = {id(r): i for i, r in enumerate(recs)}

        def fp(tr, te, tta=True):
            Xtr = [X[idx[id(r)]] for r in tr] + [ros_docs[r["item_id"]] for r in tr if r["item_id"] in ros_docs]
            ytr = list(labels(tr)) + [r["region"] for r in tr if r["item_id"] in ros_docs]
            m = make_model(vocabs, 1, 4, "logreg", 3.0).fit(Xtr, ytr)
            p = m.predict_proba([X[idx[id(r)]] for r in te])
            if tta:
                for i, r in enumerate(te):
                    if r["item_id"] in ros_docs:
                        p[i] = (p[i] + m.predict_proba([ros_docs[r["item_id"]]])[0]) / 2
            return m.classes_[p.argmax(1)]

        for tta in (False, True):
            y, pred = cv_predict(recs, lambda a, b: fp(a, b, tta))
            log_result(f"ngram[{'+'.join(vocabs)}|1-4]/logreg+rosvot_train" + ("+tta" if tta else ""), "sequence",
                       t, y, pred, notes="adds ROSVOT transcriptions of training recordings as extra samples")


def coef(tasks, vocab="deg", n_hi=3, top=8):
    for t in tasks:
        recs = task(t)
        X = [" ".join(x) for x in task_tokens(t, vocab, recs)]
        v = TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(1, n_hi), sublinear_tf=True,
                            min_df=5)
        Z = v.fit_transform(X)
        m = LogisticRegression(C=1.0, class_weight="balanced", max_iter=3000).fit(Z, labels(recs))
        names = np.array(v.get_feature_names_out())
        print(f"\n== {t} ({vocab}, 1-{n_hi}-grams)")
        for c, w in zip(m.classes_, m.coef_):
            o = np.argsort(-w)[:top]
            print(f"{c:<16}", " | ".join(f"{names[i].replace(' ', '-')}" for i in o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["sweep", "log", "coef", "tvar"])
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--vocab", default="deg")
    ap.add_argument("--n", type=int, default=3)
    a = ap.parse_args()
    ts = a.tasks.split(",")
    {"sweep": sweep, "log": log_all, "tvar": tvar, "coef": lambda t: coef(t, a.vocab, a.n)}[a.mode](ts)
