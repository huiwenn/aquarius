"""
Reviewer R8, part 2: region-profile (and province-profile) clustering.

For each source (anthology, essen, trans_primary) each region's mean profile is computed in two spaces
  theory   mean of the standardized theory features (z-scored over the source's songs)
  ngram    centroid of the L2-normalized multi-viewpoint n-gram TF-IDF rows (rev_cluster.ngram_tfidf)
Distances are bias-corrected Euclidean distances between means (see `tree`), so small regions are not pushed out
as outliers by sampling noise;
(regions with ≥ 20 songs), and an average-linkage (UPGMA) dendrogram is built. Clade support = share of 200
bootstrap resamples (songs resampled within region) that reproduce the clade.
The trees are compared with
  (i)   geography: Spearman ρ between cophenetic (and raw profile) distance and great-circle distance between
        region centroids (analyze.CENTROIDS); Mantel permutation p over region labels
  (ii)  the literature's groupings: Han 色彩区 vs minority areas; north (东北, 西北, 江淮) vs south. Statistic =
        mean between-group − mean within-group cophenetic distance (standardized), permutation p over leaves;
        plus Fowlkes–Mallows B_k of the tree cut at k = 2 vs the grouping
  (iii) other sources: cophenetic correlation of the trees restricted to shared regions (Mantel p), and
        Fowlkes–Mallows B_k at k = 2..n−1
Province level (anthology 9 provinces + 11 volumes, essen 20 Han provinces with ≥ 20 songs): the province tree is
cut at k = #色彩区 and compared with the 色彩区 grouping (FM index and within/between cophenetic contrast) against
random same-size partitions of the provinces (rev_cluster.random_partitions); plus Mantel vs province geography.

Outputs: data/regionclf/review/profiles_*.csv, profiles_summary.json,
         notebooks/figures/regionclf_dendrogram_<source>.png, regionclf_dendrogram_<source>_provinces.png
Run (py312):
  OMP_NUM_THREADS=3 PYTHONPATH=src python src/regionclf/rev_cluster_profiles.py
"""

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.analyze import CENTROIDS, MINORITY, haversine  # noqa: E402
from regionclf.common import ROOT, load  # noqa: E402
from regionclf.rev_cluster import (OUT, PROVINCE_LATLON, ngram_tfidf, province_set, random_partitions,  # noqa: E402
                                   theory_matrix)
from scipy.cluster.hierarchy import cophenet, dendrogram, fcluster, linkage, to_tree  # noqa: E402
from scipy.spatial.distance import pdist, squareform  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.metrics import fowlkes_mallows_score  # noqa: E402
from sklearn.preprocessing import StandardScaler, normalize  # noqa: E402

FIG = ROOT / "notebooks" / "figures"
SOURCES = ["anthology", "essen", "trans_primary"]
NORTH_LIT = {"东北部平原", "西北部高原", "江淮"}
SHORT = {"西南多民族古老原始文化民歌区": "西南多民族", "北方草原文化民歌区": "北方草原", "新疆民歌区": "新疆",
         "藏族民歌区": "藏族"}
N_BOOT, N_PERM = 200, 10000


# ─────────────────────────── profiles and trees ───────────────────────────

def spaces(source, recs):
    Z = StandardScaler().fit_transform(theory_matrix(recs, source))
    T = normalize(ngram_tfidf(recs, source))
    return {"theory": (Z, "euclidean"), "ngram": (T, "euclidean-on-L2-rows")}


def profile(X, idx_by_unit):
    """Unit means M and the sampling-noise term tr(Σ_a)/n_a of each mean (needed for the bias correction)."""
    M, noise = [], []
    for ix in idx_by_unit:
        Xa = X[ix]
        m = np.asarray(Xa.mean(0)).ravel()
        sq = Xa.multiply(Xa).sum(1) if hasattr(Xa, "multiply") else (Xa ** 2).sum(1)
        tr = (np.asarray(sq).ravel().mean() - m @ m) * len(ix) / max(len(ix) - 1, 1)
        M.append(m)
        noise.append(tr / len(ix))
    return np.vstack(M), np.array(noise)


def tree(P, metric="euclidean"):
    """Average-linkage tree on bias-corrected Euclidean distances between unit means:
    d²(a,b) = ||m_a − m_b||² − tr(Σ_a)/n_a − tr(Σ_b)/n_b (unbiased for ||μ_a − μ_b||²), clipped at 0.
    Without the correction, small units (few songs → noisy means) sit far from everything and form singleton
    outliers. `metric` is kept for the record: theory = z-scored features, ngram = L2-normalized TF-IDF rows, so
    the latter is a (corrected) chordal/cosine-type distance."""
    M, noise = P
    D2 = squareform(pdist(M, "sqeuclidean")) - noise[:, None] - noise[None, :]
    np.fill_diagonal(D2, 0)
    d = squareform(np.sqrt(np.clip(D2, 1e-12, None)), checks=False)
    return linkage(d, "average"), d


