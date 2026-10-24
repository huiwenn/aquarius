"""
One musical profile per region, combining the four analyses (scales, intonation, rhythm, melody).

Features (one clear measure per aspect; the unreliable ones are left out: mode shares, isochrony, glide share):
  scales      penta_coverage, bian_share
  intonation  off_grid_local
  rhythm      note_rate, long_note_share, rest_share, tempo_variation
  melody      range_90, mean_abs_interval, leap_share, phrase_net_change, contour_arch
Each region's value is the mean over its recordings. Features are z-scored across the 15 regions (0 = average region),
so every feature counts equally. Regions are compared by Euclidean distance in that space and clustered (Ward).

Uncertainty and geography (the point of the bootstrap): with 15 regions and overlapping intervals, clusters can look firmer
than they are. So the whole analysis is repeated 1,000 times, resampling whole groups (`group_id`: channel or singer) within
each region. From that:
  - pair stability: how often two regions fall in the same cluster (k clusters)
  - Mantel test: do musically similar regions lie close together? Spearman correlation between the musical distance
    and the geographic distance of the region centres (median lon/lat of recordings with a known place), with a
    permutation p-value and a bootstrap interval
Outputs: region_profile.csv (means and z-scores), region_signatures.md, pair_stability.csv, and three figures.

Limits: 15 regions give a small, discontinuous geography (Xinjiang, Tibet and the Northern Steppe are huge); many features are
correlated (rest share, held notes, note rate); regional means hide wide differences between songs; automatic measures,
exploratory only.
Run (from the repo root, after the four analyses):  python src/analysis/recordings/region_profiles.py [--k 3] [--out data/analysis/recordings/profiles]
"""

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, leaves_list, linkage
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, style

N_BOOT = 1000
FEATURES = {  # column: (table, label, phrase when high, phrase when low)
    "penta_coverage": ("scales", "Pentatonic fit", "strongly pentatonic", "less pentatonic"),
    "bian_share": ("scales", "Non-pentatonic notes (偏)", "many 偏 notes", "few 偏 notes"),
    "off_grid_local": ("intonation", "Between-the-keys singing", "more off the piano grid", "closer to the piano grid"),
    "note_rate": ("rhythm", "Notes per second", "fast notes", "slow notes"),
    "long_note_share": ("rhythm", "Held notes", "many held notes", "few held notes"),
    "rest_share": ("rhythm", "Phrase-break time", "long pauses", "short pauses"),
    "tempo_variation": ("rhythm", "Speed variation", "uneven speed", "steady speed"),
    "range_90": ("melody", "Pitch range", "wide range", "narrow range"),
    "mean_abs_interval": ("melody", "Mean interval", "larger intervals", "smaller intervals"),
    "leap_share": ("melody", "Leaps (5+ semitones)", "many leaps", "few leaps"),
    "phrase_net_change": ("melody", "Phrase end minus start", "phrases end near where they start", "phrases end much lower"),
    "contour_arch": ("melody", "Arch-shaped phrases", "many arch phrases", "few arch phrases"),
}
GROUP_TITLE = {"scales": "Scales", "intonation": "Intonation", "rhythm": "Rhythm", "melody": "Melody"}
TYPE_COLOR = {"Han": "#2a78d6", "minority": "#eb6834"}
BLUE, ORANGE = "#2a78d6", "#eb6834"


def load() -> tuple[pd.DataFrame, list[str]]:
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")[["item_id", "region_en", "group_id"]]
    d = rec.copy()
    for table in dict.fromkeys(v[0] for v in FEATURES.values()):
        cols = [c for c, v in FEATURES.items() if v[0] == table]
        t = pd.read_csv(OUT_ROOT / table / "per_recording.csv")[["item_id"] + cols]
        d = d.merge(t, on="item_id", how="left")
    d = d.dropna(subset=list(FEATURES), how="all")
    return d, sorted(d.region_en.unique())


def group_sums(d: pd.DataFrame, regions: list[str]):
    """Per region: group-level sums and counts of every feature, for fast bootstrap resampling."""
    out = []
    cols = list(FEATURES)
    for r in regions:
        g = d[d.region_en == r].groupby("group_id")
        out.append((g[cols].sum(min_count=1).fillna(0).to_numpy(), g[cols].count().to_numpy()))
    return out


def means(gs, rng=None) -> np.ndarray:
    m = []
    for s, c in gs:
        idx = np.arange(len(s)) if rng is None else rng.integers(0, len(s), len(s))
        m.append(s[idx].sum(0) / np.maximum(c[idx].sum(0), 1))
    return np.array(m)


def zscore(m: np.ndarray) -> np.ndarray:
    return (m - m.mean(0)) / m.std(0)


