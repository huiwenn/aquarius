"""
Notebook 4: the Colour Regions corpus (merged rounds 1 + 2, scores) — composition, provenance, sources.

Reads the release tables (src/colour_regions/build_release.py) and writes figures to notebooks/figures/cr_*.png
and, as vector PDFs, to ../colour_regions_paper/figures/.
Run (py312): python notebooks/04_colour_regions_corpus.py
"""

import sys
from pathlib import Path

import matplotlib
import matplotlib.patheffects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from colour_regions.regions import EN, ORDER, TYPE  # noqa: E402

matplotlib.rcParams.update({
    "font.family": ["Arial Unicode MS", "sans-serif"], "axes.unicode_minus": False, "font.size": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b",
    "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e6e5e1",
    "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 150})

# Reference palette (dataviz skill): categorical slots, ordinal blue ramp for tiers, text inks.
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
TIER = {"A1": "#0d366b", "A2": "#1c5cab", "B": "#3987e5", "C": "#86b6ef", "unknown": "#d6d5d0"}
MUTED = "#8a8984"

FIG = ROOT / "notebooks" / "figures"
PAPER = ROOT.parent / "colour_regions_paper" / "figures"
FIG.mkdir(exist_ok=True)
PAPER.mkdir(exist_ok=True)

rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
sc = pd.read_csv(ROOT / "data" / "colour_regions" / "scores.csv")
LABELS = [EN[r] for r in ORDER]
Y = np.arange(len(ORDER))[::-1]  # first region at the top


def save(fig, name: str) -> None:
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    fig.savefig(PAPER / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print("✓", name)


def region_axis(ax) -> None:
    ax.set_yticks(Y)
    ax.set_yticklabels(LABELS)
    ax.grid(axis="y", visible=False)
    ax.axhline(Y[10] - 0.5, color=MUTED, lw=0.6, ls=(0, (2, 2)))  # Han | minority


def hbar_stack(ax, table: pd.DataFrame, colors: dict, gap: float = 0.4) -> None:
    left = np.zeros(len(ORDER))
    for col, c in colors.items():
        v = table.reindex(ORDER)[col].fillna(0).to_numpy() if col in table else np.zeros(len(ORDER))
        ax.barh(Y, v, left=left, color=c, height=0.72, edgecolor="white", linewidth=gap, label=col)
        left += v


# ── 1. Overview: recordings by round and tier, scores by source ───────────────────────────
rec["tier"] = rec.provenance_tier.fillna("unknown")
fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.6), sharey=True, gridspec_kw={"width_ratios": [1, 1, 0.9]})
t = rec.pivot_table(index="region", columns="round", values="item_id", aggfunc="size")
t.columns = ["Round 1", "Round 2"]
hbar_stack(axes[0], t, {"Round 1": BLUE, "Round 2": ORANGE})
axes[0].set_title("Recordings by round", loc="left", fontsize=8.5)
axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, fontsize=7)
t = rec.pivot_table(index="region", columns="tier", values="item_id", aggfunc="size")
hbar_stack(axes[1], t, {k: v for k, v in TIER.items() if k in t.columns})
axes[1].set_title("Recordings by provenance tier", loc="left", fontsize=8.5)
axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, fontsize=7)
t = sc.pivot_table(index="region", columns="source", values="item_id", aggfunc="size")
t.columns = [c.capitalize() for c in t.columns]
hbar_stack(axes[2], t, {"Anthology": AQUA, "Essen": YELLOW})
axes[2].set_xscale("symlog", linthresh=10)
axes[2].set_title("Scores by source", loc="left", fontsize=8.5)
axes[2].legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, fontsize=7)
for ax in axes:
    region_axis(ax)
save(fig, "cr_01_overview")

# ── 2. Channel concentration per region: largest channel's share, by round ──────────────────
def top_share(df):
    return df.groupby("region").channel_key.agg(lambda s: s.value_counts(normalize=True).iloc[0])


conc = pd.DataFrame({"Round 1": top_share(rec[rec["round"] == 1]), "Round 2": top_share(rec[rec["round"] == 2]),
                     "Merged": top_share(rec)}).reindex(ORDER)
fig, ax = plt.subplots(figsize=(3.6, 3.6))
for i, r in enumerate(ORDER):
    ax.plot(conc.loc[r, ["Round 2", "Round 1"]], [Y[i]] * 2, color="#d6d5d0", lw=1.5, zorder=1)
ax.scatter(conc["Round 1"], Y, s=22, color=BLUE, label="Round 1", zorder=3, edgecolor="white", linewidth=0.8)
ax.scatter(conc["Round 2"], Y, s=22, color=ORANGE, label="Round 2", zorder=3, edgecolor="white", linewidth=0.8)
ax.scatter(conc["Merged"], Y, s=14, marker="|", color="#0b0b0b", label="Merged", zorder=4)
region_axis(ax)
ax.set_xlim(0, 0.9)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_title("Largest channel's share of a region", loc="left", fontsize=8.5)
ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=3, fontsize=7)
save(fig, "cr_02_channel_concentration")

# ── 3. Performance type and platform mix ────────────────────────────────────────────────────
PT = {"原生态": "tradition bearer (原生态)", "field": "field", "民族唱法": "conservatory (民族唱法)",
      "instrumental": "instrumental", "other": "other"}