def clades(L, n):
    root = to_tree(L)
    out = []

    def rec(node):
        if node.is_leaf():
            return frozenset([node.id])
        s = rec(node.left) | rec(node.right)
        if 1 < len(s) < n:
            out.append(s)
        return s
    rec(root)
    return out


def bootstrap_support(X, metric, idx_by_unit, L, seed=0):
    rng = np.random.RandomState(seed)
    n = len(idx_by_unit)
    ref = clades(L, n)
    hits = dict.fromkeys(ref, 0)
    for _ in range(N_BOOT):
        P = profile(X, [rng.choice(ix, len(ix), replace=True) for ix in idx_by_unit])
        cs = set(clades(tree(P, metric)[0], n))
        for c in ref:
            hits[c] += c in cs
    return {c: hits[c] / N_BOOT for c in ref}


# ─────────────────────────── statistics ───────────────────────────

def mantel(D1, D2, n_perm=N_PERM, seed=0):
    """Spearman ρ between two square distance matrices, permutation p (one-sided, ρ > 0) over labels of D2.
    Exact enumeration when n! ≤ n_perm."""
    n = len(D1)
    iu = np.triu_indices(n, 1)
    rho = spearmanr(D1[iu], D2[iu]).correlation
    if math.factorial(n) <= n_perm:
        perms = list(itertools.permutations(range(n)))
    else:
        rng = np.random.RandomState(seed)
        perms = [rng.permutation(n) for _ in range(n_perm)]
    null = np.array([spearmanr(D1[iu], D2[np.ix_(p, p)][iu]).correlation for p in perms])
    if math.factorial(n) <= n_perm:  # exact: the identity permutation is in the null
        return rho, np.sum(null >= rho - 1e-12) / len(null)
    return rho, (np.sum(null >= rho - 1e-12) + 1) / (len(null) + 1)


def group_contrast(C, groups, n_perm=N_PERM, seed=0, null_groupings=None):
    """(mean between − mean within cophenetic distance) / mean distance; p over permuted leaves or given
    null groupings."""
    g = np.asarray(groups)
    iu = np.triu_indices(len(g), 1)

    def stat(gg):
        same = (gg[:, None] == gg[None, :])[iu]
        if same.all() or not same.any():
            return np.nan
        return (C[iu][~same].mean() - C[iu][same].mean()) / C[iu].mean()
    s = stat(g)
    if null_groupings is None:
        rng = np.random.RandomState(seed)
        null_groupings = [rng.permutation(g) for _ in range(n_perm)]
    null = np.array([stat(np.asarray(x)) for x in null_groupings])
    return s, (np.sum(null >= s - 1e-12) + 1) / (len(null) + 1)


def fm_cut(L, groups, k=None):
    k = k or len(set(groups))
    return fowlkes_mallows_score(groups, fcluster(L, k, "maxclust"))


def geo_matrix(names, coords):
    return np.array([[haversine(coords[a], coords[b]) for b in names] for a in names])


# ─────────────────────────── plotting ───────────────────────────

def color_of(name, level):
    if level == "province":
        return None
    if name in MINORITY:
        return "C2"
    return "C3" if name in NORTH_LIT else "C0"


def plot_trees(fname, panels, suptitle, leaf_colors):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 0.32 * max(len(p[1]) for p in panels) + 2.2))
    for ax, (title, names, L, support) in zip(np.atleast_1d(axes), panels):
        lbl = [SHORT.get(n, n) for n in names]
        dn = dendrogram(L, labels=lbl, orientation="right", ax=ax, color_threshold=0, above_threshold_color="0.3")
        for t in ax.get_yticklabels():
            full = names[lbl.index(t.get_text())]
            c = leaf_colors(full)
            if c:
                t.set_color(c)
        # clade support on internal nodes (scipy places a node at the midpoint of its two children)
        n = len(names)
        ypos = {leaf: 5 + 10 * j for j, leaf in enumerate(dn["leaves"])}
        members = {i: frozenset([i]) for i in range(n)}
        for k, row in enumerate(L):
            a, b = int(row[0]), int(row[1])
            ypos[n + k] = (ypos[a] + ypos[b]) / 2
            members[n + k] = members[a] | members[b]
            if members[n + k] in support:
                ax.text(row[2], ypos[n + k], f"{support[members[n + k]]:.0%}", fontsize=6, color="0.35",
                        ha="right", va="bottom")
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("profile distance (average linkage)")
    fig.suptitle(suptitle, fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=150)
    plt.close(fig)


