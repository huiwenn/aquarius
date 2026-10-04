"""
R2 (few-shot): is the source (Anthology) data worth anything once some target transcriptions are labeled?

T5 song-grouped folds (common.folds, seed 0). In each fold, k labeled transcriptions per region are drawn from the
TRAINING fold only (k = 0, 2, 5, 10, 20, all ≈ 32; nested draws: the k shots are the first k of a per-region random
permutation; 3 draws for k ∈ {2, 5, 10, 20}, 1 for k = 0 / all). Anthology songs whose title occurs in the test fold
are removed. All models = multi-viewpoint n-gram TF-IDF + LR (exp_fusion.fit_ngram).
  target-only      n-gram LR on the k shots
  A only           n-gram LR on Anthology (k = 0 reference; identical for every k)
  A+shots naive    Anthology ∪ shots, unweighted
  A+shots upweight Anthology ∪ shots, sources re-weighted to equal total mass
  dual-view        surface = target-only; skeleton = L2-reduced Anthology ∪ L2-reduced shots (equal mass);
                   prediction = mean of the two views' probabilities (exp_fusion.dual with Anthology as the only
                   external source)
  late A⊕target    mean of A-only (L2 both sides) and target-only probabilities (no joint training)
Macro-F1 = mean over draws, 95% CI from 1000 bootstrap resamples of test items (draws resampled jointly).
OOF predictions are cached in data/regionclf/oof/fewshot_*.pkl so the run can resume.

Run (py312): OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 VECLIB_MAXIMUM_THREADS=3 python src/regionclf/rev_transfer_fewshot.py
"""

import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import A5_REGIONS, D, folds, labels, load, task  # noqa: E402
from regionclf.rev_transfer import report  # noqa: E402

KS = [0, 2, 5, 10, 20, "all"]
CACHE = D / "oof"
METHODS = ["target-only", "A only", "A+shots naive", "A+shots upweight", "dual-view", "late A⊕target"]


def shots_for(train, k, seed, fold):
    if k == "all":
        return list(train)
    out = []
    for reg in A5_REGIONS:
        rs = [r for r in train if r["region"] == reg]
        perm = np.random.RandomState(1000 * seed + 17 * fold + A5_REGIONS.index(reg)).permutation(len(rs))
        out += [rs[i] for i in perm[:k]]
    return out


def run():
    T5, A = task("T5"), load("anthology")
    classes = sorted(A5_REGIONS)
    C = np.array(classes)
    n = len(T5)
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "fewshot_T5.pkl"
    store = pickle.load(open(path, "rb")) if path.exists() else {}
    for f, (tr, te) in enumerate(folds(T5)):
        train, test = [T5[i] for i in tr], [T5[i] for i in te]
        tg = {r["group"] for r in test}
        src = [r for r in A if r["group"] not in tg]
        d0, d2 = [F.doc(r) for r in test], [F.doc(r, 2) for r in test]
        a0 = a2 = None
        for k in KS:
            seeds = [0, 1, 2] if k not in (0, "all") else [0]
            for s in seeds:
                key = (f, k, s)
                if key in store:
                    continue
                if a0 is None:
                    a0 = F.proba(F.fit_ngram(src), classes)(d0)
                    a2 = F.proba(F.fit_ngram(src, level=2), classes)(d2)
                res = {"A only": C[a0.argmax(1)]}
                if k != 0:
                    sh = shots_for(train, k, s, f)
                    pt = F.proba(F.fit_ngram(sh), classes)(d0)
                    res["target-only"] = C[pt.argmax(1)]
                    res["late A⊕target"] = C[(pt + a2).argmax(1)]
                    res["A+shots naive"] = F.fit_ngram(src + sh).predict(d0)
                    w = np.r_[np.full(len(src), len(sh) / len(src)), np.ones(len(sh))]
                    res["A+shots upweight"] = F.fit_ngram(src + sh, weights=w).predict(d0)
                    psk = F.proba(F.fit_ngram(src + sh, level=2, weights=w), classes)(d2)
                    res["dual-view"] = C[(psk + pt).argmax(1)]
                store[key] = (te, res)
                pickle.dump(store, open(path, "wb"))
                print(f"fold {f} k={k} seed {s} done ({len(src)} A scores)", flush=True)
    y = labels(T5)
    for k in KS:
        seeds = [0, 1, 2] if k not in (0, "all") else [0]
        for m in METHODS:
            preds = []
            for s in seeds:
                p = np.empty(n, dtype=object)
                ok = True
                for f in range(5):
                    te, res = store[(f, k, s)]
                    if m not in res:
                        ok = False
                        break
                    p[te] = res[m]
                if ok:
                    preds.append(p)
            if preds:
                report(f"fewshot T5 k={k}/region {m}", "T5", y, preds,
                       f"{len(preds)} draw(s); shots from the training fold only", k=str(k), method=m)


if __name__ == "__main__":
    run()
