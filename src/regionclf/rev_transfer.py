"""
R2: does score → performance transfer fail because of the *model* (Part I used theory+GBM) or because of the data?
Best representation (multi-viewpoint n-gram TF-IDF + LR, exp_fusion.fit_ngram) + standard, cheap domain adaptation.

Transfer pairs (training songs whose normalized title `group` occurs in the test set are always removed):
  A→T5     Anthology (5 regions)            → 200 transcriptions of the same 5 regions
  E→T14    Essen (14 regions)               → 560 transcriptions of Essen's 14 regions
  T5→A5    200 transcriptions               → Anthology

Experiments (--which):
  levels      reduction level L = 0..3 (reduce.py) applied to both sides, or only to the transcription side
  labelshift  (a) label-shift: A is imbalanced, T balanced. Balanced vs unweighted LR; posterior rescaling to a
              uniform prior; EM prior estimation (Saerens, Latinne & Decaestecker 2002); and, since T5 is known
              to be balanced, a transductive equal-count assignment (Hungarian on log-probabilities)
  coral       (b) CORAL (Sun, Feng & Saenko 2016) on theory features (LR, HGB) and on a 256-d SVD of the n-gram
              TF-IDF (SVD fitted on source ∪ unlabeled target), vs no alignment / per-domain z-scoring
  iw          (c) importance weighting: a domain classifier (source vs unlabeled target, cross-fitted) gives
              w = p(T|x)/p(S|x), clipped to [0.05, 20] and mean-normalized; the n-gram LR is refit with w
  augment     (d) score-side augmentation imitating transcription artifacts (augment()): neighbor-tone grace notes,
              chromatic pitch jitter and glide (passing) notes inside leaps, calibrated so that augmented Anthology
              matches T5's short-note share (11%), 偏音+chromatic mass (24%) and fourth share (0.06)
Every macro-F1 gets a 95% bootstrap CI over test items (1000 resamples). Rows go to results.csv
(family "review_transfer", CI in `notes`) and to data/regionclf/review_transfer.csv (CI as columns).

Run (py312):
  OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 VECLIB_MAXIMUM_THREADS=3 \
      python src/regionclf/rev_transfer.py --which levels,labelshift,coral,iw,augment
"""

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import A5_REGIONS, D, labels, load, log_result  # noqa: E402
from regionclf.features import estimate_gong, theory_features  # noqa: E402
from scipy.optimize import linear_sum_assignment  # noqa: E402
from sklearn.decomposition import TruncatedSVD  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import cross_val_predict  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

FAM = "review_transfer"
OUT = D / "review_transfer.csv"


# ----------------------------------------------------------------------------------------- statistics
def macro_f1_idx(y, p, k):
    cm = np.bincount(y * k + p, minlength=k * k).reshape(k, k)
    tp = np.diag(cm).astype(float)
    denom = cm.sum(0) + cm.sum(1)
    f1 = np.where(denom > 0, 2 * tp / np.maximum(denom, 1), 0.0)
    present = cm.sum(1) > 0
    return f1[present].mean()


