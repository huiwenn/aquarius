"""
R4: same-song paired evidence. Do transcriptions keep the melodic identity that the scores classify on?

Pairs: the 62 recordings whose normalized title matches an Anthology score in a region-consistent province volume
(matching logic and REGION_VOLUMES from src/transcription/audit/score_reference.py; a recording can match several
same-title scores, e.g. 小拜年（一）/（二）).

(a) Song-identity retrieval. For every such transcription, rank ALL Anthology scores of the volumes of its region
    (pool 1.8k–2.7k scores) by
      melodic   melodic_agreement(perf_skeleton, score_skeleton, local_a=True).acc  (audit/melody.py: transposition-
                invariant, ornament-tolerant semi-global alignment; numba port of `align`, checked identical)
      melodic-cohort  the same, minus the score's mean agreement with all other queries of the region (the raw
                acc = matches / len(score) favours short scores; this cohort normalization removes that bias)
      ngram-L0 / ngram-L2  cosine of the multi-viewpoint n-gram TF-IDF (vectorizers fitted on Anthology), with the
                transcription raw or reduced to L2 (reduce.py)
    Reported: recall@1/5/10 of any same-title score, median rank of the best-ranked same-title score, and the exact
    chance values for a random ranking with the same pool and number of same-title scores.
(b) Paired region predictions. n-gram LR trained on Anthology *minus every matched title* predicts the region of the
    transcription (raw and L2) and of its best-aligned same-title score; label = the score's region.
    Reported: macro-F1 / accuracy with bootstrap CIs, agreement of the two predictions and Cohen's kappa.
(c) --bias: (b) again at L0 with target logit centering (rev_transfer_bias): class biases are re-estimated from the
    unlabeled log-probabilities of all 600 transcriptions (for transcription predictions) and of all Anthology scores
    (for score predictions), to separate the domain-wide bias from song-level agreement.
Outputs: data/regionclf/review_pairs_retrieval.csv, review_pairs_predictions.csv; results.csv family review_transfer.

Run (py312): OMP_NUM_THREADS=3 MKL_NUM_THREADS=3 python src/regionclf/rev_transfer_pairs.py [--bias]
"""

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "transcription" / "audit"))
from melody import best_shift, melodic_agreement, skeleton  # noqa: E402
from score_reference import REGION_VOLUMES, norm, title  # noqa: E402
from scipy.special import comb  # noqa: E402
from sklearn.metrics import cohen_kappa_score  # noqa: E402

from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import D, labels, load  # noqa: E402
from regionclf.rev_transfer import boot_ci, report  # noqa: E402


