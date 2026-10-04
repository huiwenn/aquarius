"""
Family "sequence": linear probe on the frozen SSL Transformer (exp_seq_pretrain.py checkpoint).

Each song → mean-pooled hidden state (d=128) averaged over sliding windows of 256 notes → standardized →
class-balanced logistic regression on the shared folds. Tests whether masked-note pretraining yields a
region-informative embedding without any fine-tuning.

Run (regionseq env): python src/regionclf/exp_seq_probe.py [--tasks T5,T15,E,A5] [--ckpt data/regionclf/tok/ssl_mlm_all.pt]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(2)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, task  # noqa: E402
from regionclf.exp_seq_nn import DEV, INPUTS, TF, encode_notes, pad, windows  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402


@torch.no_grad()
def embed(model, recs, bs=128):
    model.eval()
    ws, owner = [], []
    for i, r in enumerate(recs):
        for w in windows(encode_notes(r["notes"])):
            ws.append(w)
            owner.append(i)
    out = torch.cat([model.encode(pad(ws[b:b + bs]).to(DEV)).cpu() for b in range(0, len(ws), bs)]).numpy()
    owner = np.array(owner)
    return np.stack([out[owner == i].mean(0) for i in range(len(recs))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="T5,T15,E,A5")
    ap.add_argument("--ckpt", default="data/regionclf/tok/ssl_mlm_all.pt")
    a = ap.parse_args()
    model = TF(INPUTS["fact"], n_cls=2)
    model.load_state_dict(torch.load(a.ckpt, map_location="cpu"))
    model = model.to(DEV)
    tag = Path(a.ckpt).stem
    for t in a.tasks.split(","):
        recs = task(t)
        Z = embed(model, recs)
        idx = {id(r): i for i, r in enumerate(recs)}

        def fp(tr, te):
            m = make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000, class_weight="balanced"))
            m.fit(Z[[idx[id(r)] for r in tr]], labels(tr))
            return m.predict(Z[[idx[id(r)] for r in te]])

        y, pred = cv_predict(recs, fp)
        log_result(f"probe[{tag}]/logreg", "sequence", t, y, pred, notes="frozen SSL TF mean-pool embedding")


if __name__ == "__main__":
    main()
