"""
Notebook 1: Aquarius Dataset — Overview & Landscape
=====================================================
Overall statistics, dataset composition, modality coverage, and metadata distributions.
Run: conda activate py312 && python notebooks/01_overview.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "figures"
OUT.mkdir(exist_ok=True)

df = pd.read_parquet(ROOT / "data" / "unified" / "master_table.parquet")
print(f"Master table: {len(df):,} items, {df['dataset'].nunique()} datasets, {len(df.columns)} columns\n")

# ─────────────────────────────────────────────────────────────
# 1. Dataset size distribution (log scale bar chart)
# ─────────────────────────────────────────────────────────────
ds_counts = df['dataset'].value_counts()
fig, ax = plt.subplots(figsize=(12, 6))
colors = plt.cm.Set3(np.linspace(0, 1, len(ds_counts)))
bars = ax.barh(range(len(ds_counts)), ds_counts.values, color=colors)
ax.set_yticks(range(len(ds_counts)))
ax.set_yticklabels(ds_counts.index, fontsize=9)
ax.set_xscale('log')
ax.set_xlabel('Number of items (log scale)')
ax.set_title('Dataset Sizes in Aquarius')
for bar, val in zip(bars, ds_counts.values):
    ax.text(val * 1.1, bar.get_y() + bar.get_height()/2, f'{val:,}',
            va='center', fontsize=8)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(OUT / "01_dataset_sizes.png", dpi=150)
plt.close()
print("✓ 01_dataset_sizes.png")

# ─────────────────────────────────────────────────────────────
# 2. Granularity breakdown
# ─────────────────────────────────────────────────────────────
gran = df['granularity'].value_counts()
print("\nGranularity:")
for g, n in gran.items():
    print(f"  {g}: {n:,} ({n/len(df)*100:.1f}%)")

# ─────────────────────────────────────────────────────────────
# 3. Modality coverage — stacked bar per dataset
# ─────────────────────────────────────────────────────────────
modalities = ['has_audio', 'has_midi', 'has_musicxml', 'has_lyrics']
mod_df = df.groupby('dataset')[modalities].apply(
    lambda x: (x == True).sum()
).reindex(ds_counts.index)

fig, ax = plt.subplots(figsize=(12, 7))
bottom = np.zeros(len(mod_df))
cmap = {'has_audio': '#e74c3c', 'has_midi': '#3498db', 'has_musicxml': '#2ecc71', 'has_lyrics': '#f39c12'}
for mod in modalities:
    vals = mod_df[mod].values.astype(float)
    pcts = vals / ds_counts.values * 100
    ax.barh(range(len(mod_df)), pcts, left=bottom,
            label=mod.replace('has_', '').upper(), color=cmap[mod], alpha=0.85)
    bottom += pcts
ax.set_yticks(range(len(mod_df)))
ax.set_yticklabels(mod_df.index, fontsize=9)
ax.set_xlabel('Coverage (%)')
ax.set_title('Modality Coverage by Dataset')
ax.legend(loc='lower right')
ax.set_xlim(0, max(bottom) * 1.05)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(OUT / "02_modality_coverage.png", dpi=150)
plt.close()
print("✓ 02_modality_coverage.png")

# ─────────────────────────────────────────────────────────────
# 4. Genre distribution (treemap-like)
# ─────────────────────────────────────────────────────────────
genre_counts = df['genre'].value_counts()
print("\nGenre distribution:")
for g, n in genre_counts.items():
    print(f"  {g}: {n:,} ({n/len(df)*100:.1f}%)")

fig, ax = plt.subplots(figsize=(10, 6))
wedges, texts, autotexts = ax.pie(
    genre_counts.values, labels=None, autopct='%1.1f%%',
    colors=plt.cm.Pastel1(np.linspace(0, 1, len(genre_counts))),
    pctdistance=0.8, startangle=90
)
ax.legend(wedges, [f"{g} ({n:,})" for g, n in genre_counts.items()],
          loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
ax.set_title('Genre Distribution')
plt.tight_layout()
plt.savefig(OUT / "03_genre_pie.png", dpi=150, bbox_inches='tight')
plt.close()
print("✓ 03_genre_pie.png")

# ─────────────────────────────────────────────────────────────
# 5. Instrument distribution
# ─────────────────────────────────────────────────────────────
inst = df[df['instrument'].notna()]['instrument'].value_counts().head(25)
fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(range(len(inst)), inst.values, color=plt.cm.viridis(np.linspace(0.2, 0.8, len(inst))))
ax.set_yticks(range(len(inst)))
ax.set_yticklabels(inst.index, fontsize=9)
ax.set_xlabel('Number of items')
ax.set_title(f'Top {len(inst)} Instruments ({df["instrument"].notna().sum():,} items with instrument labels)')
ax.invert_yaxis()
for i, v in enumerate(inst.values):
    ax.text(v + 10, i, str(v), va='center', fontsize=8)
plt.tight_layout()
plt.savefig(OUT / "04_instruments.png", dpi=150)
plt.close()
print("✓ 04_instruments.png")

# ─────────────────────────────────────────────────────────────
# 6. Province heatmap (for folk music)
# ─────────────────────────────────────────────────────────────
prov = df[df['province'].notna()]['province'].value_counts().head(35)
print(f"\nProvince coverage: {df['province'].notna().sum():,} items, {df['province'].nunique()} provinces")
fig, ax = plt.subplots(figsize=(12, 8))
ax.barh(range(len(prov)), prov.values, color=plt.cm.YlOrRd(np.linspace(0.2, 0.9, len(prov))))
ax.set_yticks(range(len(prov)))
ax.set_yticklabels(prov.index, fontsize=9)
ax.set_xlabel('Number of items')
ax.set_title('Geographic Distribution (by Province)')
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(OUT / "05_provinces.png", dpi=150)
plt.close()
print("✓ 05_provinces.png")

# ─────────────────────────────────────────────────────────────
# 7. Metadata sparsity heatmap (dataset × field)
# ─────────────────────────────────────────────────────────────
meta_fields = ['title', 'artist', 'composer', 'year', 'province', 'key', 'mode',
               'instrument', 'tempo_bpm', 'duration_seconds', 'language',
               'playing_technique', 'singing_technique', 'role_type', 'shengqiang']
sparse = df.groupby('dataset')[meta_fields].apply(
    lambda x: x.notna().mean()
).reindex(ds_counts.index)

fig, ax = plt.subplots(figsize=(14, 8))
im = ax.imshow(sparse.values, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax.set_xticks(range(len(meta_fields)))
ax.set_xticklabels(meta_fields, rotation=45, ha='right', fontsize=9)
ax.set_yticks(range(len(sparse)))
ax.set_yticklabels(sparse.index, fontsize=9)
ax.set_title('Metadata Coverage (green = complete, red = empty)')
plt.colorbar(im, ax=ax, shrink=0.6, label='Fill rate')
# Add text annotations
for i in range(len(sparse)):
    for j in range(len(meta_fields)):
        val = sparse.values[i, j]
        if val > 0:
            ax.text(j, i, f'{val:.0%}', ha='center', va='center', fontsize=7,
                    color='white' if val < 0.4 else 'black')
plt.tight_layout()
plt.savefig(OUT / "06_metadata_sparsity.png", dpi=150)
plt.close()
print("✓ 06_metadata_sparsity.png")

# ─────────────────────────────────────────────────────────────
# 8. Key/mode distribution
# ─────────────────────────────────────────────────────────────
key_dist = df[df['key'].notna()]['key'].value_counts()
print(f"\nKey distribution ({df['key'].notna().sum()} items):")
for k, n in key_dist.items():
    print(f"  {k}: {n}")

mode_dist = df[df['mode'].notna()]['mode'].value_counts().head(20)
print(f"\nMode distribution ({df['mode'].notna().sum()} items, top 20):")
for m, n in mode_dist.head(10).items():
    print(f"  {m}: {n}")

# ─────────────────────────────────────────────────────────────
# 9. License distribution
# ─────────────────────────────────────────────────────────────
lic = df.groupby('license').size().sort_values(ascending=False)
print("\nLicense distribution:")
for l, n in lic.items():
    print(f"  {l}: {n:,} ({n/len(df)*100:.1f}%)")

# ─────────────────────────────────────────────────────────────
# 10. Cross-dataset overlap analysis (by title)
# ─────────────────────────────────────────────────────────────
titled = df[df['title'].notna() & (df['title'] != '')].copy()
title_datasets = titled.groupby('title')['dataset'].apply(set)
multi = title_datasets[title_datasets.apply(len) > 1]
print(f"\n=== Title overlap ===")
print(f"Titled items: {len(titled):,}")
print(f"Unique titles: {titled['title'].nunique():,}")
print(f"Titles appearing in multiple datasets: {len(multi)}")
if len(multi) > 0:
    print("Examples:")
    for title, datasets in multi.head(15).items():
        counts = titled[titled['title'] == title].groupby('dataset').size()
        detail = ', '.join(f"{d}({n})" for d, n in counts.items())
        print(f"  「{title}」→ {detail}")

# ─────────────────────────────────────────────────────────────
# 11. Summary stats
# ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("AQUARIUS DATASET SUMMARY")
print("="*60)
print(f"Total items:     {len(df):,}")
print(f"Datasets:        {df['dataset'].nunique()}")
print(f"With audio:      {(df['has_audio']==True).sum():,} ({(df['has_audio']==True).sum()/len(df)*100:.1f}%)")
print(f"With MIDI:       {(df['has_midi']==True).sum():,} ({(df['has_midi']==True).sum()/len(df)*100:.1f}%)")
print(f"With MusicXML:   {(df['has_musicxml']==True).sum():,} ({(df['has_musicxml']==True).sum()/len(df)*100:.1f}%)")
print(f"With lyrics:     {(df['has_lyrics']==True).sum():,} ({(df['has_lyrics']==True).sum()/len(df)*100:.1f}%)")
print(f"Metadata-only:   {(df['has_metadata_only']==True).sum():,} ({(df['has_metadata_only']==True).sum()/len(df)*100:.1f}%)")
print(f"Unique titles:   {titled['title'].nunique():,}")
print(f"Unique artists:  {df['artist'].nunique()}")
print(f"Unique instruments: {df['instrument'].nunique()}")
print(f"Genres:          {df['genre'].nunique()}")
print(f"Provinces:       {df['province'].nunique()}")
print("="*60)

print(f"\nAll figures saved to {OUT}/")
