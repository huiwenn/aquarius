"""
Official transcription numbers under the strict protocol (common.folds default for transcriptions):
folds grouped by channel, and training folds drop test-fold songs → no shared channel, no shared song.
Models use musical features only (notes); channel / metadata are never inputs.

Models: theory+GBM, multi-viewpoint n-gram LR, dual-view (n-gram surface ⊕ skeleton + Essen scores).
Seeds 0/1/2 pooled; 95% bootstrap CI over items×seeds; paired permutation test dual-view vs n-gram.
Results → results.csv (family "protocol") and data/regionclf/review_protocol.csv

Run (py312): OMP_NUM_THREADS=4 python src/regionclf/rev_protocol.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import A5_REGIONS, D, folds, labels, load, log_result, task  # noqa: E402
from regionclf.rev_stats import compare, dual_fold  # noqa: E402


def oof(recs, fn, seed):
    y = labels(recs)
    pred = np.empty(len(recs), dtype=object)
    for tr, te in folds(recs, seed=seed):  # default = channel+song for transcriptions
        pred[te] = fn([recs[i] for i in tr], [recs[i] for i in te])
    return y, pred


def main() -> None:
    E, A = load("essen"), load("anthology")
    rows = []
    for tname, ext in [("T15", [E]), ("T5", [A, [r for r in E if r["region"] in A5_REGIONS]])]:
        recs = task(tname)
        runs = {}
        for mname, fn in [("theory+GBM", F.theory_fold), ("n-gram LR", F.ngram_fold),
                          ("dual-view", dual_fold(ext))]:
            runs[mname] = [oof(recs, fn, s) for s in (0, 1, 2)]
            y = np.concatenate([r[0] for r in runs[mname]])
            p = np.concatenate([r[1] for r in runs[mname]])
            s = log_result(f"{mname} [channel+song folds, 3 seeds pooled]", "protocol", tname, y, p,
                           "musical features only; no shared channel or song between train/test")
            rows.append({"task": tname, "model": mname, **s})
        c = compare(f"{tname} strict protocol: dual-view vs n-gram", runs["dual-view"], runs["n-gram LR"],
                    n_boot=2000, n_perm=5000)
        rows.append({"task": tname, "model": "Δ dual-view − n-gram", **c})
        c = compare(f"{tname} strict protocol: n-gram vs theory", runs["n-gram LR"], runs["theory+GBM"],
                    n_boot=2000, n_perm=5000)
        rows.append({"task": tname, "model": "Δ n-gram − theory", **c})
        pd.DataFrame(rows).round(4).to_csv(D / "review_protocol.csv", index=False)


if __name__ == "__main__":
    main()
