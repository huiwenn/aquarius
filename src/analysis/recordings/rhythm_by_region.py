"""
Rhythm and tempo by region, from the note onsets of the primary MIDI transcription of each recording.

The stored `tempo_bpm` of the transcription index is a generic estimate and its `free_rhythm_suspect` flag is False for
every recording, so rhythm is measured here directly.

Why no beat or tempo-in-BPM estimate: a first version looked for a pulse (period fitting on 16 s windows). On synthetic
songs with known metre it missed clearly metered music, because transcribed onsets carry tens of ms of timing error and
singers drift in tempo. A measure that cannot find a pulse in a song built to have one cannot be trusted on real songs,
so this script only uses measures that need no beat inference.

Per recording (note onsets from the MIDI; intervals between consecutive onsets are IOIs):
  note_rate         notes per second between the first and last onset
  median_ioi        median IOI (s), IOIs shorter than 2 s
  isochrony         share of consecutive IOI pairs (both < 2 s) whose ratio lies within [0.8, 1.25]: how often the next
                    note comes after about the same wait. Tolerates tempo drift (it is local) and small timing error.
                    Synthetic reference: random spacing 0.21 (5-95%: 0.13-0.34); songs that move mostly in equal note
                    values 0.43; metered songs with mixed note values, rests and timing noise 0.19-0.31. So it describes
                    HOW EVENLY notes are spaced; it does NOT separate metered from free rhythm.
  tempo_variation   standard deviation of log note rate over 8 s windows (hop 4 s, >= 6 onsets): speed change over the song
  rest_share        share of the sung span inside gaps longer than 1 s (phrase breaks)
  long_note_share   share of notes longer than 1 s (held notes)
Per region: means with cluster-bootstrap 95% intervals (groups = `group_id`: channel or singer). Style contrasts:
performance_type, dating_flag, genre (n >= 25).

Limits: onsets come from a transcriber (a held or ornamented note may count once or several times); isochrony measures
equal spacing, not metre; duple or triple metre and tempo in BPM are NOT estimated. Exploratory only.
Quality filter: recordings above 8 notes/s are dropped (transcription artefacts, e.g. one sung note split into many).
Run (from the repo root):  python src/analysis/recordings/rhythm_by_region.py [--all] [--out data/analysis/recordings/rhythm]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pretty_midi

from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, SHARE, cluster_boot, style

BLUE = "#2a78d6"
MAX_IOI = 2.0
RATIO = (0.8, 1.25)
WIN_S, HOP_S, WIN_MIN_ONSETS, MIN_WINDOWS = 8.0, 4.0, 6, 5
MAX_NOTE_RATE = 8.0  # above this the transcriber has split notes (8 of 1,200 recordings); they are excluded


def profile(path: Path) -> dict | None:
    try:
        pm = pretty_midi.PrettyMIDI(str(path))
    except Exception:
        return None
    notes = sorted((n for i in pm.instruments for n in i.notes), key=lambda n: n.start)
    if len(notes) < 30:
        return None
    on = np.array([n.start for n in notes])
    dur = np.array([n.end - n.start for n in notes])
    span = on[-1] - on[0]
    if span < 20:
        return None
    ioi = np.diff(on)
    ok = (ioi > 0.03) & (ioi < MAX_IOI)  # drop duplicate onsets and phrase breaks
    a, b = ioi[:-1], ioi[1:]
    pair = ok[:-1] & ok[1:]
    ratio = b[pair] / a[pair]
    gaps = ioi[ioi > 1.0]
    rates = []
    for t0 in np.arange(on[0], on[-1] - WIN_S + 1e-9, HOP_S):
        c = int(((on >= t0) & (on < t0 + WIN_S)).sum())
        if c >= WIN_MIN_ONSETS:
            rates.append(c / WIN_S)
    return {"n_notes": len(on), "span_s": float(span), "note_rate": len(on) / span,
            "median_ioi": float(np.median(ioi[ok])) if ok.sum() else np.nan,
            "isochrony": float(((ratio >= RATIO[0]) & (ratio <= RATIO[1])).mean()) if pair.sum() >= 30 else np.nan,
            "tempo_variation": float(np.std(np.log(rates))) if len(rates) >= MIN_WINDOWS else np.nan,
            "rest_share": float(gaps.sum() / span), "long_note_share": float((dur > 1.0).mean())}


def midi_paths() -> dict[str, Path]:
    found = {p.stem: p for p in (SHARE / "midi" / "primary").glob("*/*.mid")}
    for idx in sorted(ROOT.glob("data/regions_v*/transcription/dataset_index.csv")):  # one per collection round
        for v in pd.read_csv(idx).itertuples():
            p = ROOT / v.midi_path
            if p.exists():
                found[v.video_id] = p
    return found


def analyse(include_all: bool) -> pd.DataFrame:
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    if not include_all:
        rec = rec[rec.core]
    paths = midi_paths()
    rows = []
    for r in rec.itertuples():
        p = profile(paths[r.item_id]) if r.item_id in paths else None
        if p:
            rows.append({"item_id": r.item_id, "region_en": r.region_en, "group_id": r.group_id, "genre": r.genre,
                         "performance_type": r.performance_type, "dating_flag": r.dating_flag,
                         "ethnic_group": r.ethnic_group, "round": r.round, **p})
    out = pd.DataFrame(rows)
    bad = out.note_rate > MAX_NOTE_RATE
    print(f"{len(rec)} recordings selected, {len(out)} analysed, {int(bad.sum())} excluded for > {MAX_NOTE_RATE:g} notes/s")
    out = out[~bad].reset_index(drop=True)
    return out


COLS = ["isochrony", "note_rate", "tempo_variation", "rest_share", "long_note_share"]


def summarise(d: pd.DataFrame, by: str, min_n: int = 10, groups_min: int = 5) -> pd.DataFrame:
    rows = []
    for key, g in d.groupby(by):
        if len(g) < min_n:
            continue
        row = {by: key, "n": len(g), "n_groups": g.group_id.nunique(), "median_ioi": g.median_ioi.median(),
               "isochrony_median": g.isochrony.median(), "note_rate_median": g.note_rate.median()}
        for c in COLS:
            m, lo, hi = cluster_boot(g, c)
            if g.group_id.nunique() < groups_min:
                lo = hi = np.nan
            row[c], row[c + "_lo"], row[c + "_hi"] = m, lo, hi
        rows.append(row)
    return pd.DataFrame(rows)


def dots(ax, y, df, col, xlabel):
    ax.hlines(y, df[col + "_lo"], df[col + "_hi"], color=BLUE, lw=2, zorder=2)
    ax.scatter(df[col], y, s=44, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=8.5)
    ax.grid(axis="x", color=GRID)
    style(ax)


def plot_regions(s: pd.DataFrame, out: Path, n_total: int):
    s = s.sort_values("isochrony", ascending=False).reset_index(drop=True)
    fig, axs = plt.subplots(1, 4, figsize=(15, 5.6), sharey=True)
    y = np.arange(len(s))[::-1]
    dots(axs[0], y, s, "isochrony", "Equal-spaced notes (share of note pairs)")
    dots(axs[1], y, s, "note_rate", "Notes per second")
    dots(axs[2], y, s, "tempo_variation", "Speed variation across the song")
    dots(axs[3], y, s, "long_note_share", "Share of held notes (> 1 s)")
    axs[0].set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region_en, s.n)], color=INK, fontsize=9)
    fig.suptitle("Rhythm by region", x=0.015, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.015, 0.925, f"Dot = region mean, line = 95% interval resampling channels/singers. {n_total} recordings.",
             color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_distribution(d: pd.DataFrame, out: Path):
    t = d.dropna(subset=["isochrony"])
    order = t.groupby("region_en").isochrony.median().sort_values().index.tolist()
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.boxplot([t[t.region_en == r].isochrony for r in order], orientation="horizontal", widths=0.55, patch_artist=True,
               whis=(10, 90), showfliers=False, medianprops=dict(color=INK, lw=1.5),
               boxprops=dict(facecolor="#cfe0f6", edgecolor=BLUE), whiskerprops=dict(color=BLUE), capprops=dict(color=BLUE))
    ax.set_yticks(range(1, len(order) + 1), [f"{r}  (n={(t.region_en == r).sum()})" for r in order], color=INK, fontsize=9)
    ax.set_xlabel("Share of consecutive note pairs with about equal spacing", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    fig.suptitle("How evenly spaced are the notes, song by song?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Box = middle half of songs, line = median, whiskers = 10th-90th percentile.", color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
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
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    for yy, _, r in items:
        ax.hlines(yy, r.isochrony_lo, r.isochrony_hi, color=BLUE, lw=2, zorder=2)
        ax.scatter(r.isochrony, yy, s=48, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks([i[0] for i in items], [i[1] for i in items], color=INK, fontsize=9)
    ax.set_ylim(y, 0)
    ax.set_xlabel("Equal-spaced notes (share of consecutive note pairs)", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    for yy, t in heads:
        ax.annotate(t, xy=(0, yy), xycoords=("axes fraction", "data"), xytext=(2, 0), textcoords="offset points",
                    color=MUTED, fontsize=8, weight="bold", va="center")
    fig.suptitle("Even spacing by performance type, dating and genre", x=0.02, ha="left", color=INK, fontsize=12, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include non-core recordings")
    ap.add_argument("--out", default=str(OUT_ROOT / "rhythm"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    d = analyse(a.all)
    d.to_csv(out / "per_recording.csv", index=False)
    reg = summarise(d, "region_en", min_n=1)
    reg.to_csv(out / "region_summary.csv", index=False)
    perf = summarise(d, "performance_type")
    dat = summarise(d, "dating_flag")
    gen = summarise(d, "genre", min_n=25).sort_values("isochrony", ascending=False)
    pd.concat([perf.assign(by="performance_type").rename(columns={"performance_type": "value"}),
               dat.assign(by="dating_flag").rename(columns={"dating_flag": "value"}),
               gen.assign(by="genre").rename(columns={"genre": "value"})]).to_csv(out / "style_summary.csv", index=False)
    plot_regions(reg, out / "fig_rhythm_by_region.png", len(d))
    plot_distribution(d, out / "fig_isochrony_distribution.png")
    plot_styles([("Performance type", perf, "performance_type"), ("Dating", dat, "dating_flag"), ("Genre", gen, "genre")],
                out / "fig_rhythm_style.png")
    pd.set_option("display.width", 220)
    cols = ["region_en", "n", "isochrony", "isochrony_lo", "isochrony_hi", "note_rate", "tempo_variation", "long_note_share",
            "rest_share"]
    print(reg.sort_values("isochrony", ascending=False)[cols].round(2).to_string(index=False))
    print(gen[["genre", "n", "isochrony", "isochrony_lo", "isochrony_hi", "note_rate", "long_note_share"]].round(2).to_string(index=False))
    print(perf[["performance_type", "n", "isochrony", "isochrony_lo", "isochrony_hi", "note_rate"]].round(2).to_string(index=False))
    print("isochrony quantiles (10/50/90):", d.isochrony.quantile([.1, .5, .9]).round(2).tolist())
    print("outputs ->", out)


if __name__ == "__main__":
    main()
