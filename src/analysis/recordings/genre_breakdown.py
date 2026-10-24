"""
Genre breakdown: how do the musical measures, and the region classifier, vary by genre?

Genre is the `genre` column (284 labels in the corpus; 12 have >= 15 recordings among the 1,178 used here). Most genres belong to
one region (花儿, 咸水歌, 维吾尔民歌, 恒春民谣, 长调, 信天游, 二人转小帽 are 100% one region), so for them genre and region cannot
be told apart. Only 小调, 山歌 and 号子 occur across many regions ("pan-regional": >= 5 regions with >= 3 recordings, no region
above 50%); a genre effect with region held fixed can be estimated for these three only.

  A. Composition: which regions each genre comes from.
  B. Profile: the 12 region-profile features (see region_profiles.py) per genre, as z-scores across the genres.
  C. Region or genre? For the three pan-regional genres: adjusted R2 of each feature explained by region alone, genre alone, and
     both; the gain from adding genre to region and from adding region to genre (group-bootstrap intervals).
  D. Genre effects with region held fixed: 山歌 and 号子 against 小调 (regression with region fixed effects, outcome in standard
     deviations), group-bootstrap intervals.
  E. The region classifier by genre: recall per genre (out-of-fold predictions of the best model, data/analysis/recordings/classifier).
  F. Is genre itself predictable from the music (strict protocol, as in region_classifier.py)? Compared with guessing from the
     region alone (the commonest genre among training recordings of the same region) and the majority class.

Intervals resample whole groups (`group_id`: channel or singer). Limits: 3 pan-regional genres; thin genres (15-25 recordings);
genre labels come from titles and descriptions, are applied unevenly and overlap (民歌 is generic); region is a coarse control;
automatic measures. Exploratory only.
Run (from the repo root, after region_classifier.py):  python src/analysis/recordings/genre_breakdown.py [--out data/analysis/recordings/genre]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from region_classifier import SET_A, SET_B, confusion, load, macro_f1, oof, score, splits
from region_profiles import FEATURES
from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, style

BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
MIN_N = 15
N_BOOT = 500


def genre_table(d: pd.DataFrame) -> pd.DataFrame:
    ct = pd.crosstab(d.genre, d.region_en)
    rows = []
    for g, row in ct.iterrows():
        n = row.sum()
        if n >= MIN_N:
            rows.append({"genre": g, "n": int(n), "regions_with_3plus": int((row >= 3).sum()), "top_region": row.idxmax(),
                         "top_region_share": row.max() / n})
    t = pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)
    t["pan_regional"] = (t.regions_with_3plus >= 5) & (t.top_region_share <= 0.5)
    return t, ct


# ---------------------------------------------------------------- OLS helpers
def fit(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    return beta, float(res @ res)


def adj_r2(X, y):
    _, sse = fit(X, y)
    sst = float(((y - y.mean()) ** 2).sum())
    n, p = len(y), np.linalg.matrix_rank(X) - 1
    return 1 - (sse / (n - p - 1)) / (sst / (n - 1))


def dummies(s: pd.Series, levels=None):
    levels = levels or sorted(s.unique())
    return np.column_stack([(s.to_numpy() == l).astype(float) for l in levels]), levels


def partition_and_effects(sub: pd.DataFrame, pan: list[str], feats: list[str], rng):
    ref = "小调"
    others = [g for g in pan if g != ref]
    out_part, out_eff = [], []
    groups = sub.group_id.to_numpy()
    uniq = pd.factorize(groups)[0]
    G = uniq.max() + 1
    members = [np.flatnonzero(uniq == k) for k in range(G)]

    def stats(idx, f):
        s = sub.iloc[idx]
        y = s[f].to_numpy(float)
        ok = np.isfinite(y)
        s, y = s[ok], y[ok]
        y = (y - y.mean()) / y.std()
        Xr, _ = dummies(s.region_en)
        Xg, _ = dummies(s.genre, pan)
        r_r, r_g, r_b = adj_r2(Xr, y), adj_r2(Xg, y), adj_r2(np.hstack([Xr, Xg]), y)
        Xe = np.hstack([Xr, np.column_stack([(s.genre.to_numpy() == g).astype(float) for g in others])])
        beta, _ = fit(Xe, y)
        return r_r, r_g, r_b, beta[-len(others):]

    allidx = np.arange(len(sub))
    for f in feats:
        pt = stats(allidx, f)
        boots = []
        for _ in range(N_BOOT):
            idx = np.concatenate([members[k] for k in rng.integers(0, G, G)])
            boots.append(stats(idx, f))
        d_gen = np.array([b[2] - b[0] for b in boots])
        d_reg = np.array([b[2] - b[1] for b in boots])
        out_part.append({"feature": f, "label": FEATURES[f][1], "adjR2_region": pt[0], "adjR2_genre": pt[1], "adjR2_both": pt[2],
                         "gain_from_genre": pt[2] - pt[0], "gain_from_genre_lo": np.percentile(d_gen, 2.5),
                         "gain_from_genre_hi": np.percentile(d_gen, 97.5), "gain_from_region": pt[2] - pt[1],
                         "gain_from_region_lo": np.percentile(d_reg, 2.5), "gain_from_region_hi": np.percentile(d_reg, 97.5)})
        bco = np.array([b[3] for b in boots])
        for i, g in enumerate(others):
            out_eff.append({"feature": f, "label": FEATURES[f][1], "genre": g, "vs": ref, "effect_sd": pt[3][i],
                            "lo": np.percentile(bco[:, i], 2.5), "hi": np.percentile(bco[:, i], 97.5)})
    return pd.DataFrame(out_part), pd.DataFrame(out_eff)


# ---------------------------------------------------------------- recall by genre
def recall_by_genre(d: pd.DataFrame, oofp: pd.DataFrame, genres: list[str], rng) -> pd.DataFrame:
    m = d[["item_id", "genre", "group_id"]].merge(oofp, on="item_id")
    m["ok"] = (m.true == m.predicted).astype(float)
    rows = []
    for g in genres:
        s = m[m.genre == g]
        a = s.groupby("group_id").ok.agg(["sum", "count"])
        idx = rng.integers(0, len(a), (N_BOOT, len(a)))
        bt = a["sum"].to_numpy()[idx].sum(1) / a["count"].to_numpy()[idx].sum(1)
        rows.append({"genre": g, "n": len(s), "recall": s.ok.mean(), "lo": np.percentile(bt, 2.5), "hi": np.percentile(bt, 97.5)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- figures
def plot_composition(ct, table, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0d2f5c"])
    gen = table.genre.tolist()
    sub = ct.loc[gen]
    reg_order = sub.sum().sort_values(ascending=False).index.tolist()
    M = (sub[reg_order].div(sub.sum(1), axis=0) * 100).to_numpy()
    fig, ax = plt.subplots(figsize=(11, 5.8))
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j] >= 8:
                ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7.5, color="white" if M[i, j] > 55 else INK)
    ax.set_xticks(range(len(reg_order)), reg_order, rotation=45, ha="right", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(gen)), [f"{g}  (n={n})" for g, n in zip(table.genre, table.n)], fontsize=9.5, color=INK)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("% of the genre's recordings", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle("Which regions does each genre come from?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_profile(d, table, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", [BLUE, "#f1f0ec", ORANGE])
    gen = table.genre.tolist()
    m = np.array([d[d.genre == g][SET_A].mean().to_numpy() for g in gen])
    z = (m - m.mean(0)) / m.std(0)
    fig, ax = plt.subplots(figsize=(11, 5.9))
    im = ax.imshow(z, cmap=cmap, vmin=-2.5, vmax=2.5, aspect="auto")
    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            ax.text(j, i, f"{z[i, j]:+.1f}", ha="center", va="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(len(SET_A)), [FEATURES[f][1] for f in SET_A], rotation=40, ha="right", fontsize=8.5, color=INK)
    labels = [f"{r.genre}  (n={r.n}; {'across regions' if r.pan_regional else f'{r.top_region_share:.0%} ' + r.top_region})"
              for r in table.itertuples()]
    ax.set_yticks(range(len(gen)), labels, fontsize=9, color=INK)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("z-score across these genres (orange above, blue below)", color=MUTED, fontsize=8.5)
    cb.outline.set_visible(False)
    fig.suptitle("Musical profile of each genre", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Single-region genres mirror their region's profile; only the top three occur across regions.",
             color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_partition(p: pd.DataFrame, out: Path, n: int):
    s = p.sort_values("adjR2_region")
    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    y = np.arange(len(s))
    for col, c, lab, dy in (("adjR2_region", BLUE, "region alone", 0.2), ("adjR2_genre", ORANGE, "genre alone", 0.0),
                            ("adjR2_both", GRAY, "region + genre", -0.2)):
        ax.scatter(s[col], y + dy, s=46, color=c, edgecolor="white", linewidth=1.2, label=lab, zorder=3)
    ax.set_yticks(y, s.label, fontsize=9, color=INK)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel("Adjusted R-squared: share of the feature's variation explained", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    ax.legend(frameon=False, fontsize=8.5, labelcolor=MUTED, loc="lower right")
    style(ax)
    fig.suptitle("Region or genre? (小调, 山歌 and 号子 only)", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, f"{n} recordings across 15 regions. Adjusted for the number of groups fitted.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_effects(e: pd.DataFrame, out: Path):
    feats = (e[e.genre == e.genre.iloc[0]].assign(a=lambda x: x.effect_sd.abs()).sort_values("a").label.tolist())
    genres = e.genre.unique().tolist()
    fig, axs = plt.subplots(1, len(genres), figsize=(5.6 * len(genres), 5.8), sharey=True)
    axs = np.atleast_1d(axs)
    y = {f: i for i, f in enumerate(feats)}
    for ax, g in zip(axs, genres):
        s = e[e.genre == g]
        yy = np.array([y[l] for l in s.label])
        sig = (np.sign(s.lo) == np.sign(s.hi)).to_numpy()
        ax.hlines(yy, s.lo, s.hi, color=BLUE, lw=2, zorder=2)
        ax.scatter(s.effect_sd[sig], yy[sig], s=52, color=BLUE, edgecolor="white", linewidth=1.2, zorder=3)
        ax.scatter(s.effect_sd[~sig], yy[~sig], s=52, color="white", edgecolor=BLUE, linewidth=1.8, zorder=3)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_title(f"{g} vs 小调", color=INK, fontsize=10.5, loc="left")
        ax.set_xlabel("Difference within the same region (standard deviations)", color=MUTED, fontsize=8.5)
        ax.grid(axis="x", color=GRID)
        style(ax)
    axs[0].set_yticks(range(len(feats)), feats, fontsize=9, color=INK)
    fig.suptitle("What changes with genre when the region is held fixed?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Filled = interval excludes zero (95%, resampling channels/singers); hollow = it does not.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_recall(r: pd.DataFrame, table: pd.DataFrame, overall: float, out: Path):
    r = r.merge(table[["genre", "pan_regional"]], on="genre").sort_values("recall")
    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    y = np.arange(len(r))
    for pan, c in ((True, BLUE), (False, GRAY)):
        s = r[r.pan_regional == pan]
        yy = y[(r.pan_regional == pan).to_numpy()]
        ax.hlines(yy, s.lo, s.hi, color=c, lw=2, zorder=2)
        ax.scatter(s.recall, yy, s=52, color=c, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks(y, [f"{g}  (n={n})" for g, n in zip(r.genre, r.n)], fontsize=9.5, color=INK)
    ax.axvline(overall, color=MUTED, ls=(0, (4, 3)), lw=1)
    ax.text(overall, len(r) - 0.4, " overall", color=MUTED, fontsize=8, va="bottom")
    ax.set_xlabel("Share of the genre's recordings whose region is predicted correctly", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    fig.suptitle("Is the region easier to predict for some genres?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Blue = genre found across many regions; gray = genre confined to one or two regions.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_ROOT / "genre"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    pd.set_option("display.width", 220)

    d = load().merge(pd.read_csv(ROOT / "metadata" / "recordings.csv")[["item_id", "genre"]], on="item_id")
    for f in SET_A:  # winsorise
        d[f] = d[f].clip(*d[f].quantile([0.01, 0.99]))
    table, ct = genre_table(d)
    table.to_csv(out / "genre_summary.csv", index=False)
    print(f"{len(d)} recordings, {d.genre.nunique()} genres; {len(table)} with >= {MIN_N}")
    print(table.round(2).to_string(index=False))
    pan = table[table.pan_regional].genre.tolist()
    assert "小调" in pan, pan
    plot_composition(ct, table, out / "fig_genre_by_region.png")
    plot_profile(d, table, out / "fig_genre_profile.png")

    sub = d[d.genre.isin(pan)].reset_index(drop=True)
    part, eff = partition_and_effects(sub, pan, SET_A, rng)
    part.to_csv(out / "region_vs_genre.csv", index=False)
    eff.to_csv(out / "genre_effects.csv", index=False)
    plot_partition(part, out / "fig_region_vs_genre.png", len(sub))
    plot_effects(eff, out / "fig_genre_effects.png")
    print(part.round(3)[["label", "adjR2_region", "adjR2_genre", "adjR2_both", "gain_from_genre", "gain_from_genre_lo",
                         "gain_from_genre_hi", "gain_from_region"]].sort_values("gain_from_genre", ascending=False).to_string(index=False))
    sig = eff[np.sign(eff.lo) == np.sign(eff.hi)]
    print(sig.round(2)[["genre", "label", "effect_sd", "lo", "hi"]].sort_values(["genre", "effect_sd"]).to_string(index=False))

    oofp = pd.read_csv(OUT_ROOT / "classifier" / "oof_predictions.csv")
    rb = recall_by_genre(d, oofp, table.genre.tolist(), rng)
    rb.to_csv(out / "recall_by_genre.csv", index=False)
    overall = float((oofp.true == oofp.predicted).mean())
    plot_recall(rb, table, overall, out / "fig_classifier_by_genre.png")
    print(f"overall region accuracy {overall:.3f}")
    print(rb.round(3).to_string(index=False))

    # F. is genre predictable? strict protocol, 3 pan-regional genres
    d3 = d[d.genre.isin(pan)].reset_index(drop=True)
    d3["region_orig"] = d3.region_en
    d3["region_en"] = d3.genre
    classes = np.array(sorted(pan))
    y = np.searchsorted(classes, d3.region_en.to_numpy())
    rows = []
    for name, cols, kind in (("music: B + LR", SET_B, "LR"), ("music: B + GBM", SET_B, "GBM"), ("music: A + LR", SET_A, "LR")):
        P = oof(d3, cols, kind, classes)
        r, pcs = score(d3, P, classes, rng, name)
        r.update({f"f1_{c}": v for c, v in zip(classes, pcs[0])})
        rows.append(r)
    base = np.zeros(len(d3), int)
    for f, tr, te in splits(d3):
        prior = pd.crosstab(d3.region_orig.iloc[tr], d3.genre.iloc[tr])
        common = {r: np.searchsorted(classes, prior.loc[r].idxmax()) for r in prior.index}
        fallback = np.searchsorted(classes, d3.genre.iloc[tr].value_counts().idxmax())
        base[te] = [common.get(r, fallback) for r in d3.region_orig.iloc[te]]
    pb = np.eye(len(classes))[base]
    r, pcs = score(d3, pb, classes, rng, "region only (commonest genre in the region)")
    r.update({f"f1_{c}": v for c, v in zip(classes, pcs[0])})
    rows.append(r)
    pm = np.eye(len(classes))[np.full(len(d3), np.bincount(y).argmax())]
    r, _ = score(d3, pm, classes, rng, "majority genre")
    rows.append(r)
    gp = pd.DataFrame(rows)
    gp.to_csv(out / "genre_predictability.csv", index=False)
    print(f"genre prediction among {pan}: n = {len(d3)}, counts {pd.Series(d3.genre).value_counts().to_dict()}")
    print(gp.round(3).to_string(index=False))
    print("outputs ->", out)


if __name__ == "__main__":
    main()
