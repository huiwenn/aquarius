"""
Scales and modes by region, from RMVPE F0 tracks of the separated voice.

Per recording (steady sung frames only; glides and attacks are excluded):
  1. tuning: the global offset from 12-TET is removed (circular mean of the fractional semitone)
  2. pitch-class histogram (12 bins, tuned)
  3. pentatonic fit: best of the 12 transpositions of the template {0,2,4,7,9}
       penta_coverage = share of sung frames inside the best-fitting pentatonic collection (chance = 5/12)
       penta_margin   = best minus second-best coverage (small = the collection is ambiguous)
  4. scale size: number of pitch classes with >= 5% of the frames; pitch-class entropy (bits)
  5. 偏音 (bian_share): share of frames on the four non-pentatonic degrees 5, 6, 10, 11 above the collection root
  6. mode (调式): the degree of the FINAL note within the collection: 宫 gong, 商 shang, 角 jue, 徵 zhi, 羽 yu,
     or 'other' if the final falls outside the collection. Final = most frequent pitch class of the last 1.5 s
     of steady sung frames.
  7. degree profile relative to the final note (12 bins), for the heatmap

Per region: means, medians and mode shares with cluster-bootstrap 95% intervals (groups = `group_id`, i.e. channel or
singer, so one performer cannot pass for a regional style).

Limits: F0 from a vocal separator and a single tracker; the final note can be wrong when a recording fades, ends on
speech or applause, or ends on an instrument; the pentatonic template does not model 清乐/燕乐 heptatonic scales.
Run:  python src/analysis/recordings/scales_by_region.py [--all] [--min-margin 0.05 --out data/analysis/recordings/scales_clear]   (from the repo root)     (--all includes non-core recordings)
"""

import argparse
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[3]  # repo root
OUT_ROOT = ROOT / "data" / "analysis" / "recordings"  # all results (gitignored); one sub-folder per analysis
# Transcription package of the older recordings (f0/rmvpe, midi/primary, ...), as shared by the team. Override with the
# environment variable AQUARIUS_SHARE; round folders data/regions_v*/transcription in this repo are read as well.
SHARE = Path(os.environ.get("AQUARIUS_SHARE", ROOT.parent / "colour_regions_share"))
PENTA = np.array([0, 2, 4, 7, 9])
MODE_OF_DEGREE = {0: "gong", 2: "shang", 4: "jue", 7: "zhi", 9: "yu"}
MODES = ["gong", "shang", "jue", "zhi", "yu", "other"]
MODE_ZH = {"gong": "宫", "shang": "商", "jue": "角", "zhi": "徵", "yu": "羽", "other": "outside"}
BIAN = [5, 6, 10, 11]
FINAL_SECONDS = 1.5
MIN_STEADY = 200


def profile(f0: np.ndarray, hop: float) -> dict | None:
    v = f0 > 0
    if v.sum() < 300:
        return None
    st = np.full(len(f0), np.nan)
    st[v] = 12 * np.log2(f0[v] / 440.0) + 69
    smooth = pd.Series(st).rolling(5, center=True, min_periods=3).mean().to_numpy()
    slope = np.abs(np.gradient(smooth)) / hop  # semitones per second
    steady = v & (slope < 3)
    s = st[steady]
    if len(s) < MIN_STEADY:
        return None
    frac = s - np.round(s)
    s = s - np.angle(np.mean(np.exp(2j * np.pi * frac))) / (2 * np.pi)  # remove global tuning
    pc = np.round(s).astype(int) % 12
    hist = np.bincount(pc, minlength=12) / len(pc)

    cover = np.array([hist[(PENTA + k) % 12].sum() for k in range(12)])
    root = int(np.argmax(cover))
    order = np.sort(cover)[::-1]

    n_final = max(int(FINAL_SECONDS / hop), 30)
    final = int(np.bincount(pc[-n_final:], minlength=12).argmax())
    deg_final = (final - root) % 12
    mode = MODE_OF_DEGREE.get(deg_final, "other")

    rel_root = np.roll(hist, -root)  # index = degree above the collection root
    rel_final = np.roll(hist, -final)  # index = degree above the final note
    p = hist[hist > 0]
    out = {
        "n_steady": int(len(s)),
        "penta_coverage": float(order[0]),
        "penta_margin": float(order[0] - order[1]),
        "scale_size": int((hist >= 0.05).sum()),
        "pc_entropy": float(-(p * np.log2(p)).sum()),
        "bian_share": float(rel_root[BIAN].sum()),
        "root_pc": root,
        "final_pc": final,
        "mode": mode,
    }
    out.update({f"rel_final_{d}": float(rel_final[d]) for d in range(12)})
    return out


