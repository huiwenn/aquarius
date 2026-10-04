"""
R1: uncertainty for the headline comparisons of Part I.

For each comparison (model A vs model B on the same items and the same folds):
  - out-of-fold predictions are computed (cached in data/regionclf/oof/<name>.pkl)
  - 95% bootstrap CI of macro-F1 for each model (2000 resamples of test items)
  - paired permutation test of ΔmacroF1 = F1(A) − F1(B): for each of 10000 permutations, every item's two
    predictions are swapped with probability 1/2 (the exact null for "A and B are exchangeable")
  - pooled over fold seeds 0/1/2 when requested: items × seeds are resampled together
Results → data/regionclf/review_stats.csv and printed table.

Run (py312): OMP_NUM_THREADS=3 python src/regionclf/rev_stats.py
"""

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import A5_REGIONS, D, labels, load, task  # noqa: E402

OOF = D / "oof"


def oof(name, recs, fold_fn, seed=0):
    path = OOF / f"{name}_s{seed}.pkl"
    if path.exists():
        return pickle.load(open(path, "rb"))
    y = labels(recs)
    g = np.array([r["group"] for r in recs])
    pred = np.empty(len(recs), dtype=object)
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, g):
        pred[te] = fold_fn([recs[i] for i in tr], [recs[i] for i in te])
    OOF.mkdir(parents=True, exist_ok=True)
    pickle.dump((y, pred), open(path, "wb"))
    return y, pred


def mf1(y, p):
    return f1_score(y, p, average="macro")


def compare(label, runs_a, runs_b, n_boot=2000, n_perm=10000, seed=0):
    """runs_*: list of (y, pred) over seeds, same items in same order."""
    rng = np.random.RandomState(seed)
    ya = np.concatenate([r[0] for r in runs_a])
    pa = np.concatenate([r[1] for r in runs_a])
    pb = np.concatenate([r[1] for r in runs_b])
    fa, fb = mf1(ya, pa), mf1(ya, pb)
    n = len(ya)
    boots = []
    for _ in range(n_boot):
        i = rng.randint(0, n, n)
        boots.append((mf1(ya[i], pa[i]), mf1(ya[i], pb[i])))
    boots = np.array(boots)
    d_obs = fa - fb
    null = []
    for _ in range(n_perm):
        s = rng.rand(n) < 0.5
        qa, qb = np.where(s, pb, pa), np.where(s, pa, pb)
        null.append(mf1(ya, qa) - mf1(ya, qb))
    p = (np.sum(np.abs(null) >= abs(d_obs)) + 1) / (n_perm + 1)
    row = {"comparison": label, "F1_A": fa, "A_lo": np.percentile(boots[:, 0], 2.5),
           "A_hi": np.percentile(boots[:, 0], 97.5), "F1_B": fb, "B_lo": np.percentile(boots[:, 1], 2.5),
           "B_hi": np.percentile(boots[:, 1], 97.5), "delta": d_obs,
           "d_lo": np.percentile(boots[:, 0] - boots[:, 1], 2.5),
           "d_hi": np.percentile(boots[:, 0] - boots[:, 1], 97.5), "p_perm": p, "n_items": n}
    print(f"{label}: A {fa:.3f} [{row['A_lo']:.3f},{row['A_hi']:.3f}]  B {fb:.3f} [{row['B_lo']:.3f},"
          f"{row['B_hi']:.3f}]  Δ {d_obs:+.3f} [{row['d_lo']:+.3f},{row['d_hi']:+.3f}]  p={p:.4f}", flush=True)
    return row


def dual_fold(externals, level=2, use_scores=True):
    def fn(tr, te):
        classes = sorted(set(labels(tr)))
        tg = {r["group"] for r in te}
        ext = [r for e in externals for r in e if r["group"] not in tg and r["region"] in set(classes)] \
            if use_scores else []
        w = np.array([1.0] * len(tr) + [len(tr) / max(1, len(ext))] * len(ext))
        sk = F.fit_ngram(tr + ext, level=level, weights=w)
        sf = F.fit_ngram(tr)
        p = F.proba(sk, classes)([F.doc(r, level) for r in te]) + F.proba(sf, classes)([F.doc(r) for r in te])
        return np.array(classes)[p.argmax(1)]
    return fn


def naive_mix_fold(externals):
    def fn(tr, te):
        tg, regs = {r["group"] for r in te}, set(labels(tr))
        ext = [r for e in externals for r in e if r["group"] not in tg and r["region"] in regs]
        return F.fit_ngram(tr + ext).predict([F.doc(r) for r in te])
    return fn


def main() -> None:
    A, E = load("anthology"), load("essen")
    E5 = [r for r in E if r["region"] in A5_REGIONS]
    T15, T5 = task("T15"), task("T5")
    rows = []
    seeds = (0, 1, 2)

    run = lambda name, recs, fn: [oof(name, recs, fn, s) for s in seeds]  # noqa: E731
    ng15 = run("T15_ngram", T15, F.ngram_fold)
    dv15 = run("T15_dual_E", T15, dual_fold([E]))
    th15 = run("T15_theory", T15, F.theory_fold)
    rows.append(compare("T15: dual-view vs n-gram (3 seeds pooled)", dv15, ng15))
    rows.append(compare("T15: n-gram vs theory+GBM (3 seeds)", ng15, th15))
    mix15 = run("T15_naivemix_E", T15, naive_mix_fold([E]))
    rows.append(compare("T15: n-gram vs naive mix +Essen (3 seeds)", ng15, mix15))

    ng5 = run("T5_ngram", T5, F.ngram_fold)
    dv5 = run("T5_dual_AE", T5, dual_fold([A, E5]))
    mix5 = run("T5_naivemix_AE", T5, naive_mix_fold([A, E5]))
    rows.append(compare("T5: dual-view vs n-gram (3 seeds)", dv5, ng5))
    rows.append(compare("T5: n-gram vs naive mix +A+E5 (3 seeds)", ng5, mix5))

    A5 = task("A5")
    ngA = [oof("A5_ngram", A5, F.ngram_fold, 0)]
    thA = [oof("A5_theory", A5, F.theory_fold, 0)]
    rows.append(compare("A5: n-gram vs theory+GBM (seed 0)", ngA, thA, n_boot=500, n_perm=2000))

    # cleaner transcriptions: paired single-run vs ensemble (same items)
    s = {r["item_id"]: r for r in load("trans_game_pp")}
    e = {r["item_id"]: r for r in load("trans_game_ens3_pp")}
    ids = sorted(set(s) & set(e))
    rs, re_ = [s[i] for i in ids], [e[i] for i in ids]
    rows.append(compare("T15 n-gram: single-run vs 3-run ensemble transcriptions (3 seeds)",
                        run("T15single_ngram", rs, F.ngram_fold), run("T15ens3_ngram", re_, F.ngram_fold)))
    rows.append(compare("T15 dual-view: single-run vs ensemble (3 seeds)",
                        run("T15single_dual", rs, dual_fold([E])), run("T15ens3_dual", re_, dual_fold([E]))))

    pd.DataFrame(rows).round(4).to_csv(D / "review_stats.csv", index=False)


if __name__ == "__main__":
    main()
