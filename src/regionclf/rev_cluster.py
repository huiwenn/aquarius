"""
Reviewer R8, part 1: does *unsupervised* structure in the melodies recover the 色彩区?

Song-level clustering on each source (anthology, essen, trans_primary) with three representations
  theory   regionclf.features.matrix, standardized
  ngram    multi-viewpoint n-gram TF-IDF (exp_fusion VOCABS, fitted on all songs of the source; no labels) →
           TruncatedSVD(100) → L2-normalize (LSA)
  clamp    frozen CLaMP 3 C2 embedding c2_mtf_tonic (rows aligned with load(source) order, cf. exp_pretrained.py),
           standardized
and three methods: k-means, agglomerative (Ward), GMM (diagonal covariance), at k = number of regions and at a
sweep of k. Each clustering is scored (NMI, ARI) against
  region      the 色彩区 label
  province    province (anthology: 9; essen: songs with a province only); anthology also `volume` (11)
  randpart    random partitions of the same provinces into groups with the 色彩区's block sizes (mean over 50):
              the null for "is the 色彩区 grouping of provinces the one the clusters see?"
  random      permuted region labels (floor)
  length      quantile bins of note count (a trivial confound: do clusters just sort songs by length?)
NMI (and AMI, adjusted for chance) and ARI; and, as a trivial *clustering* control, the length-bin clustering itself scored against region/province.

Outputs: data/regionclf/review/cluster_song.csv, notebooks/figures/regionclf_cluster_sweep.png
Shared helpers (n-gram TF-IDF, province coordinates, random partitions) are imported by rev_cluster_profiles.py
and rev_cluster_labels.py.

Run (py312):
  OMP_NUM_THREADS=3 PYTHONPATH=src python src/regionclf/rev_cluster.py [--sources anthology,essen,trans_primary]
"""

import argparse
import itertools
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import D, ROOT, load  # noqa: E402
from secaiqu.mapping import PROVINCE_TO_SECAIQU  # noqa: E402
from sklearn.cluster import AgglomerativeClustering, KMeans  # noqa: E402
from sklearn.decomposition import PCA, TruncatedSVD  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.metrics import adjusted_mutual_info_score as ami  # noqa: E402
from sklearn.metrics import adjusted_rand_score as ari  # noqa: E402
from sklearn.metrics import normalized_mutual_info_score as nmi  # noqa: E402
from sklearn.mixture import GaussianMixture  # noqa: E402
from sklearn.preprocessing import StandardScaler, normalize  # noqa: E402

OUT = D / "review"
FIG = ROOT / "notebooks" / "figures"
MIN_PROV = 20  # essen: provinces with ≥ 20 songs enter province-level analyses

PROVINCE_LATLON = {  # approximate centre of each province's song-collecting area (lat, lon)
    "Hebei": (38.5, 115.5), "Jilin": (43.7, 126.2), "Tianjin": (39.1, 117.2), "Jiangsu": (32.9, 119.5),
    "Shanghai": (31.2, 121.5), "Guangdong": (23.3, 113.5), "Hainan": (19.2, 109.8), "Henan": (33.9, 113.5),
    "Sichuan": (30.6, 104.0), "Shanxi": (37.6, 112.3), "Hubei": (30.9, 112.3), "Hunan": (27.6, 111.7),
    "Anhui": (31.8, 117.2), "Jiangxi": (27.6, 115.7), "Shandong": (36.3, 118.2), "Fujian": (26.0, 118.2),
    "Liaoning": (41.3, 122.6), "Ningxia": (37.3, 106.2), "Zhejiang": (29.2, 120.1), "Gansu": (36.1, 103.8),
    "Qinghai": (36.6, 101.8), "Yunnan": (25.0, 101.5), "Taiwan": (23.7, 121.0), "Guangxi": (23.8, 108.8),
    "Heilongjiang": (47.0, 128.0), "Northern Shaanxi": (37.0, 109.5), "Guizhou": (26.8, 106.9),
    "Inner Mongolia": (41.0, 111.0)}


# ───────────────────────────── shared helpers ─────────────────────────────

def province_set(source: str, recs=None) -> dict[str, str]:
    """Provinces usable for province-level analyses → their 色彩区 (anthology: all 9; essen: Han provinces with
    ≥ MIN_PROV songs, whose 色彩区 is fixed by the province in Essen)."""
    recs = recs if recs is not None else load(source)
    c = pd.Series([r["province"] for r in recs if r.get("province")]).value_counts()
    keep = c.index if source == "anthology" else c[c >= MIN_PROV].index
    m = {}
    for p in keep:
        regs = {r["region"] for r in recs if r.get("province") == p}
        assert len(regs) == 1, (p, regs)
        m[p] = regs.pop()
        assert PROVINCE_TO_SECAIQU.get(p, m[p]) == m[p]
    return dict(sorted(m.items()))


