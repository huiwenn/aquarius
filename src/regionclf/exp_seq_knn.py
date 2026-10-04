"""
Family "sequence": k-NN over melodic strings with edit distance (rapidfuzz, bit-parallel).

Each song → a string, one character per token of a vocabulary from exp_seq_tok (deg / degdur / intdur).
Distance = normalized Levenshtein or normalized Indel (= 1 − LCS-ratio). Prediction = distance-weighted vote of
the k nearest training songs, votes divided by the class prior (class-balanced). Songs are truncated to their
first MAXLEN tokens (the opening phrase(s); keeps transcription cost bounded).

Run (regionseq env): python src/regionclf/exp_seq_knn.py [--tasks A5,E,T15,T5]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Indel, Levenshtein
from rapidfuzz.process import cdist

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, task  # noqa: E402
from regionclf.exp_seq_tok import task_tokens  # noqa: E402

MAXLEN = 400


def strings(t, vocab, recs):
    toks = task_tokens(t, vocab, recs)
    alpha = {s: chr(0x4E00 + i) for i, s in enumerate(sorted({x for tt in toks for x in tt}))}
    return ["".join(alpha[x] for x in tt[:MAXLEN]) for tt in toks]


def run(t, vocab, metric, k):
    recs = task(t)
    S = strings(t, vocab, recs)
    idx = {id(r): i for i, r in enumerate(recs)}
    sc = {"lev": Levenshtein.normalized_distance, "indel": Indel.normalized_distance}[metric]

    def fp(tr, te):
        a = [S[idx[id(r)]] for r in tr]
        b = [S[idx[id(r)]] for r in te]
        ytr = labels(tr)
        cls, prior = np.unique(ytr, return_counts=True)
        D = cdist(b, a, scorer=sc, workers=4, dtype=np.float32)
        out = []
        for d in D:
            nn = np.argsort(d)[:k]
            w = 1.0 / (d[nn] + 1e-3)
            v = np.array([w[ytr[nn] == c].sum() for c in cls]) / prior
            out.append(cls[v.argmax()])
        return np.array(out)

    y, pred = cv_predict(recs, fp)
    log_result(f"knn[{vocab}|{metric}|k{k}]", "sequence", t, y, pred, notes=f"edit distance, maxlen {MAXLEN}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="T5,T15,E,A5")
    a = ap.parse_args()
    for t in a.tasks.split(","):
        for vocab in ["deg", "degdur"]:
            for metric in ["lev", "indel"]:
                run(t, vocab, metric, 10)
