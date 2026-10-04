"""
R2 follow-up: the score-trained model *ranks* transcriptions better than its argmax suggests — the class decision
threshold is shifted (almost every transcription is predicted 东北部平原). Transductive bias corrections that use only
UNLABELED target statistics, combined with the reduction levels from rev_transfer.levels:

  argmax       plain prediction
  centering    subtract, per class, the mean log-probability over the unlabeled target set (assumes the target
               is roughly class-balanced; equivalent to re-estimating class biases on target)
  assign       equal-count assignment (Hungarian on log-probabilities; T5 and T14 are exactly balanced, 40/region)
  EM           Saerens et al. 2002 prior re-estimation (does not assume balance)
  oracle-prior (T5→A5 only) rescale by the known A class proportions — an upper bound for prior correction

Pairs: A→T5, E→T14 (model trained raw, target reduced L0–L3; and both sides L3), T5→A5.
Run (py312): OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 VECLIB_MAXIMUM_THREADS=3 python src/regionclf/rev_transfer_bias.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import labels  # noqa: E402
from regionclf.rev_transfer import balanced_assign, em_prior, pairs, report  # noqa: E402


def decide(P, how, prior=None):
    if how == "argmax":
        return P.argmax(1)
    if how == "centering":
        lp = np.log(np.clip(P, 1e-12, None))
        return (lp - lp.mean(0)).argmax(1)
    if how == "assign":
        return balanced_assign(P)
    if how == "EM":
        return em_prior(P, np.full(P.shape[1], 1 / P.shape[1]))[0].argmax(1)
    if how == "oracle-prior":
        return (P * prior).argmax(1)
    raise ValueError(how)


def main():
    for name, (src, tgt, tn) in pairs(("A→T5", "E→T14", "T5→A5")).items():
        classes = sorted(set(labels(src)))
        C, y = np.array(classes), labels(tgt)
        fits = {}
        settings = [(0, L) for L in range(4)] + [(3, 3)] if name != "T5→A5" else [(0, 0), (3, 3), (3, 0)]
        for Ls, Lt in settings:
            if Ls not in fits:
                fits[Ls] = F.fit_ngram(src, level=Ls)
            P = F.proba(fits[Ls], classes)([F.doc(r, Lt) for r in tgt])
            hows = ["argmax", "centering", "EM"]
            if name == "T5→A5":
                cnt = pd.Series(y).value_counts()
                prior = np.array([cnt.get(c, 0) for c in classes], float)
                prior /= prior.sum()
                hows.append("oracle-prior")
            else:
                prior = None
                hows.append("assign")
            for h in hows:
                report(f"bias {name} train L{Ls} test L{Lt} {h}", tn, y, C[decide(P, h, prior)],
                       pair=name, level=f"{Ls}/{Lt}", method=h)
            print("   argmax dist:", pd.Series(C[P.argmax(1)]).value_counts().to_dict(), flush=True)


if __name__ == "__main__":
    main()