@numba.njit(cache=True)
def _align(a, b, local_a):
    n, m = len(a), len(b)
    Dm = np.zeros((n + 1, m + 1))
    for i in range(n + 1):
        Dm[i, 0] = 0.0 if local_a else i
    for j in range(m + 1):
        Dm[0, j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = min(abs(a[i - 1] - b[j - 1]), 2) / 2.0
            Dm[i, j] = min(Dm[i - 1, j] + 1, Dm[i, j - 1] + 1, Dm[i - 1, j - 1] + sub)
    if local_a:
        i = int(np.argmin(Dm[:, m]))
    else:
        i = n
    j, match, pairs = m, 0, 0
    while i > 0 and j > 0:
        sub = min(abs(a[i - 1] - b[j - 1]), 2) / 2.0
        if Dm[i, j] == Dm[i - 1, j - 1] + sub:
            pairs += 1
            if a[i - 1] == b[j - 1]:
                match += 1
            i, j = i - 1, j - 1
        elif Dm[i, j] == Dm[i - 1, j] + 1:
            i -= 1
        else:
            j -= 1
    return match, pairs


def agreement(a, b, max_len=400):
    """Same as melody.melodic_agreement(a, b, local_a=True)['acc'], numba-accelerated."""
    if len(a) < 4 or len(b) < 4:
        return np.nan
    a, b = a[:max_len], b[:max_len]
    s = best_shift(a, b)
    match, _ = _align(a.astype(np.int64), (b + s).astype(np.int64), True)
    return match / len(b)


def perf_skel(r):
    n = r["notes"]
    return skeleton([(o, o + d, int(p)) for o, d, p in n], min_dur=0.08)


def score_skel(r):
    n = r["notes"]  # beats → seconds at a nominal 120 bpm, as the score MIDIs; drop grace notes < 0.06 s
    return skeleton([(0.5 * o, 0.5 * (o + d), int(p)) for o, d, p in n], min_dur=0.06)


def matched_pairs():
    A, T = load("anthology"), load("trans_primary")
    by_title = {}
    for r in A:
        by_title.setdefault(norm(title(Path(r["item_id"]))), []).append(r)
    out = []
    for t in T:
        vols = REGION_VOLUMES.get(t["region"])
        if not vols:
            continue
        c = [a for a in by_title.get(norm(t["title"]), []) if a["item_id"].split("/")[0] in vols]
        if c:
            pool = [a for a in A if a["item_id"].split("/")[0] in vols]
            out.append((t, c, pool))
    return A, out


def chance_recall(N, c, k):
    return 1 - comb(N - c, k, exact=True) / comb(N, k, exact=True)


def chance_median_rank(N, c):
    """Median of the minimum rank of c true items among N randomly ordered."""
    ks = np.arange(1, N + 1)
    cdf = np.array([chance_recall(N, c, k) for k in ks])
    return int(ks[np.searchsorted(cdf, 0.5)])


def retrieval(A, P):
    # sanity: numba agreement == melody.melodic_agreement
    t, c, _ = P[0]
    a, b = perf_skel(t), score_skel(c[0])
    ref = melodic_agreement(a, b, local_a=True)["acc"]
    assert abs(agreement(a, b) - ref) < 1e-12, (agreement(a, b), ref)

    union = F.ngram_model().steps[0][1].fit([F.doc(r) for r in A])
    aid = {r["item_id"]: i for i, r in enumerate(A)}
    MA = union.transform([F.doc(r) for r in A])
    sk_cache = {}

    def ssk(r):
        if r["item_id"] not in sk_cache:
            sk_cache[r["item_id"]] = score_skel(r)
        return sk_cache[r["item_id"]]

    # melodic agreement matrix per region (all queries of the region × its pool) for cohort normalization
    rows, sims = [], {}
    for qi, (t, c, pool) in enumerate(P):
        a = perf_skel(t)
        sims.setdefault(t["region"], {})[qi] = np.array([agreement(a, ssk(r)) for r in pool])
        if qi % 10 == 0:
            print(f"  melodic {qi}/{len(P)}", flush=True)
    cohort = {reg: np.nanmean(np.vstack(list(d.values())), 0) for reg, d in sims.items()}

    for qi, (t, c, pool) in enumerate(P):
        true = np.array([r["item_id"] in {x["item_id"] for x in c} for r in pool])
        idx = [aid[r["item_id"]] for r in pool]
        mel = np.nan_to_num(sims[t["region"]][qi], nan=-1)
        methods = {"melodic": mel, "melodic-cohort": mel - np.nan_to_num(cohort[t["region"]])}
        # the query's own contribution to the cohort mean is 1/n_queries of it — negligible but removed
        nq = len(sims[t["region"]])
        if nq > 1:
            methods["melodic-cohort"] = mel - (np.nan_to_num(cohort[t["region"]]) * nq - mel) / (nq - 1)
        for L in (0, 2):
            q = union.transform([F.doc(t, L)])
            cos = (MA[idx] @ q.T).toarray().ravel() / (np.sqrt(MA[idx].multiply(MA[idx]).sum(1)).A.ravel()
                                                      * np.sqrt(q.multiply(q).sum()) + 1e-12)
            methods[f"ngram-L{L}"] = cos
        for mname, s in methods.items():
            order = np.argsort(-s, kind="stable")
            rank = int(np.where(true[order])[0].min()) + 1
            rows.append({"video_id": t["item_id"], "song": t["title"], "region": t["region"], "method": mname,
                         "pool": len(pool), "n_true": int(true.sum()), "rank": rank,
                         "true_sim": float(s[true].max()), "pool_median_sim": float(np.median(s))})
    d = pd.DataFrame(rows)
    d.to_csv(D / "review_pairs_retrieval.csv", index=False)
    q = d[d.method == "melodic"]
    ch = {f"R@{k}": np.mean([chance_recall(N, c, k) for N, c in zip(q["pool"], q["n_true"])]) for k in (1, 5, 10)}
    ch["median_rank"] = np.median([chance_median_rank(N, c) for N, c in zip(q["pool"], q["n_true"])])
    summ = []
    rng = np.random.RandomState(0)
    for mname, g in d.groupby("method", sort=False):
        r = g["rank"].to_numpy()
        row = {"method": mname, "n": len(g), "median_rank": np.median(r)}
        for k in (1, 5, 10):
            bs = [np.mean(r[rng.randint(0, len(r), len(r))] <= k) for _ in range(1000)]
            row[f"R@{k}"] = np.mean(r <= k)
            row[f"R@{k}_ci"] = f"[{np.percentile(bs, 2.5):.2f},{np.percentile(bs, 97.5):.2f}]"
        bs = [np.median(r[rng.randint(0, len(r), len(r))]) for _ in range(1000)]
        row["median_rank_ci"] = f"[{np.percentile(bs, 2.5):.0f},{np.percentile(bs, 97.5):.0f}]"
        row["mean_pool"] = g["pool"].mean()
        summ.append(row)
    summ.append({"method": "chance", "n": len(q), **ch, "mean_pool": q["pool"].mean()})
    s = pd.DataFrame(summ)
    s.to_csv(D / "review_pairs_retrieval_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.round(3).to_string(), flush=True)
    return d


def predictions(A, P, retr):
    matched_groups = {t["group"] for t, _, _ in P} | {a["group"] for _, c, _ in P for a in c}
    train = [r for r in A if r["group"] not in matched_groups]
    print(f"  training on {len(train)} Anthology scores (all matched titles removed)", flush=True)
    # best-aligned same-title score per recording (by melodic agreement)
    best = []
    for t, c, _ in P:
        a = perf_skel(t)
        best.append(c[int(np.nanargmax([np.nan_to_num(agreement(a, score_skel(x)), nan=-1) for x in c]))])
    y = np.array([b["region"] for b in best], dtype=object)
    rows = {}
    for L in (0, 2):
        m = F.fit_ngram(train, level=L)
        rows[f"score L{L}"] = m.predict([F.doc(b, L) for b in best])
        rows[f"trans L{L}"] = m.predict([F.doc(t, L) for t, _, _ in P])
    for k, p in rows.items():
        report(f"paired same-song: A-trained ngram LR on the {k.split()[0]} ({k.split()[1]} both sides)",
               "pairs62", y, p, "62 recordings with a same-title region-consistent Anthology score; "
               "label = the score's region; matched titles removed from training", method=k)
    out = pd.DataFrame({"video_id": [t["item_id"] for t, _, _ in P], "song": [t["title"] for t, _, _ in P],
                        "trans_region": [t["region"] for t, _, _ in P], "score": [b["item_id"] for b in best],
                        "label": y, **rows})
    out.to_csv(D / "review_pairs_predictions.csv", index=False)
    for L in (0, 2):
        a, b = rows[f"score L{L}"], rows[f"trans L{L}"]
        acc_s, acc_t = np.mean(a == y), np.mean(b == y)
        agree = np.mean(a == b)
        # agreement expected by chance from the two marginal prediction distributions
        cls = sorted(set(a) | set(b))
        exp = sum(np.mean(a == c) * np.mean(b == c) for c in cls)
        rng = np.random.RandomState(0)
        bs = [np.mean(a[i] == b[i]) for i in (rng.randint(0, len(a), len(a)) for _ in range(1000))]
        both = np.mean((a == y) & (b == y))
        print(f"L{L}: acc score {acc_s:.3f}  acc trans {acc_t:.3f}  both-correct {both:.3f}  "
              f"agreement {agree:.3f} [{np.percentile(bs, 2.5):.2f},{np.percentile(bs, 97.5):.2f}] "
              f"(chance {exp:.3f}), kappa {cohen_kappa_score(a, b):.3f}; "
              f"P(trans correct | score correct) {np.mean(b[a == y] == y[a == y]):.3f}", flush=True)
    # does retrieval success predict classification success?
    mr = retr[retr.method == "melodic-cohort"].set_index("video_id")["rank"]
    out["rank"] = out.video_id.map(mr)
    for L in (0, 2):
        ok = out[f"trans L{L}"] == out.label
        print(f"L{L}: median melodic-cohort rank when trans correct {out['rank'][ok].median()} vs wrong "
              f"{out['rank'][~ok].median()}", flush=True)
    t5 = out.trans_region == out.label
    print("per-recording (T5-region subset n=%d):" % t5.sum())
    for k in rows:
        f1 = boot_ci(out.label[t5].to_numpy(), out[k][t5].to_numpy())
        print(f"   {k}: macroF1 {f1[0]:.3f} [{f1[1]:.3f},{f1[2]:.3f}]")


def bias_corrected(A, P):
    matched_groups = {t["group"] for t, _, _ in P} | {a["group"] for _, c, _ in P for a in c}
    train = [r for r in A if r["group"] not in matched_groups]
    pred = pd.read_csv(D / "review_pairs_predictions.csv")
    best = {r["item_id"]: r for r in A}
    classes = sorted(set(labels(train)))
    C = np.array(classes)
    m = F.fit_ngram(train)
    pr = F.proba(m, classes)
    T = load("trans_primary")
    lt = np.log(np.clip(pr([F.doc(r) for r in T]), 1e-12, None))
    la = np.log(np.clip(pr([F.doc(r) for r in train]), 1e-12, None))
    qt = np.log(np.clip(pr([F.doc(t) for t, _, _ in P]), 1e-12, None)) - lt.mean(0)
    qs = np.log(np.clip(pr([F.doc(best[i]) for i in pred.score]), 1e-12, None)) - la.mean(0)
    y = pred.label.to_numpy(dtype=object)
    a, b = C[qs.argmax(1)], C[qt.argmax(1)]
    report("paired same-song: score, logit-centered (L0)", "pairs62", y, a, "centering stats from A train", method="c-s")
    report("paired same-song: trans, logit-centered (L0)", "pairs62", y, b, "centering stats from all 600 trans",
           method="c-t")
    cls = sorted(set(a) | set(b))
    print(f"centered: acc score {np.mean(a == y):.3f} trans {np.mean(b == y):.3f} agreement {np.mean(a == b):.3f} "
          f"(chance {sum(np.mean(a == c) * np.mean(b == c) for c in cls):.3f}) kappa {cohen_kappa_score(a, b):.3f}; "
          f"P(trans correct | score correct) {np.mean(b[a == y] == y[a == y]):.3f}")
    print("trans pred dist:", pd.Series(b).value_counts().to_dict(), " labels:", pd.Series(y).value_counts().to_dict())


def main() -> None:
    A, P = matched_pairs()
    if "--bias" in sys.argv:
        return bias_corrected(A, P)
    print(f"{len(P)} recordings with region-consistent same-title Anthology scores", flush=True)
    retr = retrieval(A, P)
    predictions(A, P, retr)


if __name__ == "__main__":
    main()