rec["ptype"] = rec.performance_type.map(PT).fillna("other")
share = rec.pivot_table(index="region", columns="ptype", values="item_id", aggfunc="size").fillna(0)
share = share.div(share.sum(1), axis=0)
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
hbar_stack(axes[0], share, dict(zip(PT.values(), [BLUE, ORANGE, AQUA, YELLOW, MAGENTA])))
axes[0].set_title("Performance type", loc="left", fontsize=8.5)
axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=6.5)
plat = rec.pivot_table(index="region", columns="platform", values="item_id", aggfunc="size").fillna(0)
plat = plat.div(plat.sum(1), axis=0)
hbar_stack(axes[1], plat, {"youtube": BLUE, "bilibili": ORANGE, "europeana": AQUA})
axes[1].set_title("Source platform", loc="left", fontsize=8.5)
axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=6.5)
for ax in axes:
    region_axis(ax)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
save(fig, "cr_03_performance_platform")

# ── 4. Duration and upload year, by round (small multiples) ────────────────────────────────
rec["year"] = pd.to_numeric(rec.upload_date.astype(str).str[:4], errors="coerce")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.2))
bins = np.arange(0, 12.5, 0.5)
for rnd, c in ((1, BLUE), (2, ORANGE)):
    axes[0].hist(rec[rec["round"] == rnd].duration_s / 60, bins=bins, color=c, alpha=0.75, label=f"Round {rnd}",
                 edgecolor="white", linewidth=0.4)
    axes[1].hist(rec[rec["round"] == rnd].year.dropna(), bins=np.arange(2005.5, 2027.5), color=c, alpha=0.75,
                 label=f"Round {rnd}", edgecolor="white", linewidth=0.4)
axes[0].set_xlabel("duration (min)")
axes[1].set_xlabel("upload year")
for ax in axes:
    ax.set_ylabel("recordings")
    ax.legend(fontsize=7)
save(fig, "cr_04_duration_year")

# ── 5. Speech screen (when available) ──────────────────────────────────────────────────────
if rec.speech_share.notna().any():
    fig, ax = plt.subplots(figsize=(3.6, 2.2))
    for rnd, c in ((1, BLUE), (2, ORANGE)):
        v = rec[(rec["round"] == rnd)].speech_share.dropna()
        ax.hist(v, bins=np.linspace(0, 1, 21), color=c, alpha=0.75, label=f"Round {rnd} (n={len(v)})",
                edgecolor="white", linewidth=0.4)
    ax.set_yscale("log")
    ax.set_xlabel("share of 10 s windows classified as speech")
    ax.set_ylabel("recordings")
    ax.legend(fontsize=7)
    save(fig, "cr_05_speech_share")

# ── Summary table printed for the write-up ─────────────────────────────────────────────────
summ = rec.groupby("region").agg(n=("item_id", "size"), hours=("duration_s", lambda s: s.sum() / 3600),
                                 channels=("channel_key", "nunique"),
                                 tierAB=("provenance_tier", lambda s: s.isin(["A1", "A2", "A", "B"]).mean()),
                                 songs=("song_key", "nunique")).reindex(ORDER)
summ["top_channel_r1"], summ["top_channel_r2"] = conc["Round 1"], conc["Round 2"]
summ.index = LABELS
print(summ.round(2).to_string())
print("\nHan vs minority:", rec.groupby(rec.region.map(TYPE)).size().to_dict())

# ── 6. Map: where the recordings come from ─────────────────────────────────────────────────
import json  # noqa: E402

from colour_regions.regions import CODE  # noqa: E402

if "lon" in rec:
    geo = json.load(open(ROOT / "data" / "geo" / "china_provinces.json"))
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for ft in geo["features"]:
        if not ft["properties"].get("name"):  # skip the maritime dashed-line feature
            continue
        geom = ft["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = np.array(poly[0])
            ax.fill(ring[:, 0], ring[:, 1], facecolor="#f3f2ef", edgecolor="#c3c2b7", linewidth=0.4, zorder=0)
    rng = np.random.default_rng(0)
    fine = rec[rec.geo_level.isin(["county", "prefecture"])]
    jit = rng.normal(0, 0.12, (len(fine), 2))
    for typ, c in (("Han", BLUE), ("minority", ORANGE)):
        f = fine[fine.region_type == typ]
        j = jit[fine.region_type.to_numpy() == typ]
        ax.scatter(f.lon + j[:, 0], f.lat + j[:, 1], s=7, color=c, alpha=0.75, linewidth=0, zorder=3,
                   label=f"{typ} region (county/prefecture known)")
    prov = rec[rec.geo_level == "province"].groupby(["geo_name", "lon", "lat", "region_type"]).size().reset_index(name="n")
    for typ, c in (("Han", BLUE), ("minority", ORANGE)):
        p = prov[prov.region_type == typ]
        ax.scatter(p.lon, p.lat, s=6 * p.n, facecolor="none", edgecolor=c, marker="s", linewidth=0.8, zorder=2,
                   label=f"{typ} region (province only; size = count)")
    for zh in ORDER:
        f = fine[fine.region == zh]
        if len(f) == 0:
            continue
        x, y = f.lon.median(), f.lat.median()
        ax.text(x, y, EN[zh], fontsize=6.5, ha="center", va="center", color="#0b0b0b", zorder=5,
                path_effects=[matplotlib.patheffects.withStroke(linewidth=2.2, foreground="white")])
    ax.set_xlim(73, 135.5)
    ax.set_ylim(17.5, 53.8)
    ax.set_aspect(1 / np.cos(np.deg2rad(35)))
    ax.axis("off")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", color=BLUE, ms=4, label="Han region: county or prefecture known"),
               Line2D([], [], marker="o", ls="", color=ORANGE, ms=4, label="minority area: county or prefecture known"),
               Line2D([], [], marker="s", ls="", mfc="none", mec=MUTED, ms=7,
                      label="province only (square size grows with the number of recordings)")]
    ax.legend(handles=handles, loc="lower left", fontsize=6.5)
    save(fig, "cr_06_map")
    print("geocoded:", rec.geo_level.value_counts().to_dict())