def haversine(lon, lat):
    lon, lat = np.radians(lon), np.radians(lat)
    dlon, dlat = lon[:, None] - lon[None], lat[:, None] - lat[None]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None] * np.sin(dlon / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def mantel(dm: np.ndarray, dg: np.ndarray) -> float:
    iu = np.triu_indices(len(dm), 1)
    return float(spearmanr(dm[iu], dg[iu])[0])


def signature(z_row: pd.Series, thr: float = 1.0) -> str:
    parts = []
    for f in z_row.abs().sort_values(ascending=False).index:
        if abs(z_row[f]) < thr:
            break
        hi, lo = FEATURES[f][2], FEATURES[f][3]
        parts.append(f"{hi if z_row[f] > 0 else lo} ({z_row[f]:+.1f})")
    return "; ".join(parts[:5]) or "close to average on every measure"


def plot_heatmap(z, regions, order, link, out: Path, k_labels):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", [BLUE, "#f1f0ec", ORANGE])
    feats = list(FEATURES)
    fig = plt.figure(figsize=(13, 7.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 8], wspace=0.02, left=0.02, right=0.86, bottom=0.30, top=0.89)
    axd, ax = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    dendrogram(link, orientation="left", no_labels=True, ax=axd, color_threshold=0, above_threshold_color=MUTED)
    axd.set_ylim(10 * len(order), 0)  # leaf i sits at y = 10 i + 5, aligned with heatmap row i
    axd.axis("off")
    zz = z[order]
    im = ax.imshow(zz, cmap=cmap, vmin=-2.5, vmax=2.5, aspect="auto")
    for i in range(zz.shape[0]):
        for j in range(zz.shape[1]):
            ax.text(j, i, f"{zz[i, j]:+.1f}", ha="center", va="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(len(feats)), [FEATURES[f][1] for f in feats], rotation=40, ha="right", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(order)), [f"{regions[i]}" for i in order], fontsize=9, color=INK)
    ax.yaxis.tick_right()
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    start = 0
    for t in dict.fromkeys(v[0] for v in FEATURES.values()):
        n = sum(1 for v in FEATURES.values() if v[0] == t)
        ax.text(start + (n - 1) / 2, -0.9, GROUP_TITLE[t], ha="center", color=MUTED, fontsize=9, weight="bold")
        if start:
            ax.axvline(start - 0.5, color="white", lw=4)
        start += n
    cb = fig.colorbar(im, cax=fig.add_axes([0.36, 0.075, 0.26, 0.016]), orientation="horizontal")
    cb.set_label("z-score across regions (orange = above the average region, blue = below)", color=MUTED, fontsize=8.5)
    cb.outline.set_visible(False)
    fig.suptitle("Musical profile of each region", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_pca(z, regions, types, out: Path):
    u, s, vt = np.linalg.svd(z - z.mean(0), full_matrices=False)
    pc = u[:, :2] * s[:2]
    var = s**2 / (s**2).sum()
    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    for t, c in TYPE_COLOR.items():
        m = np.array([x == t for x in types])
        ax.scatter(pc[m, 0], pc[m, 1], s=70, color=c, edgecolor="white", linewidth=1.5, zorder=3,
                   label="Han regions" if t == "Han" else "Minority regions")
    offs = {"Hakka": (7, -14, "left"), "Jiang–Han": (-7, 9, "right"), "Xiang": (7, 7, "left"), "Gan": (7, -13, "left"),
            "Southwest Plateau": (0, -17, "center"), "Min–Tai": (7, -13, "left"), "Southwest Multi-ethnic": (7, -4, "left")}
    for (x, y), r in zip(pc, regions):
        dx, dy, ha = offs.get(r, (7, 5, "left"))
        ax.annotate(r, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=8.5, color=INK)
    ax.axhline(0, color=GRID, lw=1)
    ax.axvline(0, color=GRID, lw=1)
    names = list(FEATURES)
    for k in (0, 1):
        top = np.argsort(-np.abs(vt[k]))[:3]
        txt = ", ".join(f"{FEATURES[names[i]][1].lower()} ({vt[k][i]:+.2f})" for i in top)
        fig.text(0.02, 0.045 - 0.032 * k, f"PC{k + 1} drivers: {txt}", fontsize=8, color=MUTED)
    ax.set_xlabel(f"PC1 ({var[0] * 100:.0f}% of the variation)", color=MUTED, fontsize=9)
    ax.set_ylabel(f"PC2 ({var[1] * 100:.0f}%)", color=MUTED, fontsize=9)
    style(ax)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(GRID)
    ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, loc="upper right")
    fig.suptitle("Where the regions sit on the main two dimensions", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0.09, 1, 0.95))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)
    return var, vt


