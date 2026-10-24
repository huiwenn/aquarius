"""
Intonation by region: how far does sung pitch sit from the 12-tone equal-tempered (12-TET) piano grid?

Per recording (RMVPE F0 of the separated voice; steady frames only, so glides and attacks are excluded):
  1. global tuning: the circular mean of the fractional semitone is removed (singers need not sing at A=440)
  2. off_grid_share: share of steady frames more than 35 cents from the nearest semitone ("between the keys").
       A uniformly random pitch would give 0.30; perfect 12-TET singing gives about 0.
  3. grid_R: resultant length of the fractional-semitone phase (1 = all on the grid, 0 = uniform)
  4. off_grid_local: the same share after removing tuning per 8-second window. If it is much lower than
       off_grid_share, the singer drifted in pitch over the song, so the "off-grid" part is drift, not scale.
  5. drift_cents: standard deviation of the per-window tuning offsets
  6. per scale degree (relative to the best-fitting pentatonic collection, as in scales_by_region.py):
       median deviation from the tuned grid in cents, only for degrees holding >= 5% of the frames (rarer degrees
       are mostly passing notes and just lean toward the neighbouring scale note), plus the fit margin for filtering.

Per region: means with cluster-bootstrap 95% intervals (groups = `group_id`: channel or singer).
Style contrasts (pooled, all regions): performance_type (folk vs trained vs field), dating_flag (traditional vs
composed), and accompaniment (a fixed-pitch instrument pulls the singer onto the grid).

Limits: one F0 tracker on separated vocals (bleed and separation artefacts add noise); an accompaniment that is
tuned to the grid affects the singer; the degree labels depend on the pentatonic fit (use --min-margin);
automatic results are exploratory only.
Run (from the repo root):  python src/analysis/recordings/intonation_by_region.py [--all] [--min-margin 0.05] [--out data/analysis/recordings/intonation]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scales_by_region import GRID, OUT_ROOT, INK, MUTED, PENTA, ROOT, cluster_boot, f0_paths, style

OFF_GRID_CENTS = 35
WINDOW_S = 8.0
MIN_WINDOW_FRAMES = 150
MIN_FRAMES = 300
MIN_DEGREE_FRAMES = 30
MIN_DEGREE_SHARE = 0.05  # a degree counts as a scale note only if it holds >= 5% of the frames; rarer ones are mostly
#                          passing notes, whose deviation just points at the neighbouring scale note
BLUE, ORANGE = "#2a78d6", "#eb6834"


def wrap(x: np.ndarray) -> np.ndarray:
    """Wrap a fractional-semitone difference to [-0.5, 0.5)."""
    return (x + 0.5) % 1.0 - 0.5


def circ_mean(frac: np.ndarray) -> float:
    return float(np.angle(np.mean(np.exp(2j * np.pi * frac))) / (2 * np.pi))


def profile(f0: np.ndarray, hop: float) -> dict | None:
    v = f0 > 0
    if v.sum() < MIN_FRAMES:
        return None
    st = np.full(len(f0), np.nan)
    st[v] = 12 * np.log2(f0[v] / 440.0) + 69
    smooth = pd.Series(st).rolling(5, center=True, min_periods=3).mean().to_numpy()
    steady = v & (np.abs(np.gradient(smooth)) / hop < 3)
    idx = np.flatnonzero(steady)
    if len(idx) < MIN_FRAMES:
        return None
    s = st[idx]
    frac = s - np.round(s)
    off = circ_mean(frac)
    tuned = s - off
    pc = np.round(tuned).astype(int) % 12
    dev = wrap(frac - off) * 100  # cents from the tuned grid
    out = {
        "n_steady": int(len(s)),
        "tuning_cents": off * 100,
        "off_grid_share": float((np.abs(dev) > OFF_GRID_CENTS).mean()),
        "mean_abs_dev": float(np.abs(dev).mean()),
        "grid_R": float(np.abs(np.mean(np.exp(2j * np.pi * frac)))),
    }
    # local tuning: remove the offset per window
    win = (idx * hop // WINDOW_S).astype(int)
    devs, offs = [], []
    for w in np.unique(win):
        m = win == w
        if m.sum() >= MIN_WINDOW_FRAMES:
            o = circ_mean(frac[m])
            offs.append(o * 100)
            devs.append(wrap(frac[m] - o) * 100)
    if sum(len(x) for x in devs) >= MIN_FRAMES and len(offs) >= 2:
        dl = np.concatenate(devs)
        out["off_grid_local"] = float((np.abs(dl) > OFF_GRID_CENTS).mean())
        out["drift_cents"] = float(np.std(offs))
    else:
        out["off_grid_local"], out["drift_cents"] = np.nan, np.nan
    # degrees relative to the best pentatonic collection
    hist = np.bincount(pc, minlength=12) / len(pc)
    cover = np.array([hist[(PENTA + k) % 12].sum() for k in range(12)])
    root = int(np.argmax(cover))
    srt = np.sort(cover)[::-1]
    out["penta_margin"] = float(srt[0] - srt[1])
    deg = (pc - root) % 12
    for d in range(12):
        m = deg == d
        out[f"dev_{d}"] = float(np.median(dev[m])) if m.sum() >= max(MIN_DEGREE_FRAMES, MIN_DEGREE_SHARE * len(pc)) else np.nan
    return out


def accompaniment(flags) -> str:
    f = str(flags).split(";") if isinstance(flags, str) else []
    return "accompanied" if "accompanied" in f else "unaccompanied" if "unaccompanied" in f else "unknown"


def analyse(include_all: bool) -> pd.DataFrame:
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    if not include_all:
        rec = rec[rec.core]
    paths = f0_paths()
    rows = []
    for r in rec.itertuples():
        if r.item_id not in paths:
            continue
        z = np.load(paths[r.item_id])
        p = profile(z["f0"], float(z["hop_s"]) if "hop_s" in z.files else 0.01)
        if p:
            rows.append({"item_id": r.item_id, "region_en": r.region_en, "group_id": r.group_id,
                         "performance_type": r.performance_type, "dating_flag": r.dating_flag,
                         "accompaniment": accompaniment(r.feature_flags), "genre": r.genre,
                         "ethnic_group": r.ethnic_group, "round": r.round, **p})
    out = pd.DataFrame(rows)
    print(f"{len(rec)} recordings selected, {len(out)} analysed")
    return out


def summarise_regions(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for reg, g in d.groupby("region_en"):
        row = {"region": reg, "n": len(g), "n_groups": g.group_id.nunique(), "drift_cents": g.drift_cents.mean(),
               "grid_R": g.grid_R.mean(), "mean_abs_dev": g.mean_abs_dev.mean(),
               "share_unaccompanied": (g.accompaniment == "unaccompanied").mean()}
        for col in ("off_grid_share", "off_grid_local"):
            row[col], row[col + "_lo"], row[col + "_hi"] = cluster_boot(g, col)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("off_grid_share").reset_index(drop=True)


def summarise_styles(d: pd.DataFrame, min_n: int = 10) -> pd.DataFrame:
    rows = []
    for col in ("performance_type", "dating_flag", "accompaniment"):
        for val, g in d.groupby(col):
            if len(g) >= min_n:
                m, lo, hi = cluster_boot(g, "off_grid_share")
                ml, llo, lhi = cluster_boot(g, "off_grid_local")
                if g.group_id.nunique() < 5:  # too few channels/singers for an interval to mean anything
                    lo = hi = llo = lhi = np.nan
                rows.append({"by": col, "value": val, "n": len(g), "n_groups": g.group_id.nunique(),
                             "off_grid_share": m, "lo": lo, "hi": hi, "off_grid_local": ml,
                             "local_lo": llo, "local_hi": lhi, "drift_cents": g.drift_cents.mean()})
    return pd.DataFrame(rows)


def degree_table(d: pd.DataFrame, min_margin: float, min_recordings: int = 8):
    c = d[d.penta_margin >= min_margin]
    regs = sorted(d.region_en.unique())
    med = np.full((len(regs), 12), np.nan)
    cnt = np.zeros((len(regs), 12), int)
    for i, r in enumerate(regs):
        g = c[c.region_en == r]
        for k in range(12):
            v = g[f"dev_{k}"].dropna()
            cnt[i, k] = len(v)
            if len(v) >= min_recordings:
                med[i, k] = v.median()
    return regs, med, cnt, len(c)


def plot_grid(s: pd.DataFrame, out: Path, n_total: int):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
    y = np.arange(len(s))[::-1]
    for ax, col, xl in ((axs[0], "off_grid_share", "Share of singing between the piano keys (global tuning)"),
                        (axs[1], "off_grid_local", "Same, after removing slow pitch drift (8 s windows)")):
        ax.hlines(y, s[col + "_lo"], s[col + "_hi"], color=BLUE, lw=2, zorder=2)
        ax.scatter(s[col], y, s=48, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
        ax.axvline(0.30, color=MUTED, ls=(0, (4, 3)), lw=1)
        ax.set_xlabel(xl, color=MUTED, fontsize=9)
        ax.grid(axis="x", color=GRID)
        style(ax)
    axs[0].text(0.30, len(s) - 0.35, " random pitch (0.30)", color=MUTED, fontsize=8, va="bottom")
    axs[0].set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region, s.n)], color=INK, fontsize=9)
    fig.suptitle("How far from the piano grid does each region sing?", x=0.02, ha="left", color=INK, fontsize=13,
                 weight="bold")
    fig.text(0.02, 0.925, f"Dot = region mean, line = 95% interval resampling channels/singers. {n_total} recordings.",
             color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_degrees(regs, med, cnt, n_used, min_margin, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", [BLUE, "#f1f0ec", ORANGE])
    lim = 35
    fig, ax = plt.subplots(figsize=(10, 5.6))
    im = ax.imshow(np.ma.masked_invalid(med), cmap=cmap, vmin=-lim, vmax=lim, aspect="auto")
    ax.set_facecolor("#ffffff")
    for i in range(med.shape[0]):
        for j in range(12):
            if not np.isnan(med[i, j]):
                ax.text(j, i, f"{med[i, j]:+.0f}", ha="center", va="center", fontsize=7.5, color=INK)
    labels = ["0 宫", "1", "2 商", "3", "4 角", "5", "6", "7 徵", "8", "9 羽", "10", "11"]
    ax.set_xticks(range(12), labels)
    ax.set_xlabel("Semitones above the best-fitting pentatonic root (degree)", color=MUTED, fontsize=9)
    ax.set_yticks(range(len(regs)), regs, color=INK, fontsize=9)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("median deviation from the tuned grid (cents; + sharp, - flat)", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle("Where do scale degrees sit relative to the piano grid?", x=0.02, ha="left", color=INK, fontsize=13,
                 weight="bold")
    fig.text(0.02, 0.925, f"Recordings with a clear pentatonic fit (margin >= {min_margin}): {n_used}. Blank = fewer "
             "than 8 recordings use that degree as a scale note (>= 5% of their singing).", color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_styles(st: pd.DataFrame, out: Path):
    order = [("performance_type", ["原生态", "field", "民族唱法", "other"]), ("dating_flag", ["traditional", "check", "composed"]),
             ("accompaniment", ["unaccompanied", "accompanied", "unknown"])]
    titles = {"performance_type": "Performance type", "dating_flag": "Dating", "accompaniment": "Accompaniment"}
    items, y, ys = [], 0, []
    for col, vals in order:
        y += 0.8
        ys.append((y - 0.5, titles[col]))
        for v in vals:
            r = st[(st.by == col) & (st.value == v)]
            if len(r):
                items.append((y, f"{v}  (n={int(r.n.iloc[0])})", r.iloc[0]))
                y += 1
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for yy, lab, r in items:
        ax.hlines(yy, r.lo, r.hi, color=BLUE, lw=2, zorder=2)
        ax.scatter(r.off_grid_share, yy, s=48, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks([i[0] for i in items], [i[1] for i in items], color=INK, fontsize=9)
    ax.set_ylim(y, 0)
    ax.axvline(0.30, color=MUTED, ls=(0, (4, 3)), lw=1)
    ax.set_xlabel("Share of singing between the piano keys", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    for yy, t in ys:
        ax.annotate(t, xy=(0, yy), xycoords=("axes fraction", "data"), xytext=(0.01, 0), textcoords="offset points",
                    color=MUTED, fontsize=8, weight="bold", va="center")
    fig.suptitle("Is stage-style, composed or accompanied singing closer to the grid?", x=0.02, ha="left", color=INK,
                 fontsize=12, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include non-core recordings")
    ap.add_argument("--min-margin", type=float, default=0.05, help="degree table: only clear pentatonic fits")
    ap.add_argument("--out", default=str(OUT_ROOT / "intonation"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    d = analyse(a.all)
    d.to_csv(out / "per_recording.csv", index=False)
    s = summarise_regions(d)
    s.to_csv(out / "region_summary.csv", index=False)
    st = summarise_styles(d)
    st.to_csv(out / "style_summary.csv", index=False)
    pd.crosstab(d.performance_type, d.accompaniment).to_csv(out / "type_by_accompaniment_counts.csv")
    regs, med, cnt, n_used = degree_table(d, a.min_margin)
    pd.DataFrame(med, index=regs, columns=[f"deg_{k}" for k in range(12)]).round(1).to_csv(out / "degree_deviation.csv")
    plot_grid(s, out / "fig_grid_by_region.png", len(d))
    plot_degrees(regs, med, cnt, n_used, a.min_margin, out / "fig_degree_deviation.png")
    plot_styles(st, out / "fig_style_contrasts.png")
    pd.set_option("display.width", 220)
    print(s[["region", "n", "off_grid_share", "off_grid_share_lo", "off_grid_share_hi", "off_grid_local", "drift_cents",
             "grid_R", "share_unaccompanied"]].round(3).to_string(index=False))
    print(st.round(3).to_string(index=False))
    print("outputs ->", out)


if __name__ == "__main__":
    main()