# ─────────────────────────── main analyses ───────────────────────────

def region_level(source):
    recs = load(source)
    y = np.array([r["region"] for r in recs])
    cnt = pd.Series(y).value_counts()
    regs = sorted(cnt[cnt >= 20].index)
    idx = [np.where(y == g)[0] for g in regs]
    geo = geo_matrix(regs, CENTROIDS)
    res, trees, panels = {}, {}, []
    for sp, (X, metric) in spaces(source, recs).items():
        P = profile(X, idx)
        L, d = tree(P, metric)
        D = squareform(d)
        C = squareform(cophenet(L))
        sup = bootstrap_support(X, metric, idx, L)
        r = {"n_regions": len(regs), "cophenetic_fit": cophenet(L, d)[0]}
        r["geo_rho_profile"], r["geo_p_profile"] = mantel(D, geo)
        r["geo_rho_tree"], r["geo_p_tree"] = mantel(C, geo)
        han = np.array(["minority" if g in MINORITY else "Han" for g in regs])
        if len(set(han)) > 1:
            r["hanmin_contrast"], r["hanmin_p"] = group_contrast(C, han)
            r["hanmin_FM_k2"] = fm_cut(L, han, 2)
        hanidx = [i for i, g in enumerate(regs) if g not in MINORITY]
        ns = np.array(["N" if regs[i] in NORTH_LIT else "S" for i in hanidx])
        if len(set(ns)) > 1:
            Ch = C[np.ix_(hanidx, hanidx)]
            r["NS_contrast_han"], r["NS_p_han"] = group_contrast(Ch, ns)
            Lh = tree((P[0][hanidx], P[1][hanidx]), metric)[0]
            r["NS_FM_k2_han"] = fm_cut(Lh, ns, 2)
        a = fcluster(L, 2, "maxclust")
        r["cut_k2"] = " | ".join(",".join(SHORT.get(regs[i], regs[i]) for i in np.where(a == c)[0]) for c in (1, 2))
        r["strong_clades"] = "; ".join(",".join(SHORT.get(regs[i], regs[i]) for i in sorted(c)) + f" ({s:.0%})"
                                       for c, s in sorted(sup.items(), key=lambda x: -x[1]) if s >= 0.7)
        res[sp] = r
        trees[sp] = (regs, L, C, D)
        panels.append((f"{sp} profiles  (tree~geo ρ={r['geo_rho_tree']:.2f}, p={r['geo_p_tree']:.3f})",
                       regs, L, sup))
        print(source, sp, json.dumps(r, ensure_ascii=False, default=float), flush=True)
    plot_trees(f"regionclf_dendrogram_{source}.png", panels,
               f"{source}: 色彩区 profile dendrograms (red = north 东北/西北/江淮, blue = south Han, green = minority;"
               f" % = bootstrap clade support)", lambda g: color_of(g, "region"))
    return res, trees