def plot_stability(co, regions, order, k, mantel_txt, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0d2f5c"])
    m = co[np.ix_(order, order)] * 100
    fig, ax = plt.subplots(figsize=(8.6, 7))
    im = ax.imshow(m, cmap=cmap, vmin=0, vmax=100)
    for i in range(len(order)):
        for j in range(len(order)):
            if i != j:
                ax.text(j, i, f"{m[i, j]:.0f}", ha="center", va="center", fontsize=7.5,
                        color="white" if m[i, j] > 55 else INK)
    names = [regions[i] for i in order]
    ax.set_xticks(range(len(order)), names, rotation=45, ha="right", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(order)), names, fontsize=8.5, color=INK)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label(f"% of 1,000 resamples in the same cluster (k = {k})", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle("Which regions are reliably similar?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.94, textwrap.fill(mantel_txt, 105), color=MUTED, fontsize=8.5, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.81))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3, help="number of clusters")
    ap.add_argument("--out", default=str(OUT_ROOT / "profiles"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    d, regions = load()
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    types = [rec[rec.region_en == r].region_type.iloc[0] for r in regions]
    placed = rec[rec.geo_level.isin(["county", "prefecture"])]
    lon = np.array([placed[placed.region_en == r].lon.median() for r in regions])
    lat = np.array([placed[placed.region_en == r].lat.median() for r in regions])
    dg = haversine(lon, lat)

    gs = group_sums(d, regions)
    m = means(gs)
    z = zscore(m)
    dm = squareform(pdist(z))
    link = linkage(z, "ward")
    order = leaves_list(link)
    lab = fcluster(link, a.k, "maxclust")

    # bootstrap: resample groups within each region, redo z-scores, distances, clusters, Mantel
    rng = np.random.default_rng(0)
    co = np.zeros((len(regions),) * 2)
    boot_r = []
    for _ in range(N_BOOT):
        zb = zscore(means(gs, rng))
        lb = fcluster(linkage(zb, "ward"), a.k, "maxclust")
        co += lb[:, None] == lb[None]
        boot_r.append(mantel(squareform(pdist(zb)), dg))
    co /= N_BOOT
    r_obs = mantel(dm, dg)
    perm = np.array([mantel(dm, dg[np.ix_(p, p)]) for p in (rng.permutation(len(regions)) for _ in range(9999))])
    p_val = float((np.sum(perm >= r_obs) + 1) / (len(perm) + 1))
    lo, hi = np.percentile(boot_r, [2.5, 97.5])
    # robustness: Han regions only (the Han / minority split alone could create a west-east gradient)
    han = [i for i, t in enumerate(types) if t == "Han"]
    r_han = mantel(dm[np.ix_(han, han)], dg[np.ix_(han, han)])
    perm_han = np.array([mantel(dm[np.ix_(han, han)], dg[np.ix_(han, han)][np.ix_(p, p)])
                         for p in (rng.permutation(len(han)) for _ in range(9999))])
    p_han = float((np.sum(perm_han >= r_han) + 1) / (len(perm_han) + 1))
    boot_han = []
    for _ in range(300):
        zb = zscore(means(gs, rng))
        boot_han.append(mantel(squareform(pdist(zb))[np.ix_(han, han)], dg[np.ix_(han, han)]))
    han_txt = (f"Han regions only ({len(han)}): r = {r_han:.2f}, permutation p = {p_han:.3f}, resampling 95% interval "
               f"{np.percentile(boot_han, 2.5):.2f} to {np.percentile(boot_han, 97.5):.2f}.")
    mantel_txt = (f"Musical vs geographic distance between regions: Spearman r = {r_obs:.2f} "
                  f"(permutation p = {p_val:.3f}; resampling 95% interval {lo:.2f} to {hi:.2f}, median {np.median(boot_r):.2f}). "
                  + han_txt)

    prof = pd.DataFrame(m, index=regions, columns=list(FEATURES))
    zdf = pd.DataFrame(z, index=regions, columns=[f"z_{f}" for f in FEATURES])
    pd.concat([prof, zdf], axis=1).assign(cluster=lab, region_type=types, lon=lon, lat=lat).to_csv(out / "region_profile.csv")
    pd.DataFrame(co, index=regions, columns=regions).round(3).to_csv(out / "pair_stability.csv")
    with open(out / "region_signatures.md", "w") as f:
        f.write("# Region signatures (features with |z| >= 1 against the average region)\n\n")
        for i, r in enumerate(regions):
            f.write(f"- **{r}**: {signature(pd.Series(z[i], index=list(FEATURES)))}\n")
    plot_heatmap(z, regions, order, link, out / "fig_profile_heatmap.png", lab)
    var, vt = plot_pca(z, regions, types, out / "fig_region_map.png")
    plot_stability(co, regions, order, a.k, mantel_txt, out / "fig_pair_stability.png")

    print(f"{len(regions)} regions, {len(FEATURES)} features, {len(d)} recordings")
    for c in range(1, a.k + 1):
        mem = [regions[i] for i in order if lab[i] == c]
        idx = [i for i in range(len(regions)) if lab[i] == c]
        within = np.mean([co[i, j] for i in idx for j in idx if i < j]) if len(idx) > 1 else np.nan
        print(f"cluster {c} (mean within-cluster stability {within:.2f}): {', '.join(mem)}")
    iu = np.triu_indices(len(regions), 1)
    pairs = sorted(zip(co[iu], [regions[i] for i in iu[0]], [regions[j] for j in iu[1]]), reverse=True)
    print("most stable pairs:", "; ".join(f"{x} + {y} ({s:.2f})" for s, x, y in pairs[:5]))
    print("PCA variance explained:", np.round(var[:3], 2).tolist())
    print(mantel_txt)
    print(open(out / "region_signatures.md").read())
    print("outputs ->", out)


if __name__ == "__main__":
    main()
