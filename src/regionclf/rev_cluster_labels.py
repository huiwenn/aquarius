"""
Reviewer R8, parts 3–4: is the 色彩区 partition of provinces more *learnable* than alternative label sets built
from the same provinces — above all, than random partitions of the same provinces into groups of the same sizes?

Sources with province labels:
  A  anthology: 9 provinces (11 volumes) → 5 色彩区, block sizes 3/2/2/1/1 → 3,780 distinct same-size partitions
  E  essen: the 20 Han provinces with ≥ 20 songs → 10 色彩区 (sizes 4/3/2/2/2/2/2/1/1/1). Shanxi (912 songs, 802 of
     them one sub-collection) is capped at 150 songs (seed 0) so one province doesn't dominate every grouping.

Model / protocol: the exp_fusion multi-viewpoint n-gram TF-IDF + LR (C=10, balanced), 5-fold StratifiedGroupKFold
(seed 0) grouped by song title and stratified by *province*, so every label set is evaluated on identical folds.
TF-IDF is refitted on each training fold (it is label-free, so it is shared by all label sets of that fold).
Label sets:
  secaiqu      the 色彩区
  province     provinces (and `volume` for A: 11 editorial volumes)
  NS-lit       literature north (东北, 西北, 江淮) vs south, coarsened from the 色彩区
  NS-lat       Qinling–Huai line (province centre ≥ 33.5°N) — geography-only 2-way split
  NSC-lat      3-way North (≥ 35°N) / Central / South (< 28°N)
  geo-k        k-means (k = #色彩区, 2, 3) on province coordinates
  geo-opt      the same-size partition (as 色彩区) minimizing within-group geographic distance
  randpart#i   random same-size partitions of the provinces (--n-rand, default 30 for A, 30 for E)
  randNS#i     random same-size 2-way partitions (null for NS-lat), 10 each
Metrics: macro-F1, Cohen's kappa, and chance-normalized macro-F1 (F1 − 1/K)/(1 − 1/K) (stratified-random macro-F1
= 1/K). All runs are logged with log_result(family="review_labels").

Post-hoc (cheap, exhaustive): the out-of-fold *province* predictions are mapped through every same-size partition
(A: all 3,780; E: 5,000 random) → rank of the 色彩区 grouping by kappa of the mapped predictions.
Part 4: in the province classifier, share of errors that stay inside the true province's 色彩区, vs the same share
under random same-size partitions (permutation p). For A also the volume classifier: within-province and within-
色彩区 error shares.

Outputs: data/regionclf/review/labels_<src>.csv (per label set), labels_posthoc_<src>.csv, labels_confusion_<src>.csv,
         notebooks/figures/regionclf_labels_null_<src>.png
Run (py312):
  OMP_NUM_THREADS=3 PYTHONPATH=src python src/regionclf/rev_cluster_labels.py --sources A,E [--n-rand 30]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import D, ROOT, load, log_result  # noqa: E402
from regionclf.exp_fusion import doc  # noqa: E402
from regionclf.rev_cluster import (OUT, PROVINCE_LATLON, VOCABS, all_partitions, province_set,  # noqa: E402
                                   random_partitions)
from scipy import sparse  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import cohen_kappa_score, confusion_matrix, f1_score  # noqa: E402
from sklearn.model_selection import StratifiedGroupKFold  # noqa: E402

FIG = ROOT / "notebooks" / "figures"
NORTH_LIT = {"东北部平原", "西北部高原", "江淮"}


def records(src):
    if src == "A":
        return load("anthology")
    recs = load("essen")
    p2g = province_set("essen", recs)
    recs = [r for r in recs if r.get("province") in p2g]
    rng = np.random.RandomState(0)
    sx = [i for i, r in enumerate(recs) if r["province"] == "Shanxi"]
    drop = set(rng.choice(sx, len(sx) - 150, replace=False)) if len(sx) > 150 else set()
    return [r for i, r in enumerate(recs) if i not in drop]


def xy(p):
    lat, lon = PROVINCE_LATLON[p]
    return np.array([lat * 111.0, lon * 111.0 * np.cos(np.radians(lat))])


def label_sets(src, recs, n_rand, seed=0):
    p2g = {p: g for p, g in province_set("anthology" if src == "A" else "essen").items()
           if p in {r["province"] for r in recs}}
    provs = list(p2g)
    K = len(set(p2g.values()))
    sets = {"secaiqu": dict(p2g), "province": {p: p for p in provs}}
    sets["NS-lit"] = {p: "N" if g in NORTH_LIT else "S" for p, g in p2g.items()}
    sets["NS-lat"] = {p: "N" if PROVINCE_LATLON[p][0] >= 33.5 else "S" for p in provs}
    sets["NSC-lat"] = {p: "N" if PROVINCE_LATLON[p][0] >= 35 else ("S" if PROVINCE_LATLON[p][0] < 28 else "C")
                       for p in provs}
    P = np.vstack([xy(p) for p in provs])
    for k in sorted({K, 2, 3}):
        km = KMeans(k, n_init=50, random_state=seed).fit_predict(P)
        sets[f"geo-k{k}"] = {p: f"g{c}" for p, c in zip(provs, km)}
    # geography-optimal partition with the 色彩区's block sizes (A: exhaustive; E: swap hill-climbing, 200 starts)
    def within(m):
        return sum(np.linalg.norm(xy(a) - xy(b)) for a in provs for b in provs if a < b and m[a] == m[b])
    if src == "A":
        best = min(all_partitions(p2g), key=within)
    else:
        best, bw = None, np.inf
        for m in random_partitions(p2g, 200, seed=11, exclude_true=False):
            w, improved = within(m), True
            while improved:
                improved = False
                for a in provs:
                    for b in provs:
                        if m[a] != m[b]:
                            m2 = dict(m)
                            m2[a], m2[b] = m[b], m[a]
                            w2 = within(m2)
                            if w2 < w - 1e-9:
                                m, w, improved = m2, w2, True
            if w < bw:
                best, bw = m, w
    sets["geo-opt"] = best

    def canon(m):
        inv = {}
        for p, g in m.items():
            inv.setdefault(g, set()).add(p)
        return frozenset(frozenset(v) for v in inv.values())
    for k in [k for k in sets if k != "secaiqu" and canon(sets[k]) == canon(sets["secaiqu"])]:
        print(f"[{src}] label set {k} is identical to the 色彩区 partition — dropped", flush=True)
        del sets[k]
    for i, rp in enumerate(random_partitions(p2g, n_rand, seed=seed)):
        sets[f"randpart#{i}"] = rp
    for i, rp in enumerate(random_partitions(sets["NS-lat"], 10, seed=seed + 1)):
        sets[f"randNS#{i}"] = rp
    return p2g, sets


def make_folds(recs, seed=0):
    y = np.array([r["province"] for r in recs])
    g = np.array([r["group"] for r in recs])
    return list(StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(np.zeros(len(y)), y, g))


def fold_matrices(train_docs, test_docs):
    tr, te = [], []
    for i in range(len(VOCABS)):
        v = TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 4), sublinear_tf=True,
                            min_df=2, max_features=200_000)
        tr.append(v.fit_transform([d[i] for d in train_docs]))
        te.append(v.transform([d[i] for d in test_docs]))
    return sparse.hstack(tr).tocsr(), sparse.hstack(te).tocsr()


def metrics(y, pred):
    K = len(set(y))
    f1 = f1_score(y, pred, average="macro")
    return {"K": K, "macro_f1": f1, "kappa": cohen_kappa_score(y, pred), "f1_norm": (f1 - 1 / K) / (1 - 1 / K)}


def learnability(src, recs, sets, extra_sets=None):
    prov = np.array([r["province"] for r in recs])
    docs = [doc(r) for r in recs]
    extra_sets = extra_sets or {}
    names = list(sets) + list(extra_sets)
    Y = {n: np.array([sets[n][p] for p in prov]) for n in sets}
    Y.update(extra_sets)
    pred = {n: np.empty(len(recs), dtype=object) for n in names}
    for f, (tr, te) in enumerate(make_folds(recs)):
        t0 = time.time()
        Xtr, Xte = fold_matrices([docs[i] for i in tr], [docs[i] for i in te])
        for n in names:
            lr = LogisticRegression(C=10, class_weight="balanced", max_iter=3000)
            pred[n][te] = lr.fit(Xtr, Y[n][tr]).predict(Xte)
        print(f"[{src}] fold {f} done in {time.time() - t0:.0f}s", flush=True)
    rows = []
    for n in names:
        s = log_result(f"R8 labels: {n}", "review_labels", f"{src}-labels", Y[n], pred[n],
                       notes=("partition " + json.dumps(sets[n], ensure_ascii=False)) if n in sets else "")
        rows.append({"label_set": n, **metrics(Y[n], pred[n]), "bal_acc": s["bal_acc"]})
    return pd.DataFrame(rows), pred


def within_share(cm, provs, m):
    grp = np.array([m[p] for p in provs])
    same = grp[:, None] == grp[None, :]
    off = ~np.eye(len(provs), dtype=bool)
    return cm[same & off].sum() / cm[off].sum()


def posthoc(src, recs, p2g, prov_pred, n_null, seed=0):
    """Map OOF province predictions through partitions; also part 4 (within-色彩区 error share)."""
    prov = np.array([r["province"] for r in recs])
    provs = sorted(p2g)
    parts = all_partitions(p2g) if src == "A" else random_partitions(p2g, n_null, seed=seed + 7)
    rows = []
    cm = confusion_matrix(prov, prov_pred, labels=provs)
    for i, m in enumerate([p2g] + parts):
        y = np.array([m[p] for p in prov])
        yp = np.array([m[p] for p in prov_pred])
        rows.append({"partition": "secaiqu" if i == 0 else f"null#{i}", **metrics(y, yp),
                     "within_err_share": within_share(cm, provs, m)})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"labels_posthoc_{src}.csv", index=False)
    true, null = df.iloc[0], df.iloc[1:]
    out = {"n_null": len(null)}
    for k in ["kappa", "macro_f1", "within_err_share"]:
        out[f"{k}_secaiqu"] = true[k]
        out[f"{k}_null_mean"] = null[k].mean()
        out[f"{k}_null_p95"] = null[k].quantile(0.95)
        out[f"{k}_p"] = (np.sum(null[k] >= true[k]) + 1) / (len(null) + 1)
    # errors as a share of all songs, and the 'expected' within share if errors were spread by pair counts
    grp = np.array([p2g[p] for p in provs])
    same = (grp[:, None] == grp[None, :]) & ~np.eye(len(provs), dtype=bool)
    out["pairs_within_share"] = same.sum() / (len(provs) * (len(provs) - 1))
    pd.DataFrame(cm, index=provs, columns=provs).to_csv(OUT / f"labels_confusion_{src}.csv")
    return out, df


def plot_null(src, df, post):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    rp = df[df.label_set.str.startswith("randpart")]
    ax = axes[0]
    ax.hist(rp.kappa, bins=15, color="0.7", label=f"random same-size partitions (n={len(rp)})")
    for n, c in [("secaiqu", "C3"), ("geo-opt", "C0"), (f"geo-k{df.K[df.label_set == 'secaiqu'].iloc[0]}", "C2")]:
        if n in set(df.label_set):
            ax.axvline(df.kappa[df.label_set == n].iloc[0], color=c, lw=2, label=n)
    ax.set_xlabel("Cohen's kappa (retrained n-gram LR)")
    ax.set_title(f"{src}: learnability of province groupings")
    ax.legend(fontsize=7)
    ax = axes[1]
    null = post[post.partition != "secaiqu"]
    ax.hist(null.within_err_share, bins=30, color="0.7", label=f"same-size partitions (n={len(null)})")
    ax.axvline(post.within_err_share.iloc[0], color="C3", lw=2, label="色彩区")
    ax.set_xlabel("share of province-classifier errors within the same group")
    ax.set_title(f"{src}: are province confusions within 色彩区?")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / f"regionclf_labels_null_{src}.png", dpi=150)


def volume_analysis(recs):
    """A only: 11-volume classifier; share of errors within the same province / same 色彩区."""
    vol = np.array([r["channel"] for r in recs])
    df, pred = learnability("A", recs, {}, {"volume": vol})
    vols = sorted(set(vol))
    v2p = {r["channel"]: r["province"] for r in recs}
    v2g = {r["channel"]: r["region"] for r in recs}
    cm = confusion_matrix(vol, pred["volume"], labels=vols)
    pd.DataFrame(cm, index=vols, columns=vols).to_csv(OUT / "labels_confusion_A_volume.csv")
    return df, {"within_province_err_share": within_share(cm, vols, v2p),
                "within_secaiqu_err_share": within_share(cm, vols, v2g)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="A,E")
    ap.add_argument("--n-rand", type=int, default=30)
    ap.add_argument("--n-null", type=int, default=5000)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for src in a.sources.split(","):
        recs = records(src)
        p2g, sets = label_sets(src, recs, a.n_rand)
        with open(OUT / f"labels_sets_{src}.json", "w") as f:
            json.dump(sets, f, ensure_ascii=False, indent=1)
        df, pred = learnability(src, recs, sets)
        if src == "A":
            dv, vol = volume_analysis(recs)
            df = pd.concat([df, dv])
            summary["A_volume"] = vol
        df.to_csv(OUT / f"labels_{src}.csv", index=False)
        rp = df[df.label_set.str.startswith("randpart")]
        t = df[df.label_set == "secaiqu"].iloc[0]
        summary[src] = {"n": len(recs), "n_prov": len(p2g), "K": int(t.K),
                        "kappa_secaiqu": t.kappa, "kappa_rand_mean": rp.kappa.mean(),
                        "kappa_rand_max": rp.kappa.max(), "kappa_rank_p": (np.sum(rp.kappa >= t.kappa) + 1) / (len(rp) + 1),
                        "f1_secaiqu": t.macro_f1, "f1_rand_mean": rp.macro_f1.mean(),
                        "f1_rank_p": (np.sum(rp.macro_f1 >= t.macro_f1) + 1) / (len(rp) + 1)}
        post, pdf = posthoc(src, recs, p2g, pred["province"], a.n_null)
        summary[f"{src}_posthoc"] = post
        plot_null(src, df, pdf)
        print(json.dumps(summary, ensure_ascii=False, indent=1, default=float), flush=True)
        with open(OUT / "labels_summary.json", "w") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
