"""
Analyze 色彩区 (stylistic color region) distribution in Aquarius.

Run: conda activate py312 && python src/secaiqu/analyze.py
"""

import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams["font.family"] = ["Arial Unicode MS", "SimHei", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from secaiqu.mapping import (
    AMBIGUOUS_PROVINCES,
    PROVINCE_TO_SECAIQU,
    SECAIQU_METADATA,
    assign_secaiqu,
)

OUT = ROOT / "notebooks" / "figures"
OUT.mkdir(exist_ok=True)

df = pd.read_parquet(ROOT / "data" / "unified" / "master_table.parquet")
print(f"Loaded {len(df):,} items\n")

# ─────────────────────────────────────────────────────────────
# Apply mapping
# ─────────────────────────────────────────────────────────────
df = assign_secaiqu(df)

has_province = df["province"].notna().sum()
has_secaiqu = df["secaiqu"].notna().sum()
unmapped = has_province - has_secaiqu
print(f"Items with province: {has_province:,}")
print(f"Items mapped to 色彩区: {has_secaiqu:,}")
print(f"Unmapped (边疆/少数民族 or invalid): {unmapped:,}")

# Check for unmapped province values
mapped_provs = set(PROVINCE_TO_SECAIQU.keys())
actual_provs = set(df[df["province"].notna()]["province"].unique())
unknown = actual_provs - mapped_provs
if unknown:
    print(f"\nWARNING: Unknown provinces not in mapping: {unknown}")
    for p in unknown:
        n = (df["province"] == p).sum()
        print(f"  {p}: {n} items")

# ─────────────────────────────────────────────────────────────
# Distribution stats
# ─────────────────────────────────────────────────────────────
all_regions = list(SECAIQU_METADATA.keys())
region_counts = df["secaiqu"].value_counts().reindex(all_regions, fill_value=0)

print("\n" + "=" * 60)
print("色彩区 DISTRIBUTION")
print("=" * 60)
for region in all_regions:
    n = region_counts[region]
    en = SECAIQU_METADATA[region]["name_en"]
    pct = n / has_secaiqu * 100 if has_secaiqu > 0 else 0
    bar = "█" * int(pct / 2)
    status = ""
    if n == 0:
        status = " ← MISSING"
    elif n < 500:
        status = " ← underrepresented"
    print(f"  {region:6s} ({en:22s}): {n:>6,} ({pct:5.1f}%) {bar}{status}")

print(f"\n  {'TOTAL':29s}: {has_secaiqu:>6,}")

# ─────────────────────────────────────────────────────────────
# Per-dataset breakdown
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("色彩区 BY DATASET")
print("=" * 60)
datasets_with_prov = df[df["secaiqu"].notna()]["dataset"].unique()
for ds in sorted(datasets_with_prov):
    sub = df[(df["dataset"] == ds) & df["secaiqu"].notna()]
    print(f"\n  {ds} ({len(sub):,} items):")
    for region, n in sub["secaiqu"].value_counts().items():
        print(f"    {region}: {n:,}")

# ─────────────────────────────────────────────────────────────
# Ambiguous provinces
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("AMBIGUOUS PROVINCES (mapped to dominant region)")
print("=" * 60)
for prov, regions in AMBIGUOUS_PROVINCES.items():
    n = (df["province"] == prov).sum()
    assigned = PROVINCE_TO_SECAIQU.get(prov, "?")
    alts = [r for r in regions if r and r != assigned]
    print(f"  {prov} ({n:,} items) → {assigned} (could also be: {', '.join(str(a) for a in alts)})")

# ─────────────────────────────────────────────────────────────
# Figure 13: 色彩区 distribution bar chart
# ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))

colors = plt.cm.Set3(np.linspace(0, 1, len(all_regions)))
bars = ax.barh(range(len(all_regions)), region_counts.values, color=colors, edgecolor="white")

ax.set_yticks(range(len(all_regions)))
labels = [f"{r} ({SECAIQU_METADATA[r]['name_en']})" for r in all_regions]
ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel("Number of items")
ax.set_title("色彩区 Distribution in Aquarius (Han Folk Music Stylistic Regions)")
ax.invert_yaxis()

for bar, val in zip(bars, region_counts.values):
    if val > 0:
        ax.text(val + 50, bar.get_y() + bar.get_height() / 2, f"{val:,}",
                va="center", fontsize=9)
    else:
        ax.text(50, bar.get_y() + bar.get_height() / 2, "MISSING",
                va="center", fontsize=9, color="red", fontstyle="italic")

plt.tight_layout()
plt.savefig(OUT / "13_secaiqu_distribution.png", dpi=150)
plt.close()
print("\n✓ 13_secaiqu_distribution.png")

# ─────────────────────────────────────────────────────────────
# Figure 14: 色彩区 × modality heatmap
# ─────────────────────────────────────────────────────────────
modalities = ["has_audio", "has_midi", "has_musicxml", "has_lyrics"]
mod_labels = ["Audio", "MIDI", "MusicXML", "Lyrics"]

secaiqu_df = df[df["secaiqu"].notna()]
mod_matrix = np.zeros((len(all_regions), len(modalities)))
count_matrix = np.zeros(len(all_regions))

for i, region in enumerate(all_regions):
    sub = secaiqu_df[secaiqu_df["secaiqu"] == region]
    count_matrix[i] = len(sub)
    for j, mod in enumerate(modalities):
        if len(sub) > 0:
            mod_matrix[i, j] = (sub[mod] == True).sum() / len(sub) * 100

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(mod_matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=100)

ax.set_xticks(range(len(mod_labels)))
ax.set_xticklabels(mod_labels, fontsize=11)
ax.set_yticks(range(len(all_regions)))
ylabels = [f"{r} (n={int(count_matrix[i]):,})" for i, r in enumerate(all_regions)]
ax.set_yticklabels(ylabels, fontsize=10)
ax.set_title("色彩区 × Modality Coverage (%)")

plt.colorbar(im, ax=ax, shrink=0.7, label="Coverage %")

for i in range(len(all_regions)):
    for j in range(len(modalities)):
        val = mod_matrix[i, j]
        if count_matrix[i] > 0:
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=9,
                    color="white" if val < 40 else "black")
        else:
            ax.text(j, i, "—", ha="center", va="center", fontsize=9, color="gray")

plt.tight_layout()
plt.savefig(OUT / "14_secaiqu_modality.png", dpi=150)
plt.close()
print("✓ 14_secaiqu_modality.png")

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
missing = [r for r in all_regions if region_counts[r] == 0]
under = [r for r in all_regions if 0 < region_counts[r] < 500]
well = [r for r in all_regions if region_counts[r] >= 1000]

if missing:
    print(f"Missing regions: {', '.join(missing)}")
else:
    print("All 11 色彩区 represented!")
if under:
    print(f"Underrepresented (<500): {', '.join(f'{r}({region_counts[r]})' for r in under)}")
if well:
    print(f"Well-represented (≥1000): {', '.join(f'{r}({region_counts[r]:,})' for r in well)}")
print(f"\nCoverage: {len(well)}/11 regions have ≥1000 items")
