"""
Family "pretrained": frozen embeddings (cached .npy under data/regionclf/emb/) → linear / kernel / kNN classifiers
on the shared grouped folds. Every (embedding, classifier, task) run is logged to data/regionclf/results.csv.

Embeddings are produced by:
  src/regionclf/emb_clamp.py   CLaMP 3 C2 (c2 = joint-space projection, c2pre = pooled encoder) and M3 (CLaMP 2)
  src/regionclf/emb_text.py    text-embedding models on ABC / 简谱 scale-degree strings
File naming: {emb}_{source}.npy with emb e.g. "c2_mtf_tonic" and source ∈ anthology / essen / trans_primary.

Classifiers (fixed hyper-parameters, no tuning on test folds):
  LR   StandardScaler → LogisticRegression(C=0.1, class_weight=balanced)
  SVM  StandardScaler → SVC(RBF, C=1, class_weight=balanced)
  kNN  L2-normalized → 5-NN cosine, distance-weighted
  +theory: LR on [standardized embedding, standardized theory features] (regionclf.features.matrix)

Run (arm64 env, CPU only):
  PYTHONPATH=src ~/miniforge3/envs/regionclf/bin/python src/regionclf/exp_pretrained.py \
      --embs c2_mtf_raw,c2_mtf_tonic --clfs LR,SVM,kNN --tasks A5,E,T15,T5 [--dry] [--theory] [--by channel]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.neighbors import KNeighborsClassifier  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import Normalizer, StandardScaler  # noqa: E402
from sklearn.svm import SVC  # noqa: E402

from regionclf.common import D, cv_predict, log_result, task  # noqa: E402

EMB = D / "emb"
SOURCE = {"A5": "anthology", "E": "essen", "T15": "trans_primary", "T5": "trans_primary"}


def make_clf(name):
    if name == "LR":
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=3000, class_weight="balanced"))
    if name == "SVM":
        return make_pipeline(StandardScaler(), SVC(C=1.0, class_weight="balanced"))
    if name == "kNN":
        return make_pipeline(Normalizer(), KNeighborsClassifier(5, weights="distance", metric="cosine"))
    raise ValueError(name)


def features(recs, emb: str, source: str, theory: bool = False) -> np.ndarray:
    full = np.load(EMB / f"{emb}_{source}.npy")
    from regionclf.common import load
    ids = {r["item_id"]: i for i, r in enumerate(load(source))}
    X = full[[ids[r["item_id"]] for r in recs]]
    if theory:
        from regionclf.features import matrix
        X = np.hstack([X, matrix(recs)])
    return X.astype(np.float64)


def run(emb, clf, tname, dry=False, theory=False, by="group"):
    recs = task(tname)
    X = features(recs, emb, SOURCE[tname], theory)
    X = np.nan_to_num(X)
    row = {r["item_id"]: i for i, r in enumerate(recs)}

    def fp(tr, te):
        m = make_clf(clf)
        m.fit(X[[row[r["item_id"]] for r in tr]], [r["region"] for r in tr])
        return m.predict(X[[row[r["item_id"]] for r in te]])

    y, pred = cv_predict(recs, fp, by=by)
    name = f"{emb}{'+theory' if theory else ''}+{clf}{'@channelCV' if by == 'channel' else ''}"
    if dry:
        from regionclf.common import scores
        s = scores(y, pred)
        print(f"[{tname}] {name} (dry): macroF1 {s['macro_f1']:.3f}", flush=True)
        return s
    return log_result(name, "pretrained", tname, y, pred, notes=f"frozen {emb} dim={X.shape[1]}; {clf}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--embs", required=True)
    ap.add_argument("--clfs", default="LR,SVM,kNN")
    ap.add_argument("--tasks", default="A5,E,T15,T5")
    ap.add_argument("--theory", action="store_true", help="concatenate theory features (LR only)")
    ap.add_argument("--by", default="group", help="'channel' = folds grouped by recording channel/volume")
    ap.add_argument("--dry", action="store_true", help="don't log to results.csv")
    a = ap.parse_args()
    for emb in a.embs.split(","):
        for t in a.tasks.split(","):
            for c in a.clfs.split(","):
                run(emb, c, t, a.dry, a.theory, a.by)


if __name__ == "__main__":
    main()


def transfer(emb, clf, train_task="A5", test_task="T5", dry=False):
    """Train on all of one source, test on another (label sets must match, e.g. A5 → T5). Not CV.
    Run: python -c "from regionclf.exp_pretrained import transfer; transfer('c2pre_mtf_tonic', 'SVM')"
    """
    tr, te = task(train_task), task(test_task)
    Xtr = np.nan_to_num(features(tr, emb, SOURCE[train_task]))
    Xte = np.nan_to_num(features(te, emb, SOURCE[test_task]))
    m = make_clf(clf).fit(Xtr, [r["region"] for r in tr])
    y, pred = np.array([r["region"] for r in te]), m.predict(Xte)
    name = f"transfer {train_task}→{test_task} {emb}+{clf}"
    if dry:
        from regionclf.common import scores
        print(name, scores(y, pred))
        return
    return log_result(name, "pretrained", test_task, y, pred, notes=f"train on all {train_task}, test on {test_task}")
