"""
Family "image", step 3: frozen backbone embeddings (exp_image_embed.py) -> song-level mean pooling over crops ->
standardized logistic regression (class-balanced), on the shared song-grouped folds.

Experiments logged: img-<backbone>-<rendering>/logreg for every available (backbone, rendering) and task, plus
fusions: img-<backbone>-all (concat of the renderings' pooled embeddings) and img-all-all.
Tasks: A5 (anthology), E and E5prior (essen), T15/T5 (trans_primary).

Run (arm64 env):
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_frozen.py [--tasks T15,T5,E,E5prior,A5]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, task  # noqa: E402
from regionclf.exp_image_embed import MAX_CROPS, crop_subset  # noqa: E402
from regionclf.exp_image_mfdmap import e5prior  # noqa: E402
from regionclf.exp_image_render import IMG, RENDERINGS, already_logged, get  # noqa: E402

BACKBONES = ["dinov2", "resnet50", "clip"]
SOURCE = {"A5": "anthology", "E": "essen", "E5prior": "essen", "T15": "trans_primary", "T5": "trans_primary"}


def get_task(name):
    return e5prior() if name == "E5prior" else task(name)


def pooled(backbone, source, rendering):
    """(item_id -> mean-pooled embedding) or None if not embedded yet."""
    f = IMG / f"emb_{backbone}_{source}_{rendering}.npy"
    if not f.exists():
        return None
    emb = np.load(f).astype(np.float32)
    _, song, _, item_id = get(source, rendering)
    song = song[crop_subset(song, MAX_CROPS.get(source))]
    if len(song) != len(emb):
        return None
    sums = np.zeros((len(item_id), emb.shape[1]), np.float32)
    np.add.at(sums, song, emb)
    cnt = np.bincount(song, minlength=len(item_id))[:, None]
    return dict(zip(item_id, sums / np.maximum(cnt, 1)))


def clf(dim, n):
    steps = [StandardScaler()]
    if dim > 1024:
        steps.append(PCA(min(512, n // 2), random_state=0))
    return make_pipeline(*steps, LogisticRegression(C=0.05, max_iter=3000, class_weight="balanced"))


def run(recs, name, emb_by_id, exp, notes=""):
    if already_logged(name, exp):
        return None
    X = {r["item_id"]: emb_by_id[r["item_id"]] for r in recs}
    dim = len(next(iter(X.values())))

    def fp(tr, te):
        m = clf(dim, len(tr)).fit(np.stack([X[r["item_id"]] for r in tr]), labels(tr))
        return m.predict(np.stack([X[r["item_id"]] for r in te]))
    y, pred = cv_predict(recs, fp)
    return log_result(exp, "image", name, y, pred, notes=notes)


def main(tasks):
    for name in tasks:
        recs = get_task(name)
        src = SOURCE[name]
        allfeat = {}
        for b in BACKBONES:
            per = {}
            for rd in RENDERINGS:
                e = pooled(b, src, rd)
                if e is None:
                    continue
                per[rd] = e
                run(recs, name, e, f"img-{b}-{rd}/logreg",
                    notes="frozen backbone, crops mean-pooled per song" + (
                        ", E5prior = Essen Han 5 provinces (Khoo 2012/13 setting), grouped 5-fold"
                        if name == "E5prior" else ""))
            if len(per) > 1:
                cat = {i: np.concatenate([per[rd][i] for rd in per]) for i in per[next(iter(per))]}
                run(recs, name, cat, f"img-{b}-all/logreg", notes="concat of renderings: " + ",".join(per))
                allfeat.update({(b, rd): v for rd, v in per.items()})
        if len({k[0] for k in allfeat}) > 1:
            keys = sorted(allfeat)
            cat = {i: np.concatenate([allfeat[k][i] for k in keys]) for i in allfeat[keys[0]]}
            run(recs, name, cat, "img-all-all/logreg", notes="concat of all backbones x renderings (PCA min(512, n/2))")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="T15,T5,E,E5prior,A5")
    main(ap.parse_args().tasks.split(","))
