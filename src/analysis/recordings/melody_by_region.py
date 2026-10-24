"""
Melodic range, intervals and contour by region, from the primary MIDI transcription of each recording
. All measures are transposition-invariant (the singer's key does not matter).

Per recording (notes shorter than 50 ms are dropped; consecutive notes belong to one phrase when the onset gap is <= 1 s):
  range_90          pitch range in semitones between the 5th and 95th percentile of note pitches (robust to stray notes)
  mean_abs_interval mean size of the melodic interval between consecutive notes in a phrase (semitones, capped at 12)
  repeat / step / third / leap shares of those intervals: 0, 1-2, 3-4 and >= 5 semitones. Intervals above 12 semitones
                    (probably octave errors of the transcriber) are counted in `over_octave_share` and left out of the others.
  up_share          share of ascending intervals among the intervals that move
  int_0 ... int_12  histogram of interval sizes (int_12 = 12 or more), for the heatmap
  phrase contour    for phrases of >= 6 notes: first note, mean of the middle notes, last note (Huron 1996). Change over
                    1.5 semitones counts as a move. Families: arch (up then down), concave (down then up), ascending,
                    descending, level (no move). Shares need >= 3 phrases.
  phrase_net_change mean of (last - first pitch) over phrases, semitones (negative = phrases end lower)
Per region: means with cluster-bootstrap 95% intervals (groups = `group_id`: channel or singer).

Dropped: a glide share from the F0 track (frames moving > 3 semitones/s) was 60-79% in every region. That is tracker
noise, not ornamentation, so it was removed.

Limits: the notes come from a transcriber (ornaments may become extra notes; octave errors exist; a held note is one note);
phrases are cut at rests, not at lyric or melodic cadences; contour is a coarse three-point summary.
Recordings above 8 notes/s are dropped (transcription artefacts). Exploratory only.
Run (from the repo root):  python src/analysis/recordings/melody_by_region.py [--all] [--out data/analysis/recordings/melody]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pretty_midi

from rhythm_by_region import MAX_NOTE_RATE, midi_paths
from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, cluster_boot, style

BLUE = "#2a78d6"
MIN_NOTE_S = 0.05
PHRASE_GAP_S = 1.0
MIN_PHRASE_NOTES = 6
MIN_PHRASES = 3
MOVE_ST = 1.5
FAMILIES = ["arch", "descending", "ascending", "concave", "level"]
FAMILY_LABEL = {"arch": "arch (up, down)", "descending": "descending", "ascending": "ascending",
                "concave": "concave (down, up)", "level": "level"}
FAMILY_COLOR = {"arch": "#2a78d6", "descending": "#eb6834", "ascending": "#1baf7a", "concave": "#eda100",
                "level": "#e87ba4"}


def contour_family(p: np.ndarray) -> str:
    a = np.mean(p[1:-1]) - p[0]
    b = p[-1] - np.mean(p[1:-1])
    sa = 0 if abs(a) < MOVE_ST else int(np.sign(a))
    sb = 0 if abs(b) < MOVE_ST else int(np.sign(b))
    if sa > 0 and sb < 0:
        return "arch"
    if sa < 0 and sb > 0:
        return "concave"
    if sa + sb > 0:
        return "ascending"
    if sa + sb < 0:
        return "descending"
    return "level"


def profile(midi: Path) -> dict | None:
    try:
        pm = pretty_midi.PrettyMIDI(str(midi))
    except Exception:
        return None
    notes = sorted((n for i in pm.instruments for n in i.notes if n.end - n.start >= MIN_NOTE_S), key=lambda n: n.start)
    if len(notes) < 30:
        return None
    on = np.array([n.start for n in notes])
    pit = np.array([n.pitch for n in notes], float)
    span = on[-1] - on[0]
    if span < 20 or len(on) / span > MAX_NOTE_RATE:
        return None
    gap = np.diff(on) > PHRASE_GAP_S
    iv = np.abs(np.diff(pit))[~gap]
    sgn = np.sign(np.diff(pit))[~gap]
    if len(iv) < 30:
        return None
    over = iv > 12
    ivc = iv[~over]
    out = {"n_notes": len(notes), "range_90": float(np.percentile(pit, 95) - np.percentile(pit, 5)),
           "mean_abs_interval": float(ivc.mean()), "repeat_share": float((ivc < 0.5).mean()),
           "step_share": float(((ivc >= 0.5) & (ivc <= 2.5)).mean()), "third_share": float(((ivc > 2.5) & (ivc <= 4.5)).mean()),
           "leap_share": float((ivc > 4.5).mean()), "over_octave_share": float(over.mean()),
           "up_share": float((sgn[~over][ivc > 0.5] > 0).mean()) if (ivc > 0.5).sum() else np.nan}
    hist = np.bincount(np.minimum(np.round(iv).astype(int), 12), minlength=13) / len(iv)
    out.update({f"int_{k}": float(hist[k]) for k in range(13)})
    # phrases
    cuts = np.flatnonzero(gap) + 1
    phrases = [p for p in np.split(pit, cuts) if len(p) >= MIN_PHRASE_NOTES]
    out["n_phrases"] = len(phrases)
    fam = {f: np.nan for f in FAMILIES}
    out["phrase_notes_median"] = float(np.median([len(p) for p in phrases])) if phrases else np.nan
    out["phrase_net_change"] = np.nan
    if len(phrases) >= MIN_PHRASES:
        c = pd.Series([contour_family(p) for p in phrases]).value_counts(normalize=True)
        fam = {f: float(c.get(f, 0.0)) for f in FAMILIES}
        out["phrase_net_change"] = float(np.mean([p[-1] - p[0] for p in phrases]))
    out.update({f"contour_{f}": v for f, v in fam.items()})
    return out


def analyse(include_all: bool) -> pd.DataFrame:
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    if not include_all:
        rec = rec[rec.core]
    mp = midi_paths()
    rows = []
    for r in rec.itertuples():
        p = profile(mp[r.item_id]) if r.item_id in mp else None
        if p:
            rows.append({"item_id": r.item_id, "region_en": r.region_en, "group_id": r.group_id, "genre": r.genre,
                         "performance_type": r.performance_type, "dating_flag": r.dating_flag,
                         "ethnic_group": r.ethnic_group, "round": r.round, **p})
    out = pd.DataFrame(rows)
    print(f"{len(rec)} recordings selected, {len(out)} analysed ({int(out.contour_arch.notna().sum())} with >= "
          f"{MIN_PHRASES} phrases for contour)")
    return out


COLS = ["range_90", "mean_abs_interval", "repeat_share", "step_share", "third_share", "leap_share", "over_octave_share",
        "up_share", "phrase_net_change", "phrase_notes_median"] + [f"contour_{f}" for f in FAMILIES]


def summarise(d: pd.DataFrame, by: str, min_n: int = 10, groups_min: int = 5) -> pd.DataFrame:
    rows = []
    for key, g in d.groupby(by):
        if len(g) < min_n:
            continue
        row = {by: key, "n": len(g), "n_groups": g.group_id.nunique(), "n_contour": int(g.contour_arch.notna().sum()),
               "range_90_median": g.range_90.median()}
        for c in COLS:
            m, lo, hi = cluster_boot(g, c)
            if g.group_id.nunique() < groups_min:
                lo = hi = np.nan
            row[c], row[c + "_lo"], row[c + "_hi"] = m, lo, hi
        for k in range(13):
            row[f"int_{k}"] = g[f"int_{k}"].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def dots(ax, y, df, col, xlabel):
    ax.hlines(y, df[col + "_lo"], df[col + "_hi"], color=BLUE, lw=2, zorder=2)
    ax.scatter(df[col], y, s=44, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=8.5)
    ax.grid(axis="x", color=GRID)
    style(ax)


def plot_regions(s: pd.DataFrame, out: Path, n_total: int):
    s = s.sort_values("range_90", ascending=False).reset_index(drop=True)
    fig, axs = plt.subplots(1, 4, figsize=(15, 5.6), sharey=True)
    y = np.arange(len(s))[::-1]
    dots(axs[0], y, s, "range_90", "Pitch range (semitones, 5th-95th percentile)")
    dots(axs[1], y, s, "mean_abs_interval", "Mean interval between notes (semitones)")
    dots(axs[2], y, s, "leap_share", "Share of leaps (5 semitones or more)")
    dots(axs[3], y, s, "phrase_net_change", "Phrase end minus start (semitones)")
    axs[3].axvline(0, color=MUTED, lw=1)
    axs[0].set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region_en, s.n)], color=INK, fontsize=9)
    fig.suptitle("Melodic range and movement by region", x=0.015, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.015, 0.925, f"Dot = region mean, line = 95% interval resampling channels/singers. {n_total} recordings.",
             color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_contours(s: pd.DataFrame, out: Path):
    s = s.sort_values("contour_arch").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    y = np.arange(len(s))
    left = np.zeros(len(s))
    for f in FAMILIES:
        w = s[f"contour_{f}"].to_numpy()
        ax.barh(y, w, left=left, height=0.72, color=FAMILY_COLOR[f], edgecolor="white", linewidth=2, label=FAMILY_LABEL[f])
        for yi, (wi, li) in enumerate(zip(w, left)):
            if wi >= 0.08:
                ax.text(li + wi / 2, yi, f"{wi * 100:.0f}", ha="center", va="center", fontsize=8, color=INK)
        left += w
    ax.set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region_en, s.n_contour)], color=INK, fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, .25, .5, .75, 1], ["0%", "25%", "50%", "75%", "100%"])
    style(ax)
    ax.legend(ncol=5, loc="upper left", bbox_to_anchor=(0, 1.08), frameon=False, fontsize=9, labelcolor=MUTED,
              handlelength=1, columnspacing=1.2)
    fig.suptitle("Phrase contour by region", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_intervals(s: pd.DataFrame, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0d2f5c"])
    s = s.sort_values("mean_abs_interval").reset_index(drop=True)
    m = s[[f"int_{k}" for k in range(13)]].to_numpy() * 100
    fig, ax = plt.subplots(figsize=(10, 5.6))
    im = ax.imshow(m, cmap=cmap, aspect="auto", vmin=0, vmax=m.max())
    for i in range(m.shape[0]):
        for j in range(13):
            if m[i, j] >= 1:
                ax.text(j, i, f"{m[i, j]:.0f}", ha="center", va="center", fontsize=7.5,
                        color="white" if m[i, j] > 0.55 * m.max() else INK)
    ax.set_xticks(range(13), [str(k) if k < 12 else "12+" for k in range(13)])
    ax.set_xlabel("Interval between consecutive notes (semitones)", color=MUTED, fontsize=9)
    ax.set_yticks(range(len(s)), s.region_en, color=INK, fontsize=9)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("% of intervals", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle("Which melodic intervals does each region use?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_styles(parts: list[tuple[str, pd.DataFrame, str]], out: Path):
    items, y, heads = [], 0.0, []
    for title, df, key in parts:
        y += 0.8
        heads.append((y - 0.5, title))
        for r in df.itertuples():
            items.append((y, f"{getattr(r, key)}  (n={r.n})", r))
            y += 1
    fig, axs = plt.subplots(1, 2, figsize=(11, 6.2), sharey=True)
    for ax, col, xl in ((axs[0], "range_90", "Pitch range (semitones)"), (axs[1], "leap_share", "Share of leaps (5+ semitones)")):
        for yy, _, r in items:
            ax.hlines(yy, getattr(r, col + "_lo"), getattr(r, col + "_hi"), color=BLUE, lw=2, zorder=2)
            ax.scatter(getattr(r, col), yy, s=48, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
        ax.set_xlabel(xl, color=MUTED, fontsize=9)
        ax.grid(axis="x", color=GRID)
        style(ax)
    axs[0].set_yticks([i[0] for i in items], [i[1] for i in items], color=INK, fontsize=9)
    axs[0].set_ylim(y, 0)
    for yy, t in heads:
        axs[0].annotate(t, xy=(0, yy), xycoords=("axes fraction", "data"), xytext=(2, 0), textcoords="offset points",
                        color=MUTED, fontsize=8, weight="bold", va="center")
    fig.suptitle("Range and leaps by performance type, dating and genre", x=0.02, ha="left", color=INK, fontsize=12,
                 weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include non-core recordings")
    ap.add_argument("--out", default=str(OUT_ROOT / "melody"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    d = analyse(a.all)
    d.to_csv(out / "per_recording.csv", index=False)
    reg = summarise(d, "region_en", min_n=1)
    reg.to_csv(out / "region_summary.csv", index=False)
    perf = summarise(d, "performance_type")
    dat = summarise(d, "dating_flag")
    gen = summarise(d, "genre", min_n=25).sort_values("range_90", ascending=False)
    pd.concat([perf.assign(by="performance_type").rename(columns={"performance_type": "value"}),
               dat.assign(by="dating_flag").rename(columns={"dating_flag": "value"}),
               gen.assign(by="genre").rename(columns={"genre": "value"})]).to_csv(out / "style_summary.csv", index=False)
    plot_regions(reg, out / "fig_melody_by_region.png", len(d))
    plot_contours(reg, out / "fig_contour_by_region.png")
    plot_intervals(reg, out / "fig_interval_profile.png")
    plot_styles([("Performance type", perf, "performance_type"), ("Dating", dat, "dating_flag"), ("Genre", gen, "genre")],
                out / "fig_melody_style.png")
    pd.set_option("display.width", 230)
    cols = ["region_en", "n", "range_90", "mean_abs_interval", "repeat_share", "step_share", "third_share", "leap_share",
            "over_octave_share", "up_share", "phrase_net_change"]
    print(reg.sort_values("range_90", ascending=False)[cols].round(2).to_string(index=False))
    print(reg.sort_values("contour_arch", ascending=False)[["region_en", "n_contour"] + [f"contour_{f}" for f in FAMILIES]
                                                          + ["phrase_net_change", "phrase_notes_median"]].round(2).to_string(index=False))
    print(gen[["genre", "n", "range_90", "mean_abs_interval", "leap_share", "contour_arch", "contour_descending"]].round(2).to_string(index=False))
    print(perf[["performance_type", "n", "range_90", "range_90_lo", "range_90_hi", "leap_share"]].round(2).to_string(index=False))
    print("outputs ->", out)


if __name__ == "__main__":
    main()
