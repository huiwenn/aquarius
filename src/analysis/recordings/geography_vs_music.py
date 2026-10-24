"""
Do musical distances follow geography?

Uses the 12 region-profile features (scales, intonation, rhythm, melody; see region_profiles.py) and asks four questions.

1. DISTANCE DECAY (recording level). Every pair of recordings with a precise place (county or prefecture level) gets a
   musical distance (Euclidean, on winsorised z-scored features) and a distance in km. Mean musical distance is shown per
   distance band, for pairs inside the same region and pairs from different regions. Pairs from the same channel or singer
   (`group_id`) are excluded, so one performer cannot make near pairs look alike. Intervals come from resampling whole
   groups (pair-level "pigeonhole" bootstrap, 1,000 resamples).
2. WHICH MUSIC FOLLOWS GEOGRAPHY (region level). Mantel test (Spearman r between musical and geographic distance of the 15
   regions, one-sided permutation p, 9,999 permutations) for all features, each of the four families and each single
   feature, plus a leave-one-region-out range. Bonferroni threshold for the 17 tests.
3. GRADIENTS (recording level). Spearman correlation of each feature with longitude and latitude, with group-bootstrap
   intervals, for all regions and for Han regions only (the Han / minority split alone makes a west-east gradient).
4. EXCEPTIONS (region level). Region pairs that are musically much closer or farther than their distance predicts
   (difference of rank percentiles), with the share of 1,000 resamples in which the pair keeps its sign.

Limits: the 15 regions are drawn geographically, so some link to geography is built in; place is known precisely for only
701 of 1,335 recordings (some regions have only 20-30); region centres are the median place of a region's recordings, and
Xinjiang, Tibet and the Steppe are huge; features are correlated and equally weighted; correlation is not diffusion or
contact. Exploratory only.
Run (from the repo root, after region_profiles.py):  python src/analysis/recordings/geography_vs_music.py [--out data/analysis/recordings/geography]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.stats import rankdata

from region_profiles import FEATURES, GROUP_TITLE, group_sums, haversine, load, means, zscore
from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, style

BLUE, ORANGE = "#2a78d6", "#eb6834"
N_BOOT, N_PERM = 1000, 9999
EDGES = np.array([0, 50, 150, 400, 800, 1500, 3000, 6000.0])
BAND_LABELS = ["< 50", "50-150", "150-400", "400-800", "800-1,500", "1,500-3,000", "> 3,000"]
FAMILIES = {t: [c for c, v in FEATURES.items() if v[0] == t] for t in dict.fromkeys(v[0] for v in FEATURES.values())}


def recordings() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "metadata" / "recordings.csv")[["item_id", "region_en", "region_type", "group_id", "lon", "lat",
                                                          "geo_level"]]
    for t, cols in FAMILIES.items():
        d = d.merge(pd.read_csv(OUT_ROOT / t / "per_recording.csv")[["item_id"] + cols], on="item_id", how="inner")
    d = d.dropna(subset=list(FEATURES))
    d = d[d.geo_level.isin(["county", "prefecture"])].reset_index(drop=True)
    for f in FEATURES:  # winsorise at 1/99% so a few transcription outliers cannot dominate distances
        d[f] = d[f].clip(*d[f].quantile([0.01, 0.99]))
    return d


# ---------------------------------------------------------------- 1. distance decay
def distance_decay(d: pd.DataFrame, rng) -> pd.DataFrame:
    z = ((d[list(FEATURES)] - d[list(FEATURES)].mean()) / d[list(FEATURES)].std()).to_numpy()
    iu = np.triu_indices(len(d), 1)
    dm = pdist(z)
    km = haversine(d.lon.to_numpy(), d.lat.to_numpy())[iu]
    g = pd.factorize(d.group_id)[0]
    G, B = g.max() + 1, len(EDGES) - 1
    gi, gj = g[iu[0]], g[iu[1]]
    same_region = (d.region_en.to_numpy()[iu[0]] == d.region_en.to_numpy()[iu[1]])
    band = np.clip(np.digitize(km, EDGES) - 1, 0, B - 1)
    keep = gi != gj
    out, tables = [], {}
    for name, m in (("same region", keep & same_region), ("different regions", keep & ~same_region), ("all pairs", keep)):
        idx = (gi[m] * G + gj[m]) * B + band[m]
        S = np.bincount(idx, weights=dm[m], minlength=G * G * B).reshape(G, G, B)
        C = np.bincount(idx, minlength=G * G * B).reshape(G, G, B).astype(float)
        tables[name] = (S, C)

    def est(S, C, w):
        num = (np.tensordot(w, S, axes=(0, 0)) * w[:, None]).sum(0)
        den = (np.tensordot(w, C, axes=(0, 0)) * w[:, None]).sum(0)
        return np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)

    ones = np.ones(G)
    boots = {k: [] for k in tables}
    for _ in range(N_BOOT):
        w = np.bincount(rng.integers(0, G, G), minlength=G).astype(float)
        for k, (S, C) in tables.items():
            boots[k].append(est(S, C, w))
    for k, (S, C) in tables.items():
        pt, bt = est(S, C, ones), np.array(boots[k])
        n = C.sum((0, 1))
        for b in range(B):
            ok = np.isfinite(bt[:, b])
            out.append({"pairs": k, "band_km": BAND_LABELS[b], "band": b, "n_pairs": int(n[b]), "mean_distance": pt[b],
                        "lo": np.percentile(bt[ok, b], 2.5) if ok.sum() > 50 else np.nan,
                        "hi": np.percentile(bt[ok, b], 97.5) if ok.sum() > 50 else np.nan})
    return pd.DataFrame(out)


# ---------------------------------------------------------------- 2. Mantel by feature
def mantel_tests(prof: pd.DataFrame, dg: np.ndarray, rng) -> pd.DataFrame:
    R = len(prof)
    iu = np.triu_indices(R, 1)
    perms = np.array([rng.permutation(R) for _ in range(N_PERM)])
    rg = rankdata(dg[perms[:, iu[0]], perms[:, iu[1]]], axis=1)
    rg = (rg - rg.mean(1, keepdims=True))
    rg /= np.linalg.norm(rg, axis=1, keepdims=True)
    gtrue = rankdata(dg[iu])

    def dist(df, cols):
        z = zscore(df[cols].to_numpy())
        return pdist(z)

    def corr(x, y):
        a, b = rankdata(x) - rankdata(x).mean(), rankdata(y) - rankdata(y).mean()
        return float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))

    tests = [("All 12 features", "all", list(FEATURES))]
    tests += [(f"{GROUP_TITLE[t]} (family)", "family", c) for t, c in FAMILIES.items()]
    tests += [(FEATURES[c][1], GROUP_TITLE[FEATURES[c][0]], [c]) for c in FEATURES]
    rows = []
    for name, kind, cols in tests:
        x = dist(prof, cols)
        r = corr(x, dg[iu])
        rx = rankdata(x) - rankdata(x).mean()
        rx = rx / np.linalg.norm(rx)
        p = float((1 + (rg @ rx >= r).sum()) / (N_PERM + 1))
        loo = []
        for k in range(R):
            keepi = [i for i in range(R) if i != k]
            sub, dgs = prof.iloc[keepi], dg[np.ix_(keepi, keepi)]
            loo.append(corr(dist(sub, cols), dgs[np.triu_indices(R - 1, 1)]))
        rows.append({"test": name, "kind": kind, "r": r, "p_perm": p, "bonferroni_sig": p < 0.05 / len(tests),
                     "loo_min": min(loo), "loo_max": max(loo), "loo_drop_min": prof.index[int(np.argmin(loo))]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 3. gradients
def gradients(d: pd.DataFrame, rng) -> pd.DataFrame:
    rows = []
    for label, sub in (("all regions", d), ("Han regions only", d[d.region_type == "Han"].reset_index(drop=True))):
        X = np.column_stack([rankdata(sub[f]) for f in FEATURES])
        Y = np.column_stack([rankdata(sub.lon), rankdata(sub.lat)])
        g = pd.factorize(sub.group_id)[0]
        G = g.max() + 1

        def wcorr(w):
            sw = w.sum()
            mx, my = (w @ X) / sw, (w @ Y) / sw
            Xc, Yc = X - mx, Y - my
            cov = (Xc * w[:, None]).T @ Yc / sw
            vx = ((Xc**2) * w[:, None]).sum(0) / sw
            vy = ((Yc**2) * w[:, None]).sum(0) / sw
            return cov / np.sqrt(np.outer(vx, vy))

        pt = wcorr(np.ones(len(sub)))
        bt = np.array([wcorr(np.bincount(rng.integers(0, G, G), minlength=G)[g].astype(float)) for _ in range(N_BOOT)])
        lo, hi = np.percentile(bt, 2.5, axis=0), np.percentile(bt, 97.5, axis=0)
        for i, f in enumerate(FEATURES):
            for j, axis in enumerate(("longitude", "latitude")):
                rows.append({"sample": label, "n": len(sub), "feature": f, "label": FEATURES[f][1], "axis": axis,
                             "rho": pt[i, j], "lo": lo[i, j], "hi": hi[i, j]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 4. exceptions
def exceptions(prof: pd.DataFrame, dg: np.ndarray, rng) -> pd.DataFrame:
    regions = list(prof.index)
    R = len(regions)
    iu = np.triu_indices(R, 1)
    gkm = dg[iu]

    def resid(z):
        dm = pdist(z)
        return rankdata(dm) / len(dm) - rankdata(gkm) / len(gkm)

    z = zscore(prof.to_numpy())
    res = resid(z)
    d, regs = load()
    gs = group_sums(d, regs)
    assert regs == regions
    boots = np.array([resid(zscore(means(gs, rng))) for _ in range(N_BOOT)])
    stab = (np.sign(boots) == np.sign(res)).mean(0)
    return pd.DataFrame({"region_a": [regions[i] for i in iu[0]], "region_b": [regions[j] for j in iu[1]], "km": gkm,
                         "musical_distance": pdist(z), "residual": res, "sign_stability": stab}).sort_values("residual")


# ---------------------------------------------------------------- figures
def plot_decay(t: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    x = np.arange(len(BAND_LABELS))
    for k, c, lab in (("same region", BLUE, "same region"), ("different regions", ORANGE, "different regions")):
        s = t[t.pairs == k].sort_values("band").dropna(subset=["mean_distance"])
        xs = s.band.to_numpy()
        ax.fill_between(xs, s.lo, s.hi, color=c, alpha=0.15, lw=0)
        ax.plot(xs, s.mean_distance, color=c, lw=2, marker="o", ms=6, mfc=c, mec="white", mew=1.5)
        ax.text(xs[-1] + 0.12, s.mean_distance.iloc[-1], lab, color=INK, fontsize=9, va="center")
    ax.axhline(t[t.pairs == "all pairs"].mean_distance.mean(), color=MUTED, ls=(0, (4, 3)), lw=1)
    ax.set_xticks(x, BAND_LABELS, fontsize=9, color=MUTED)
    ax.set_xlim(-0.3, len(x) + 0.9)
    ax.set_xlabel("Distance between the two recordings' places (km)", color=MUTED, fontsize=9)
    ax.set_ylabel("Mean musical distance (z-score units)", color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID)
    style(ax)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(GRID)
    fig.suptitle("Do recordings that are closer together sound more alike?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.915, "Band = 95% interval resampling channels/singers; pairs from the same channel or singer excluded. "
             "Dashed line = average of all pairs.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_mantel(m: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    y, ys, labels = 0.0, [], []
    for kind in ("all", "family", *GROUP_TITLE.values()):
        s = m[m.kind == kind]
        if not len(s):
            continue
        y += 0.6
        if kind in GROUP_TITLE.values():
            ax.annotate(kind, xy=(0, y - 0.3), xycoords=("axes fraction", "data"), xytext=(2, 0), textcoords="offset points",
                        color=MUTED, fontsize=8, weight="bold", va="center")
            y += 0.4
        for r in s.itertuples():
            ax.hlines(y, r.loo_min, r.loo_max, color=BLUE, lw=2, zorder=2)
            ax.scatter(r.r, y, s=56, zorder=3, color=BLUE if r.bonferroni_sig else "white", edgecolor=BLUE, linewidth=1.8)
            ys.append(y)
            labels.append(r.test)
            y += 1
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_yticks(ys, labels, fontsize=9, color=INK)
    ax.set_ylim(y, 0)
    ax.set_xlabel("Spearman r between musical and geographic distance of the 15 regions", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    fig.suptitle("Which kinds of music follow geography?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Filled dot = significant after Bonferroni (17 tests); hollow = not. Line = range when each region "
             "is left out in turn.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_gradients(g: pd.DataFrame, out: Path):
    order = (g[(g["sample"] == "all regions") & (g.axis == "longitude")].assign(a=lambda x: x.rho.abs())
             .sort_values("a", ascending=False).label.tolist())
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.8), sharey=True)
    y = {lab: len(order) - 1 - i for i, lab in enumerate(order)}
    for ax, axis in zip(axs, ("longitude", "latitude")):
        for sample, c, dy, filled in (("all regions", BLUE, 0.14, True), ("Han regions only", ORANGE, -0.14, True)):
            s = g[(g["sample"] == sample) & (g.axis == axis)]
            yy = np.array([y[l] + dy for l in s.label])
            ax.hlines(yy, s.lo, s.hi, color=c, lw=1.8, zorder=2)
            ax.scatter(s.rho, yy, s=34, color=c, edgecolor="white", linewidth=1, zorder=3, label=sample)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_xlabel(f"Spearman correlation with {axis} ({'+ = higher further east' if axis == 'longitude' else '+ = higher further north'})",
                      color=MUTED, fontsize=8.5)
        ax.grid(axis="x", color=GRID)
        style(ax)
    axs[0].set_yticks([y[l] for l in order], order, color=INK, fontsize=9)
    axs[0].legend(frameon=False, fontsize=8.5, labelcolor=MUTED, loc="lower left")
    fig.suptitle("West-east and south-north gradients in the music", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Recordings with a precise place. Line = 95% interval resampling channels/singers.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_pairs(e: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(e.km, e.musical_distance, s=30, color="#b9b8b1", edgecolor="white", linewidth=0.8, zorder=2)
    k = np.polyfit(e.km, e.musical_distance, 1)
    xs = np.linspace(e.km.min(), e.km.max(), 50)
    ax.plot(xs, np.polyval(k, xs), color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1)
    for sub, c, dy in ((e.head(5), BLUE, 7), (e.tail(5), ORANGE, 7)):
        ax.scatter(sub.km, sub.musical_distance, s=44, color=c, edgecolor="white", linewidth=1.2, zorder=3)
        for r in sub.itertuples():
            name = f"{r.region_a} + {r.region_b}"
            dx, dyy, ha = {"Northeast Plain + Southwest Plateau": (-7, 8, "right"), "Hakka + Northwest Plateau": (7, -15, "left"),
                           "Northeast Plain + Yue": (8, 5, "left"), "Hakka + Southwest Plateau": (-8, -3, "right")}.get(name, (6, dy, "left"))
            ax.annotate(name, (r.km, r.musical_distance), xytext=(dx, dyy), textcoords="offset points", ha=ha,
                        fontsize=7.5, color=INK)
    ax.set_xlabel("Distance between region centres (km)", color=MUTED, fontsize=9)
    ax.set_ylabel("Musical distance between regions (z-score units)", color=MUTED, fontsize=9)
    ax.grid(color=GRID)
    style(ax)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(GRID)
    fig.suptitle("Region pairs that break the pattern", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Blue = musically much closer than their distance predicts; orange = musically farther than expected "
             "(5 each, by rank).", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_ROOT / "geography"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    pd.set_option("display.width", 220)

    d = recordings()
    print(f"{len(d)} recordings with a precise place and all 12 measures, {d.group_id.nunique()} groups")
    decay = distance_decay(d, rng)
    decay.to_csv(out / "distance_decay.csv", index=False)
    plot_decay(decay, out / "fig_distance_decay.png")
    print(decay.pivot(index="band_km", columns="pairs", values="mean_distance").loc[BAND_LABELS].round(2).to_string())
    print(decay[decay.pairs == "all pairs"].set_index("band_km").loc[BAND_LABELS][["n_pairs", "mean_distance", "lo", "hi"]].round(2).to_string())

    prof = pd.read_csv(OUT_ROOT / "profiles" / "region_profile.csv", index_col=0)[list(FEATURES)]
    reg = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    placed = reg[reg.geo_level.isin(["county", "prefecture"])]
    dg = haversine(np.array([placed[placed.region_en == r].lon.median() for r in prof.index]),
                   np.array([placed[placed.region_en == r].lat.median() for r in prof.index]))
    mt = mantel_tests(prof, dg, rng)
    mt.to_csv(out / "mantel_tests.csv", index=False)
    plot_mantel(mt, out / "fig_mantel_by_feature.png")
    print(mt.round(3).to_string(index=False))

    gr = gradients(d, rng)
    gr.to_csv(out / "gradients.csv", index=False)
    plot_gradients(gr, out / "fig_gradients.png")
    sig = gr[(np.sign(gr.lo) == np.sign(gr.hi))]
    print(sig.round(2)[["sample", "axis", "label", "rho", "lo", "hi"]].sort_values(["sample", "axis", "rho"]).to_string(index=False))

    ex = exceptions(prof, dg, rng)
    ex.to_csv(out / "region_pair_residuals.csv", index=False)
    plot_pairs(ex, out / "fig_region_pairs.png")
    print(ex.head(6).round(2).to_string(index=False))
    print(ex.tail(6).round(2).to_string(index=False))
    print("outputs ->", out)


if __name__ == "__main__":
    main()