def province_level(source, unit="province"):
    recs = load(source)
    if unit == "volume":
        key = "channel"
        u2g = {r["channel"]: r["region"] for r in recs}
    else:
        key = "province"
        u2g = province_set(source, recs)
    units = sorted(u2g)
    lab = np.array([r.get(key) or "" for r in recs])
    idx = [np.where(lab == u)[0] for u in units]
    grp = np.array([u2g[u] for u in units])
    K = len(set(grp))
    geo_units = units if unit == "province" else None
    out, panels = {}, []
    if unit == "province":
        nulls = [np.array([m[u] for u in units]) for m in random_partitions(dict(zip(units, grp)), 2000, seed=3)]
    else:  # volumes: randomize the volume → province grouping? use same-size partitions of volumes
        nulls = [np.array([m[u] for u in units]) for m in random_partitions(dict(zip(units, grp)), 2000, seed=3)]
    for sp, (X, metric) in spaces(source, recs).items():
        P = profile(X, idx)
        L, d = tree(P, metric)
        C = squareform(cophenet(L))
        sup = bootstrap_support(X, metric, idx, L)
        r = {"n_units": len(units), "K": K}
        fm = fm_cut(L, grp, K)
        fm_null = np.array([fm_cut(L, g, K) for g in nulls])
        r["FM_secaiqu"], r["FM_null_mean"], r["FM_p"] = fm, fm_null.mean(), (np.sum(fm_null >= fm) + 1) / (len(nulls) + 1)
        r["contrast_secaiqu"], r["contrast_p"] = group_contrast(C, grp, null_groupings=nulls)
        if unit == "volume":
            v2p = {rr["channel"]: rr["province"] for rr in recs}
            prov = np.array([v2p[u] for u in units])
            r["contrast_province"], r["contrast_province_p"] = group_contrast(C, prov, n_perm=2000)
        if geo_units:
            geo = geo_matrix(units, PROVINCE_LATLON)
            r["geo_rho_profile"], r["geo_p_profile"] = mantel(squareform(d), geo, n_perm=2000)
            r["geo_rho_tree"], r["geo_p_tree"] = mantel(C, geo, n_perm=2000)
        cut = fcluster(L, K, "maxclust")
        r["cut_K"] = " | ".join(",".join(units[i] for i in np.where(cut == c)[0]) for c in sorted(set(cut)))
        out[sp] = r
        panels.append((f"{sp}: cut at k={K} vs 色彩区 FM={fm:.2f} (null {fm_null.mean():.2f}, p={r['FM_p']:.3f})",
                       [f"{u} ({SHORT.get(u2g[u], u2g[u])})" for u in units], L, sup))
        print(source, unit, sp, json.dumps(r, ensure_ascii=False, default=float), flush=True)
    pal = {g: f"C{i}" for i, g in enumerate(sorted(set(grp)))}
    lc = {f"{u} ({SHORT.get(u2g[u], u2g[u])})": pal[u2g[u]] for u in units}
    plot_trees(f"regionclf_dendrogram_{source}_{unit}s.png",
               [(t, n, L, s) for t, n, L, s in panels], f"{source}: {unit} profile dendrograms (colour = 色彩区)",
               lambda n: lc.get(n))
    return out


def cross_source(trees):
    rows = []
    for sp in ["theory", "ngram"]:
        for a, b in itertools.combinations(SOURCES, 2):
            ra, La, Ca, Da = trees[a][sp]
            rb, Lb, Cb, Db = trees[b][sp]
            shared = [g for g in ra if g in rb]
            ia, ib = [ra.index(g) for g in shared], [rb.index(g) for g in shared]
            Ca_, Cb_ = Ca[np.ix_(ia, ia)], Cb[np.ix_(ib, ib)]
            Da_, Db_ = Da[np.ix_(ia, ia)], Db[np.ix_(ib, ib)]
            rho_t, p_t = mantel(Ca_, Cb_)
            rho_d, p_d = mantel(Da_, Db_)
            La_ = linkage(squareform(Da_, checks=False), "average")
            Lb_ = linkage(squareform(Db_, checks=False), "average")
            bk = {}
            rng = np.random.RandomState(0)
            for k in range(2, len(shared)):
                ca, cb = fcluster(La_, k, "maxclust"), fcluster(Lb_, k, "maxclust")
                v = fowlkes_mallows_score(ca, cb)
                null = [fowlkes_mallows_score(ca, rng.permutation(cb)) for _ in range(2000)]
                bk[k] = (v, np.mean(null), (np.sum(np.array(null) >= v) + 1) / 2001)
            rows.append({"space": sp, "pair": f"{a}~{b}", "n_shared": len(shared),
                         "coph_rho": rho_t, "coph_p": p_t, "profile_rho": rho_d, "profile_p": p_d,
                         **{f"B{k}": f"{v:.2f} (null {m:.2f}, p={p:.3f})" for k, (v, m, p) in bk.items()}})
            print(rows[-1], flush=True)
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary, trees = {}, {}
    for s in SOURCES:
        res, trees[s] = region_level(s)
        summary[f"{s}_regions"] = res
    pd.DataFrame([{"source": k, "space": sp, **v} for k, d in summary.items() for sp, v in d.items()]) \
        .to_csv(OUT / "profiles_regions.csv", index=False)
    cs = cross_source(trees)
    cs.to_csv(OUT / "profiles_cross_source.csv", index=False)
    prov = {}
    for s, unit in [("anthology", "province"), ("anthology", "volume"), ("essen", "province")]:
        prov[f"{s}_{unit}"] = province_level(s, unit)
    pd.DataFrame([{"what": k, "space": sp, **v} for k, d in prov.items() for sp, v in d.items()]) \
        .to_csv(OUT / "profiles_provinces.csv", index=False)
    with open(OUT / "profiles_summary.json", "w") as f:
        json.dump({**summary, **prov}, f, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
