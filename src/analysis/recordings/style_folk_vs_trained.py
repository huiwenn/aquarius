"""
Style as a proxy for time: does stage-style (民族唱法, "trained") singing differ from folk-style (原生态) singing?

Question (item 6 of the plan): does stage style flatten intonation and make rhythm more regular?
Pre-specified PRIMARY measures and predicted directions (fixed before looking):
  off_grid_local   trained LOWER   (closer to the piano grid, after removing slow pitch drift)
  tempo_variation  trained LOWER   (steadier speed)
  isochrony        trained HIGHER  (more evenly spaced notes)
Everything else (the other region-profile features, drift, mean deviation from the grid) is SECONDARY and exploratory;
there are 15 measures in all, so a few "significant" secondary results are expected by chance.

Four views of the same question, from strongest control to weakest sample:
  1. Pooled, region held fixed: regression with region fixed effects; trained, field and other against folk;
     outcomes in standard deviations; group-bootstrap intervals (group = channel or singer).
  2. Same channel: only channels that hold both folk and trained recordings (5; two hold nearly all of them), with channel
     fixed effects, so the recording chain is the same; stratified recording-level bootstrap.
  3. Same song: songs with both a folk and a trained version (18); mean trained-minus-folk difference per song,
     bootstrap over songs, sign test.
  4. By region: folk and trained means in the regions with at least 10 of each.

Not possible here: "composed" pieces are not in the analysis set (all 61 are outside `core`: orchestral or arranged); an
accompaniment control (the flag exists for one channel only); real dates (performance type is a STYLE proxy, not a date, so
this cannot show change over time).
Limits: trained recordings are often studio or stage recordings (cleaner audio, accompaniment), which can lower pitch-tracker
noise by themselves; trained singing comes mostly from a few channels; the same-song sample is tiny. Exploratory only.
Run (from the repo root):  python src/analysis/recordings/style_folk_vs_trained.py [--out data/analysis/recordings/style]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest

from genre_breakdown import dummies, fit
from region_classifier import SET_A, load
from region_profiles import FEATURES
from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, style

BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
N_BOOT = 1000
PRIMARY = {"off_grid_local": -1, "tempo_variation": -1, "isochrony": +1}  # predicted sign of (trained - folk)
EXTRA = {"drift_cents": "Pitch drift over the song", "mean_abs_dev": "Mean distance from the grid",
         "isochrony": "Evenly spaced notes"}
FEATS = list(PRIMARY) + [f for f in SET_A if f not in PRIMARY] + ["drift_cents", "mean_abs_dev"]
TYPES = ["原生态", "民族唱法", "field", "other"]


def label(f: str) -> str:
    return FEATURES[f][1] if f in FEATURES else EXTRA[f]


def prepare() -> pd.DataFrame:
    d = load().merge(pd.read_csv(ROOT / "metadata" / "recordings.csv")[["item_id", "performance_type"]], on="item_id")
    d = d.merge(pd.read_csv(OUT_ROOT / "intonation" / "per_recording.csv")[["item_id", "drift_cents"]], on="item_id", how="left")
    d = d[d.performance_type.isin(TYPES)].reset_index(drop=True)
    for f in FEATS:
        d[f] = d[f].clip(*d[f].quantile([0.01, 0.99]))
    return d


def zscores(d):
    return {f: (d[f].mean(), d[f].std()) for f in FEATS}


def pooled(d, f, mu_sd, idx):
    s = d.iloc[idx]
    y = s[f].to_numpy(float)
    ok = np.isfinite(y)
    s, y = s[ok], (y[ok] - mu_sd[0]) / mu_sd[1]
    Xr, _ = dummies(s.region_en)
    T = np.column_stack([(s.performance_type.to_numpy() == t).astype(float) for t in ("民族唱法", "field", "other")])
    beta, _ = fit(np.hstack([Xr, T]), y)
    return beta[-3:]


def view1(d, rng):
    ms = zscores(d)
    uniq = pd.factorize(d.group_id)[0]
    G = uniq.max() + 1
    members = [np.flatnonzero(uniq == k) for k in range(G)]
    rows = []
    for f in FEATS:
        pt = pooled(d, f, ms[f], np.arange(len(d)))
        bt = np.array([pooled(d, f, ms[f], np.concatenate([members[k] for k in rng.integers(0, G, G)])) for _ in range(N_BOOT)])
        for i, t in enumerate(("民族唱法", "field", "other")):
            rows.append({"view": "pooled, region fixed", "contrast": f"{t} vs 原生态", "feature": f, "label": label(f),
                         "effect_sd": pt[i], "lo": np.percentile(bt[:, i], 2.5), "hi": np.percentile(bt[:, i], 97.5)})
    return pd.DataFrame(rows)


def view2(d, rng, min_each=10):
    t = d[d.performance_type.isin(["原生态", "民族唱法"])]
    cnt = t.groupby(["group_id", "performance_type"]).size().unstack(fill_value=0)
    use = cnt[(cnt.min(axis=1) >= min_each)].index.tolist()
    s = t[t.group_id.isin(use)].reset_index(drop=True)
    ms = zscores(d)
    strata = [np.flatnonzero(((s.group_id == g) & (s.performance_type == p)).to_numpy()) for g in use for p in ("原生态", "民族唱法")]

    def est(idx, f):
        x = s.iloc[idx]
        y = x[f].to_numpy(float)
        ok = np.isfinite(y)
        x, y = x[ok], (y[ok] - ms[f][0]) / ms[f][1]
        Xg, _ = dummies(x.group_id.astype(str))
        T = (x.performance_type.to_numpy() == "民族唱法").astype(float)[:, None]
        return fit(np.hstack([Xg, T]), y)[0][-1]

    rows = []
    for f in FEATS:
        pt = est(np.arange(len(s)), f)
        bt = [est(np.concatenate([rng.choice(ix, len(ix)) for ix in strata]), f) for _ in range(N_BOOT)]
        rows.append({"view": f"same channel ({len(use)} channels)", "contrast": "民族唱法 vs 原生态", "feature": f, "label": label(f),
                     "effect_sd": pt, "lo": np.percentile(bt, 2.5), "hi": np.percentile(bt, 97.5)})
    info = {"channels": use, "n_folk": int((s.performance_type == "原生态").sum()), "n_trained": int((s.performance_type == "民族唱法").sum())}
    return pd.DataFrame(rows), info


def view3(d, rng):
    t = d[d.performance_type.isin(["原生态", "民族唱法"])]
    songs = t.groupby("song_key").performance_type.nunique()
    songs = songs[songs == 2].index
    ms = zscores(d)
    rows = []
    diffs = {}
    for f in FEATS:
        z = (t[f] - ms[f][0]) / ms[f][1]
        m = z.groupby([t.song_key, t.performance_type]).mean().unstack()
        diff = (m["民族唱法"] - m["原生态"]).reindex(songs).dropna()
        diffs[f] = diff
        bt = [diff.to_numpy()[rng.integers(0, len(diff), len(diff))].mean() for _ in range(N_BOOT)]
        pos, tot = int((diff > 0).sum()), int((diff != 0).sum())
        rows.append({"view": f"same song ({len(diff)} songs)", "contrast": "民族唱法 vs 原生态", "feature": f, "label": label(f),
                     "effect_sd": diff.mean(), "lo": np.percentile(bt, 2.5), "hi": np.percentile(bt, 97.5), "n_songs": len(diff),
                     "songs_trained_higher": pos, "sign_test_p": binomtest(pos, tot, 0.5).pvalue if tot else np.nan})
    return pd.DataFrame(rows), len(songs)


def view4(d, rng, min_each=10):
    t = d[d.performance_type.isin(["原生态", "民族唱法"])]
    cnt = t.groupby(["region_en", "performance_type"]).size().unstack(fill_value=0)
    regs = cnt[cnt.min(axis=1) >= min_each].index.tolist()
    rows = []
    for r in regs:
        for p in ("原生态", "民族唱法"):
            s = t[(t.region_en == r) & (t.performance_type == p)]
            g = s.groupby("group_id")
            for f in PRIMARY:
                a = g[f].agg(["sum", "count"]).dropna()
                idx = rng.integers(0, len(a), (N_BOOT, len(a)))
                bt = a["sum"].to_numpy()[idx].sum(1) / a["count"].to_numpy()[idx].sum(1)
                rows.append({"region": r, "type": p, "feature": f, "n": len(s), "mean": s[f].mean(), "lo": np.percentile(bt, 2.5),
                             "hi": np.percentile(bt, 97.5)})
    return pd.DataFrame(rows), regs


def plot_effects(parts, out: Path):
    panels = [(e, title) for e, title in parts]
    order = FEATS
    fig, axs = plt.subplots(1, len(panels), figsize=(4.7 * len(panels), 6.4), sharey=True)
    yv = {f: len(order) - 1 - i for i, f in enumerate(order)}
    for ax, (e, title) in zip(axs, panels):
        e = e.set_index("feature").reindex(order)
        sig = (np.sign(e.lo) == np.sign(e.hi)).to_numpy()
        yy = np.array([yv[f] for f in order])
        ax.axhspan(yv[PRIMARY_LAST] - 0.5, yv[order[0]] + 0.5, color="#f1f0ec", zorder=0)
        ax.hlines(yy, e.lo, e.hi, color=BLUE, lw=2, zorder=2)
        ax.scatter(e.effect_sd[sig], yy[sig], s=50, color=BLUE, edgecolor="white", linewidth=1.2, zorder=3)
        ax.scatter(e.effect_sd[~sig], yy[~sig], s=50, color="white", edgecolor=BLUE, linewidth=1.8, zorder=3)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_title(title, color=INK, fontsize=9.5, loc="left")
        ax.set_xlabel("Difference (standard deviations)", color=MUTED, fontsize=8.5)
        ax.grid(axis="x", color=GRID)
        style(ax)
    axs[0].set_yticks([yv[f] for f in order], [("★ " if f in PRIMARY else "") + label(f) for f in order], fontsize=9, color=INK)
    fig.suptitle("Does stage-style singing differ from folk-style singing?", x=0.015, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.015, 0.925, "★ shaded = main measures with predicted direction (trained lower in grid distance and speed variation, higher in "
             "even spacing). Filled = interval excludes zero.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


PRIMARY_LAST = list(PRIMARY)[-1]


def plot_regions(b: pd.DataFrame, regs, out: Path):
    feats = list(PRIMARY)
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 4.9), sharey=True)
    y = {r: len(regs) - 1 - i for i, r in enumerate(regs)}
    for ax, f in zip(axs, feats):
        for p, c, dy in (("原生态", BLUE, 0.12), ("民族唱法", ORANGE, -0.12)):
            s = b[(b.feature == f) & (b.type == p)]
            yy = np.array([y[r] + dy for r in s.region])
            ax.hlines(yy, s.lo, s.hi, color=c, lw=1.8, zorder=2)
            ax.scatter(s["mean"], yy, s=40, color=c, edgecolor="white", linewidth=1, zorder=3, label="folk (原生态)" if p == "原生态" else "trained (民族唱法)")
        ax.set_title(f"{label(f)}  (trained {'lower' if PRIMARY[f] < 0 else 'higher'} predicted)", color=INK, fontsize=9.5, loc="left")
        ax.grid(axis="x", color=GRID)
        style(ax)
    n = b.drop_duplicates(["region", "type"]).pivot(index="region", columns="type", values="n")
    axs[0].set_yticks([y[r] for r in regs], [f"{r}  ({n.loc[r, '原生态']} / {n.loc[r, '民族唱法']})" for r in regs], fontsize=9, color=INK)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=8.5, labelcolor=MUTED, loc="upper right", bbox_to_anchor=(0.99, 0.97), ncol=2)
    fig.suptitle("Folk and trained singing within the same region", x=0.015, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.015, 0.915, "Regions with at least 10 recordings of each (folk / trained counts in brackets). Line = 95% interval resampling channels/singers.",
             color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_ROOT / "style"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    pd.set_option("display.width", 220)
    d = prepare()
    print(f"{len(d)} recordings: {d.performance_type.value_counts().to_dict()}")

    e1 = view1(d, rng)
    e2, info = view2(d, rng)
    e3, n_songs = view3(d, rng)
    b, regs = view4(d, rng)
    pd.concat([e1, e2, e3]).to_csv(out / "effects.csv", index=False)
    b.to_csv(out / "by_region.csv", index=False)
    print("same-channel groups:", info, "| songs with both versions:", n_songs, "| regions compared:", regs)

    tr = e1[e1.contrast == "民族唱法 vs 原生态"]
    fl = e1[e1.contrast == "field vs 原生态"]
    plot_effects([(tr, "1. Pooled, region held fixed\n(trained vs folk)"), (e2, f"2. {e2.view.iloc[0]}\n(trained vs folk)"),
                  (e3, f"3. same song ({e3.n_songs.min()}-{e3.n_songs.max()} songs)\n(trained - folk)"), (fl, "Field recordings vs folk\n(region held fixed)")], out / "fig_style_effects.png")
    plot_regions(b, regs, out / "fig_style_by_region.png")

    def show(e, name):
        s = e.set_index("feature").reindex(FEATS)
        print(f"\n{name}")
        print(s[["label", "effect_sd", "lo", "hi"] + [c for c in ("songs_trained_higher", "sign_test_p") if c in s]].round(2).to_string())
    show(tr, "1. trained vs folk, pooled with region fixed")
    show(e2, "2. same channel")
    show(e3, "3. same song")
    show(fl, "field vs folk, pooled with region fixed")
    print("\nprimary measures, predicted sign:", PRIMARY)
    print("outputs ->", out)


if __name__ == "__main__":
    main()