def random_partitions(prov2grp: dict[str, str], n: int, seed: int = 0, exclude_true: bool = True):
    """n distinct random re-groupings of the provinces into blocks with the same sizes as prov2grp.
    Returns a list of dicts province → 'G<i>'."""
    provs = list(prov2grp)
    sizes = sorted(pd.Series(prov2grp).value_counts().tolist(), reverse=True)

    def canon(m):
        blocks = {}
        for p, g in m.items():
            blocks.setdefault(g, []).append(p)
        return frozenset(frozenset(b) for b in blocks.values())

    seen = {canon(prov2grp)} if exclude_true else set()
    rng = np.random.RandomState(seed)
    out, tries = [], 0
    while len(out) < n and tries < 100 * n:
        tries += 1
        perm = rng.permutation(provs)
        m, i = {}, 0
        for g, s in enumerate(sizes):
            for p in perm[i:i + s]:
                m[p] = f"G{g}"
            i += s
        c = canon(m)
        if c not in seen:
            seen.add(c)
            out.append(m)
    return out


def all_partitions(prov2grp: dict[str, str]):
    """Every distinct partition of the provinces into blocks of the same sizes (for small cases, e.g. 9 → 5)."""
    provs = list(prov2grp)
    sizes = sorted(pd.Series(prov2grp).value_counts().tolist(), reverse=True)
    res = set()

    def rec(rest, sizes, acc):
        if not sizes:
            res.add(frozenset(acc))
            return
        s = sizes[0]
        first = rest[0]  # canonical: block containing the first remaining province of the largest remaining size
        for comb in itertools.combinations(rest, s):
            left = [p for p in rest if p not in comb]
            rec(left, sizes[1:], acc + [frozenset(comb)])
        _ = first

    rec(provs, sizes, [])
    parts = []
    for fs in res:
        m = {}
        for g, b in enumerate(sorted(fs, key=lambda b: (-len(b), sorted(b)))):
            for p in b:
                m[p] = f"G{g}"
        parts.append(m)
    return parts


VOCABS = ["deg", "int", "degdur", "intdur", "dur", "degoct", "contour"]


def ngram_tfidf(recs, cache_name: str | None = None):
    """Multi-viewpoint n-gram TF-IDF (same vocabularies/settings as exp_fusion.ngram_model), one block per
    viewpoint, each block L2-normalized, blocks hstacked. Fitted on all given records (unsupervised)."""
    from scipy import sparse
    path = OUT / f"tfidf_{cache_name}.pkl" if cache_name else None
    if path is not None and path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    from regionclf.exp_fusion import doc
    docs = [doc(r) for r in recs]
    blocks = []
    for i in range(len(VOCABS)):
        v = TfidfVectorizer(token_pattern=r"\S+", lowercase=False, ngram_range=(1, 4), sublinear_tf=True,
                            min_df=2, max_features=200_000)
        blocks.append(v.fit_transform([d[i] for d in docs]))
    X = sparse.hstack(blocks).tocsr()
    if path is not None:
        OUT.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(X, f)
    return X


def theory_matrix(recs, cache_name: str | None = None):
    path = OUT / f"theory_{cache_name}.npy" if cache_name else None
    if path is not None and path.exists():
        return np.load(path)
    from regionclf.features import matrix
    X = np.nan_to_num(matrix(recs))
    if path is not None:
        OUT.mkdir(parents=True, exist_ok=True)
        np.save(path, X)
    return X


# ───────────────────────────── song-level clustering ─────────────────────────────

def representations(source, recs):
    reps = {}
    reps["theory"] = StandardScaler().fit_transform(theory_matrix(recs, source))
    X = ngram_tfidf(recs, source)
    reps["ngram"] = normalize(TruncatedSVD(100, random_state=0).fit_transform(X))
    emb = np.load(D / "emb" / f"c2_mtf_tonic_{source}.npy")
    assert len(emb) == len(recs)
    reps["clamp"] = StandardScaler().fit_transform(np.nan_to_num(emb))
    return reps


def cluster(method, X, k, seed=0):
    if method == "kmeans":
        return KMeans(k, n_init=10, random_state=seed).fit_predict(X)
    if method == "ward":
        return AgglomerativeClustering(k, linkage="ward").fit_predict(X)
    if method == "gmm":
        Z = PCA(min(50, X.shape[1]), random_state=seed).fit_transform(X) if X.shape[1] > 50 else X
        return GaussianMixture(k, covariance_type="diag", n_init=2, random_state=seed, reg_covar=1e-4).fit_predict(Z)
    raise ValueError(method)