def boot_ci(y, preds, n_boot=1000, seed=0):
    """y: true labels; preds: one prediction array or a list (e.g. over sampling seeds; the statistic is then
    the mean macro-F1 over seeds, and items are resampled jointly). Returns (point, lo, hi)."""
    preds = preds if isinstance(preds, list) else [preds]
    classes = sorted(set(y) | {c for p in preds for c in p})
    ix = {c: i for i, c in enumerate(classes)}
    k = len(classes)
    yi = np.array([ix[c] for c in y])
    pis = [np.array([ix[c] for c in p]) for p in preds]
    # sklearn's macro-F1 averages over labels present in y ∪ pred; match that on the full sample
    from sklearn.metrics import f1_score
    point = np.mean([f1_score(y, p, average="macro") for p in preds])
    rng = np.random.RandomState(seed)
    n = len(yi)
    bs = []
    for _ in range(n_boot):
        i = rng.randint(0, n, n)
        bs.append(np.mean([macro_f1_idx(yi[i], pi[i], k) for pi in pis]))
    return point, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def report(experiment, task_name, y, pred, notes="", **extra):
    """Log to results.csv (family review_transfer) with the CI in notes; mirror to review_transfer.csv."""
    y = np.asarray(y, dtype=object)
    preds = pred if isinstance(pred, list) else [pred]
    f1, lo, hi = boot_ci(y, [np.asarray(p, dtype=object) for p in preds])
    s = log_result(experiment, FAM, task_name, np.tile(y, len(preds)), np.concatenate(preds),
                   f"{notes} | macroF1 {f1:.3f} 95%CI [{lo:.3f},{hi:.3f}]".strip(" |"))
    row = {"time": dt.datetime.now().isoformat(timespec="seconds"), "experiment": experiment, "task": task_name,
           "n": len(y), "macro_f1": round(f1, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
           "bal_acc": round(s["bal_acc"], 4), "n_seeds": len(preds), "notes": notes,
           "extra": ";".join(f"{k}={v}" for k, v in extra.items())}  # fixed schema: extras in one column
    pd.DataFrame([row]).to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
    print(f"      CI [{lo:.3f},{hi:.3f}]", flush=True)
    return row


# ----------------------------------------------------------------------------------------- data
def pairs(which=("A→T5", "E→T14", "T5→A5")):
    A, E, T = load("anthology"), load("essen"), load("trans_primary")
    T5 = [r for r in T if r["region"] in A5_REGIONS]
    eregs = {r["region"] for r in E}
    T14 = [r for r in T if r["region"] in eregs]
    out = {"A→T5": (A, T5, "T5"), "E→T14": (E, T14, "T14"), "T5→A5": (T5, A, "A5"),
           "E5→T5": ([r for r in E if r["region"] in A5_REGIONS], T5, "T5")}
    res = {}
    for k in which:
        src, tgt, tn = out[k]
        tg = {r["group"] for r in tgt}
        res[k] = ([r for r in src if r["group"] not in tg], tgt, tn)
    return res


def is_trans(recs):
    return recs[0]["source"].startswith("trans")


# ----------------------------------------------------------------------------------------- (1) levels
def levels():
    for name, (src, tgt, tn) in pairs().items():
        fits = {}

        def fit(L):
            if L not in fits:
                fits[L] = F.fit_ngram(src, level=L)
            return fits[L]
        for L in range(4):
            report(f"ngram LR {name} reduce L{L} both sides", tn, labels(tgt),
                   fit(L).predict([F.doc(r, L) for r in tgt]), f"train {len(src)}", pair=name, level=L, mode="both")
            if L == 0:
                continue
            # reduce only the transcription side (the target for A→T5 / E→T14, the source for T5→A5)
            pred = (fit(0).predict([F.doc(r, L) for r in tgt]) if is_trans(tgt)
                    else fit(L).predict([F.doc(r, 0) for r in tgt]))
            report(f"ngram LR {name} reduce L{L} transcription side only", tn, labels(tgt), pred,
                   f"train {len(src)}", pair=name, level=L, mode="trans-only")


# ----------------------------------------------------------------------------------------- (a) label shift
def ngram_unweighted():
    m = F.ngram_model()
    m.steps[-1][1].set_params(class_weight=None)
    return m


def em_prior(P, prior_s, n_iter=200, tol=1e-8):
    """Saerens et al. 2002: re-estimate target priors and adjusted posteriors by EM."""
    pt = prior_s.copy()
    for _ in range(n_iter):
        Q = P * (pt / prior_s)
        Q /= Q.sum(1, keepdims=True)
        new = Q.mean(0)
        if np.abs(new - pt).max() < tol:
            break
        pt = new
    return Q, pt


def balanced_assign(P):
    """Transductive: every class gets ≈ n/K items (T is balanced by construction), max total log-probability."""
    n, k = P.shape
    cap = int(np.ceil(n / k))
    cost = -np.log(np.clip(np.repeat(P, cap, axis=1), 1e-12, None))
    r, c = linear_sum_assignment(cost)
    out = np.empty(n, dtype=int)
    out[r] = c // cap
    return out


def labelshift():
    for name, (src, tgt, tn) in pairs(("A→T5", "E→T14")).items():
        classes = sorted(set(labels(src)))
        y = labels(tgt)
        for L in (0, 2):
            for wname, mk in [("balanced", F.ngram_model), ("unweighted", ngram_unweighted)]:
                m = mk().fit([F.doc(r, L) for r in src], labels(src))
                P = F.proba(m, classes)([F.doc(r, L) for r in tgt])
                cnt = pd.Series(labels(src)).value_counts()
                prior_s = np.array([cnt[c] for c in classes], float)
                prior_s /= prior_s.sum()
                # effective training prior: class_weight='balanced' makes the fitted model's prior ≈ uniform
                eff = np.full(len(classes), 1 / len(classes)) if wname == "balanced" else prior_s
                C = np.array(classes)
                tag = f"{name} L{L} LR-{wname}"
                report(f"labelshift {tag} argmax", tn, y, C[P.argmax(1)], pair=name, level=L, method="argmax")
                Pu = P / eff
                report(f"labelshift {tag} uniform-prior rescale", tn, y, C[Pu.argmax(1)], pair=name, level=L,
                       method="uniform")
                Q, pt = em_prior(P, eff)
                report(f"labelshift {tag} EM prior (Saerens)", tn, y, C[Q.argmax(1)],
                       "EM target prior " + " ".join(f"{c[:2]}={v:.2f}" for c, v in zip(classes, pt)),
                       pair=name, level=L, method="EM")
                if name == "A→T5":  # T14 isn't exactly balanced over E's label set; assignment only for T5
                    report(f"labelshift {tag} balanced assignment (transductive)", tn, y, C[balanced_assign(P)],
                           pair=name, level=L, method="assign")
                print("  pred dist argmax:", pd.Series(C[P.argmax(1)]).value_counts().to_dict(), flush=True)


# ----------------------------------------------------------------------------------------- (b) CORAL
_th = {}


def theory(recs, L=0):
    out = []
    for r in recs:
        k = (r["source"], r["item_id"], L)
        if k not in _th:
            from regionclf.reduce import reduce
            _th[k] = theory_features(reduce(r["notes"], L) if L else r["notes"])
        out.append(_th[k])
    return np.nan_to_num(np.vstack(out))


def _msqrt(C, inv=False):
    w, V = np.linalg.eigh(C)
    w = np.clip(w, 1e-8, None)
    return (V * (w ** (-0.5 if inv else 0.5))) @ V.T


def coral(Xs, Xt, eps=1.0):
    """Sun et al. 2016 on per-domain standardized features: whiten source, recolor with target covariance."""
    Xs = StandardScaler().fit_transform(Xs)
    Xt = StandardScaler().fit_transform(Xt)
    Cs = np.cov(Xs, rowvar=False) + eps * np.eye(Xs.shape[1])
    Ct = np.cov(Xt, rowvar=False) + eps * np.eye(Xt.shape[1])
    return Xs @ _msqrt(Cs, inv=True) @ _msqrt(Ct), Xt


def align_variants(Xs, Xt):
    sc = StandardScaler().fit(Xs)
    yield "none (source scaler)", sc.transform(Xs), sc.transform(Xt)
    yield "per-domain z-score", StandardScaler().fit_transform(Xs), StandardScaler().fit_transform(Xt)
    yield "CORAL", *coral(Xs, Xt)


def lr_bal():
    return LogisticRegression(C=1.0, class_weight="balanced", max_iter=5000)


def svd_feats(src, tgt, L=0, dim=256):
    union = F.ngram_model().steps[0][1]
    Ms = union.fit_transform([F.doc(r, L) for r in src])
    Mt = union.transform([F.doc(r, L) for r in tgt])
    import scipy.sparse as sp
    svd = TruncatedSVD(dim, random_state=0).fit(sp.vstack([Ms, Mt]))
    return svd.transform(Ms), svd.transform(Mt)


def coral_exp():
    for name, (src, tgt, tn) in pairs(("A→T5", "E→T14", "T5→A5")).items():
        ys, y = labels(src), labels(tgt)
        for L in (0, 2):
            reps = [("theory", theory(src, L), theory(tgt, L))]
            reps.append(("ngram-SVD256", *svd_feats(src, tgt, L)))
            for rep, Xs0, Xt0 in reps:
                for al, Xs, Xt in align_variants(Xs0, Xt0):
                    clfs = [("LR", lr_bal())]
                    if rep == "theory":
                        clfs.append(("HGB", HistGradientBoostingClassifier(
                            max_iter=300, learning_rate=0.08, class_weight="balanced", random_state=0)))
                    for cn, clf in clfs:
                        pred = clf.fit(Xs, ys).predict(Xt)
                        report(f"coral {name} L{L} {rep}/{cn} align={al}", tn, y, pred, pair=name, level=L,
                               method=f"{rep}/{cn}/{al}")


# ----------------------------------------------------------------------------------------- (c) importance weighting
def iw():
    for name, (src, tgt, tn) in pairs(("A→T5", "E→T14")).items():
        for L in (0, 2):
            for rep in ("theory", "ngram-SVD256"):
                if rep == "theory":
                    Xs, Xt = theory(src, L), theory(tgt, L)
                else:
                    Xs, Xt = svd_feats(src, tgt, L)
                X = StandardScaler().fit_transform(np.vstack([Xs, Xt]))
                d = np.r_[np.zeros(len(Xs)), np.ones(len(Xt))]
                dc = LogisticRegression(C=0.1, class_weight="balanced", max_iter=5000)
                p = cross_val_predict(dc, X, d, cv=5, method="predict_proba")[:, 1]
                auc = roc_auc_score(d, p)
                ps = np.clip(p[: len(Xs)], 1e-6, 1 - 1e-6)
                w = np.clip(ps / (1 - ps), 0.05, 20)
                w /= w.mean()
                ess = w.sum() ** 2 / (w ** 2).sum()
                m = F.fit_ngram(src, level=L, weights=w)
                report(f"iw {name} L{L} domain-clf on {rep} → weighted ngram LR", tn, labels(tgt),
                       m.predict([F.doc(r, L) for r in tgt]),
                       f"domain AUC {auc:.3f}; ESS {ess:.0f}/{len(w)}", pair=name, level=L, method=f"iw/{rep}",
                       domain_auc=round(auc, 3), ess=round(ess))


# ----------------------------------------------------------------------------------------- (d) augmentation
STRENGTH = {"half": dict(pg=0.025, pj=0.11, ps=0.12), "matched": dict(pg=0.05, pj=0.22, ps=0.25),
            "strong": dict(pg=0.10, pj=0.33, ps=0.50)}


def augment(notes, rng, pg=0.10, pj=0.20, ps=0.40, orn=0.2):
    """Make a clean score look like a performance transcription.
      jitter  each note moves ±1 semitone with prob pj (→ 偏音 / chromatic degrees, intonation errors)
      glide   a leap of ≥3 semitones gets a short passing note (滑音) at the end of its first note with prob ps
              (splits fourths into steps: fewer fourths, more steps)
      grace   a short neighbor-tone note (倚音; ±1/±2 semitones, upper neighbor more likely) is inserted before a
              note with prob pg
    Short notes last `orn` × the median IOI (below reduce.py's 0.5 ornament threshold)."""
    n = notes.copy()
    ioi = np.diff(n[:, 0])
    med = np.median(ioi[ioi > 0]) if (ioi > 0).any() else 1.0
    sd = orn * med
    jit = rng.rand(len(n)) < pj
    n[jit, 2] += rng.choice([-1, 1], jit.sum())
    out = []
    for i in range(len(n)):
        on, du, p = n[i]
        if i > 0 and rng.rand() < pg and du > 2 * sd:  # grace note before this note
            g = p + rng.choice([2, 1, -1, -2], p=[0.4, 0.2, 0.2, 0.2])
            out.append([on, sd, g])
            on, du = on + sd, du - sd
        if i + 1 < len(n) and abs(n[i + 1, 2] - p) >= 3 and rng.rand() < ps and du > 2 * sd:
            nxt = n[i + 1, 2]
            mid = p + np.sign(nxt - p) * rng.randint(1, abs(nxt - p))
            out.append([on, du - sd, p])
            out.append([on + du - sd, sd, mid])
        else:
            out.append([on, du, p])
    return np.array(out, dtype=float)


def aug_recs(recs, strength, seed=0):
    rng = np.random.RandomState(seed)
    return [{**r, "source": f"{r['source']}_aug{strength}{seed}", "notes": augment(r["notes"], rng,
                                                                                 **STRENGTH[strength])}
            for r in recs]


def surface_stats(recs):
    rows = []
    for r in recs:
        n = r["notes"]
        p = n[:, 2].astype(int)
        rel = (p - estimate_gong(n)) % 12
        w = np.bincount(rel, weights=n[:, 1], minlength=12)
        w /= w.sum()
        ioi = np.diff(n[:, 0])
        med = np.median(ioi[ioi > 0])
        iv = np.diff(p)
        rows.append({"short": np.mean(ioi < 0.5 * med), "pianyin+chrom": w[[1, 3, 5, 6, 8, 10, 11]].sum(),
                     "fourth": np.mean(np.abs(iv) == 5), "step": np.mean((np.abs(iv) >= 1) & (np.abs(iv) <= 2)),
                     "n_degrees": (w >= 0.03).sum()})
    return pd.DataFrame(rows).mean().round(3)


def augment_exp():
    (src, tgt, tn), = pairs(("A→T5",)).values()
    y = labels(tgt)
    print("surface stats  A:", surface_stats(src).to_dict())
    print("surface stats T5:", surface_stats(tgt).to_dict())
    for s in STRENGTH:
        Aa = aug_recs(src, s)
        st = surface_stats(Aa).to_dict()
        print(f"surface stats A aug-{s}:", st, flush=True)
        for mix, train in [("aug only", Aa), ("A ∪ aug", src + Aa)]:
            m = F.fit_ngram(train)
            report(f"augment A({s}, {mix})→T5 ngram LR, test raw", tn, y, m.predict([F.doc(r) for r in tgt]),
                   "aug stats " + " ".join(f"{k}={v:.3f}" for k, v in st.items()), pair="A→T5", method=f"aug/{s}/{mix}")
            if mix == "aug only":
                m2 = F.fit_ngram(train, level=2)
                report(f"augment A({s}, {mix})→T5 ngram LR, both reduced L2", tn, y,
                       m2.predict([F.doc(r, 2) for r in tgt]), pair="A→T5", level=2, method=f"aug/{s}/{mix}/L2")
                h = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, class_weight="balanced",
                                                   random_state=0).fit(theory(train), labels(train))
                report(f"augment A({s}, {mix})→T5 theory HGB, test raw", tn, y, h.predict(theory(tgt)),
                       pair="A→T5", method=f"aug/{s}/{mix}/theoryHGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="levels,labelshift,coral,iw,augment")
    args = ap.parse_args()
    fns = {"levels": levels, "labelshift": labelshift, "coral": coral_exp, "iw": iw, "augment": augment_exp}
    for w in args.which.split(","):
        print(f"=== {w}", flush=True)
        fns[w]()


if __name__ == "__main__":
    main()