def cluster_boot(df: pd.DataFrame, col: str, n: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    """Mean of `col` with a 95% interval from resampling whole groups (channel/singer) with replacement."""
    d = df[["group_id", col]].dropna()
    if d.empty:
        return (np.nan,) * 3
    g = d.groupby("group_id")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(g), (n, len(g)))
    est = s[idx].sum(1) / c[idx].sum(1)
    return float(s.sum() / c.sum()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def f0_paths() -> dict[str, Path]:
    found = list((SHARE / "f0" / "rmvpe").glob("*/*.npz"))
    found += list(ROOT.glob("data/regions_v*/transcription/f0_rmvpe/*/*.npz"))
    return {p.stem: p for p in found}


def analyse(include_all: bool) -> pd.DataFrame:
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    if not include_all:
        rec = rec[rec.core]
    paths = f0_paths()
    rows, missing = [], 0
    for r in rec.itertuples():
        if r.item_id not in paths:
            missing += 1
            continue
        z = np.load(paths[r.item_id])
        p = profile(z["f0"], float(z["hop_s"]) if "hop_s" in z.files else 0.01)
        if p:
            rows.append({"item_id": r.item_id, "region_en": r.region_en, "group_id": r.group_id,
                         "genre": r.genre, "performance_type": r.performance_type, "dating_flag": r.dating_flag,
                         "ethnic_group": r.ethnic_group, "round": r.round, **p})
    out = pd.DataFrame(rows)
    print(f"{len(rec)} recordings selected, {missing} without F0, {len(rec) - missing - len(out)} too little steady "
          f"singing, {len(out)} analysed")
    return out


def summarise(d: pd.DataFrame, min_margin: float = 0.0) -> pd.DataFrame:
    """Mode shares use only recordings whose pentatonic fit is clear (penta_margin >= min_margin)."""
    unclear = d.penta_margin < min_margin
    for m in MODES:
        d[f"is_{m}"] = (d["mode"] == m).astype(float).mask(unclear)
    rows = []
    for reg, g in d.groupby("region_en"):
        row = {"region": reg, "n": len(g), "n_groups": g.group_id.nunique(),
               "n_mode": int(g["is_gong"].notna().sum()),
               "scale_size_median": g.scale_size.median(), "entropy": g.pc_entropy.mean()}
        for col in ("penta_coverage", "bian_share"):
            row[col], row[col + "_lo"], row[col + "_hi"] = cluster_boot(g, col)
        for m in MODES:
            row[f"mode_{m}"], row[f"mode_{m}_lo"], row[f"mode_{m}_hi"] = cluster_boot(g, f"is_{m}")
        for k in range(12):
            row[f"rel_final_{k}"] = g[f"rel_final_{k}"].mean()
        rows.append(row)
    return pd.DataFrame(rows).sort_values("penta_coverage", ascending=False).reset_index(drop=True)


# chart colours: reference categorical order (slots 1-5) and a neutral for 'outside'; sequential blue ramp
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
MODE_COLOR = {"gong": "#2a78d6", "shang": "#eb6834", "jue": "#1baf7a", "zhi": "#eda100", "yu": "#e87ba4",
              "other": "#b9b8b1"}


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.set_axisbelow(True)


def plot_pentatonicity(s: pd.DataFrame, out: Path, n_total: int):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
    y = np.arange(len(s))[::-1]
    for ax, col, xlabel in ((axs[0], "penta_coverage", "Share of singing inside the best-fitting pentatonic scale"),
                            (axs[1], "bian_share", "Share on the four non-pentatonic (偏) degrees")):
        ax.hlines(y, s[col + "_lo"], s[col + "_hi"], color="#2a78d6", lw=2, zorder=2)
        ax.scatter(s[col], y, s=48, color="#2a78d6", edgecolor="white", linewidth=1.5, zorder=3)
        ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
        ax.grid(axis="x", color=GRID)
        style(ax)
    axs[0].axvline(5 / 12, color=MUTED, ls=(0, (4, 3)), lw=1)
    axs[0].text(5 / 12, len(s) - 0.35, " chance (5/12)", color=MUTED, fontsize=8, va="bottom")
    axs[0].set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region, s.n)], color=INK, fontsize=9)
    fig.suptitle("How pentatonic is each region's singing?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, f"Dot = region mean, line = 95% interval resampling channels/singers. {n_total} recordings.",
             color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_modes(s: pd.DataFrame, out: Path):
    s = s.sort_values("mode_gong").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    y = np.arange(len(s))
    left = np.zeros(len(s))
    for m in MODES:
        w = s[f"mode_{m}"].to_numpy()
        ax.barh(y, w, left=left, height=0.72, color=MODE_COLOR[m], edgecolor="white", linewidth=2,
                label=f"{MODE_ZH[m]} {m}" if m != "other" else "outside the scale")
        for yi, (wi, li) in enumerate(zip(w, left)):
            if wi >= 0.08:
                ax.text(li + wi / 2, yi, f"{wi * 100:.0f}", ha="center", va="center", fontsize=8, color=INK)
        left += w
    ax.set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region, s.n_mode)], color=INK, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, .25, .5, .75, 1], ["0%", "25%", "50%", "75%", "100%"])
    style(ax)
    ax.legend(ncol=6, loc="upper left", bbox_to_anchor=(0, 1.08), frameon=False, fontsize=9, labelcolor=MUTED,
              handlelength=1, columnspacing=1.2)
    fig.suptitle("Which note do songs end on? Mode (调式) by region", x=0.02, ha="left", color=INK, fontsize=13,
                 weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_degree_profile(s: pd.DataFrame, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0d2f5c"])
    m = s[[f"rel_final_{k}" for k in range(12)]].to_numpy() * 100
    fig, ax = plt.subplots(figsize=(10, 5.6))
    im = ax.imshow(m, cmap=cmap, aspect="auto", vmin=0, vmax=max(m.max(), 1))
    for i in range(m.shape[0]):
        for j in range(12):
            if m[i, j] >= 1:
                ax.text(j, i, f"{m[i, j]:.0f}", ha="center", va="center", fontsize=7.5,
                        color="white" if m[i, j] > 0.55 * m.max() else INK)
    ax.set_xticks(range(12), [str(k) for k in range(12)])
    ax.set_xlabel("Semitones above the song's final note", color=MUTED, fontsize=9)
    ax.set_yticks(range(len(s)), s.region, color=INK, fontsize=9)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("% of singing", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle("Pitch use relative to the final note", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include non-core recordings (opera, instrumental, composed)")
    ap.add_argument("--min-margin", type=float, default=0.0,
                    help="mode shares only from recordings with penta_margin >= this (0.05 = clear fits, ~47%%)")
    ap.add_argument("--out", default=str(OUT_ROOT / "scales"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    d = analyse(a.all)
    d.to_csv(out / "per_recording.csv", index=False)
    s = summarise(d, a.min_margin)
    s.to_csv(out / "region_summary.csv", index=False)
    plot_pentatonicity(s, out / "fig_pentatonicity.png", len(d))
    plot_modes(s, out / "fig_modes.png")
    plot_degree_profile(s, out / "fig_degree_profile.png")
    pd.set_option("display.width", 200)
    show = s[["region", "n", "n_mode", "n_groups", "penta_coverage", "penta_coverage_lo", "penta_coverage_hi", "scale_size_median",
              "bian_share"] + [f"mode_{m}" for m in MODES]]
    print(show.round(2).to_string(index=False))
    print("outputs ->", out)


if __name__ == "__main__":
    main()