def label_sets(source, recs, n_rand=50):
    """Reference labelings: name → (array, mask of songs where it is defined)."""
    n = len(recs)
    y = np.array([r["region"] for r in recs])
    L = {"region": (y, np.ones(n, bool))}
    p2g = province_set(source, recs) if source != "trans_primary" else {}
    if p2g:
        prov = np.array([r.get("province") or "" for r in recs])
        m = np.isin(prov, list(p2g))
        L["province"] = (prov, m)
        L["region|prov"] = (y, m)  # region restricted to the same songs, for a fair comparison with randpart
        L["randpart"] = [(np.array([rp.get(p, "") for p in prov]), m) for rp in random_partitions(p2g, n_rand)]
    if source == "anthology":
        L["volume"] = (np.array([r["channel"] for r in recs]), np.ones(n, bool))
    rng = np.random.RandomState(0)
    L["random"] = [(rng.permutation(y), np.ones(n, bool)) for _ in range(5)]
    return L


def length_bins(recs, k):
    ln = np.array([len(r["notes"]) for r in recs])
    q = np.quantile(ln, np.linspace(0, 1, k + 1)[1:-1])
    return np.digitize(ln, q)


def score(c, L, lb):
    row = {}
    for name, v in L.items():
        vs = v if isinstance(v, list) else [v]
        nm = [nmi(lab[m], c[m]) for lab, m in vs]
        ar = [ari(lab[m], c[m]) for lab, m in vs]
        row[f"NMI_{name}"] = np.mean(nm)
        row[f"ARI_{name}"] = np.mean(ar)
        row[f"AMI_{name}"] = np.mean([ami(lab[m], c[m]) for lab, m in vs])
        if name == "randpart":
            row["NMI_randpart_p95"] = np.percentile(nm, 95)
            row["NMI_randpart_max"] = np.max(nm)
            row["ARI_randpart_p95"] = np.percentile(ar, 95)
    row["NMI_length"] = nmi(lb, c)
    row["AMI_length"] = ami(lb, c)
    return row


def run_source(source, ks):
    recs = load(source)
    K = len({r["region"] for r in recs})
    reps = representations(source, recs)
    L = label_sets(source, recs)
    rows = []
    for k in sorted(set(ks) | {K}):
        lb = length_bins(recs, k)
        rows.append({"source": source, "rep": "length-bins", "method": "quantile", "k": k, "K_region": K,
                     **score(lb, L, lb)})
        for rep, X in reps.items():
            for method in ["kmeans", "ward", "gmm"]:
                c = cluster(method, X, k)
                r = {"source": source, "rep": rep, "method": method, "k": k, "K_region": K, **score(c, L, lb)}
                rows.append(r)
                print(f"{source:13s} {rep:6s} {method:6s} k={k:2d}  NMI region {r['NMI_region']:.3f}  "
                      f"province {r.get('NMI_province', np.nan):.3f}  randpart {r.get('NMI_randpart', np.nan):.3f}"
                      f"  random {r['NMI_random']:.3f}  length {r['NMI_length']:.3f}", flush=True)
    return rows


def plot_sweep(df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    srcs = list(df.source.unique())
    fig, axes = plt.subplots(1, len(srcs), figsize=(5 * len(srcs), 3.8), squeeze=False)
    for ax, s in zip(axes[0], srcs):
        d = df[(df.source == s) & (df.method == "kmeans")]
        for rep, col in [("theory", "C0"), ("ngram", "C1"), ("clamp", "C2"), ("length-bins", "0.5")]:
            e = d[d.rep == rep] if rep != "length-bins" else df[(df.source == s) & (df.rep == rep)]
            e = e.sort_values("k")
            ax.plot(e.k, e.NMI_region, "-o", color=col, ms=3, label=f"{rep} vs 色彩区")
            if "NMI_province" in e and e.NMI_province.notna().any() and rep != "length-bins":
                ax.plot(e.k, e.NMI_province, "--", color=col, lw=1, label=f"{rep} vs province")
            if "NMI_randpart" in e and e.NMI_randpart.notna().any() and rep != "length-bins":
                ax.plot(e.k, e.NMI_randpart, ":", color=col, lw=1, label=f"{rep} vs random prov. grouping")
        ax.axvline(d.K_region.iloc[0], color="k", lw=0.5)
        ax.set_title(f"{s}: k-means clusters")
        ax.set_xlabel("k")
        ax.set_ylabel("NMI")
        ax.set_xscale("log")
    axes[0][0].legend(fontsize=6)
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
    fig.tight_layout()
    fig.savefig(FIG / "regionclf_cluster_sweep.png", dpi=150)


def main():
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="anthology,essen,trans_primary")
    ap.add_argument("--ks", default="2,3,5,8,11,15,20,30")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in a.sources.split(","):
        rows += run_source(s, [int(k) for k in a.ks.split(",")])
        pd.DataFrame(rows).to_csv(OUT / "cluster_song.csv", index=False)
    plot_sweep(pd.DataFrame(rows))


if __name__ == "__main__":
    main()
