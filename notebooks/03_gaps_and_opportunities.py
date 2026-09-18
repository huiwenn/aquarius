"""
Notebook 3: Gaps, Low-Hanging Fruit & Conversion Opportunities
===============================================================
Identifies actionable opportunities for modality conversion, metadata imputation,
and data quality improvements.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = ['Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "figures"
OUT.mkdir(exist_ok=True)

df = pd.read_parquet(ROOT / "data" / "unified" / "master_table.parquet")
print(f"Loaded {len(df):,} items\n")

# ═══════════════════════════════════════════════════════════════
# 1. MODALITY CONVERSION LANDSCAPE
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("MODALITY CONVERSION OPPORTUNITIES")
print("=" * 60)

# Classify each item by what conversions are possible
df['can_synth_audio'] = (df['has_midi'] == True) & (df['has_audio'] != True)
df['can_transcribe_midi'] = (df['has_audio'] == True) & (df['has_midi'] != True)
df['can_gen_musicxml'] = (df['has_midi'] == True) & (df['has_musicxml'] != True)
df['can_extract_key'] = ((df['has_midi'] == True) | (df['has_musicxml'] == True)) & (df['key'].isna())
df['can_detect_mode'] = ((df['has_midi'] == True) | (df['has_musicxml'] == True)) & (df['mode'].isna())

conversions = {
    'MIDI → Audio (synthesis)': df['can_synth_audio'].sum(),
    'Audio → MIDI (transcription)': df['can_transcribe_midi'].sum(),
    'MIDI → MusicXML (score gen)': df['can_gen_musicxml'].sum(),
    'MIDI/XML → Key detection': df['can_extract_key'].sum(),
    'MIDI/XML → Mode detection': df['can_detect_mode'].sum(),
}

print("\nConversion opportunities:")
for conv, n in sorted(conversions.items(), key=lambda x: -x[1]):
    print(f"  {conv}: {n:,} items")

fig, ax = plt.subplots(figsize=(10, 5))
labels = list(conversions.keys())
values = list(conversions.values())
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
bars = ax.barh(labels, values, color=colors, alpha=0.85)
ax.set_xlabel('Number of items')
ax.set_title('Low-Hanging Fruit: Modality Conversion Opportunities')
for bar, val in zip(bars, values):
    ax.text(val + 50, bar.get_y() + bar.get_height()/2, f'{val:,}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(OUT / "11_conversion_opportunities.png", dpi=150)
plt.close()
print("✓ 11_conversion_opportunities.png")

# Breakdown by dataset
print("\nPer-dataset conversion breakdown:")
conv_cols = ['can_synth_audio', 'can_transcribe_midi', 'can_gen_musicxml',
             'can_extract_key', 'can_detect_mode']
conv_by_ds = df.groupby('dataset')[conv_cols].sum()
conv_by_ds = conv_by_ds[conv_by_ds.sum(axis=1) > 0].sort_values('can_extract_key', ascending=False)
print(conv_by_ds.to_string())

# ═══════════════════════════════════════════════════════════════
# 2. DEDUPLICATION IMPACT ANALYSIS
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("DEDUPLICATION IMPACT")
print("=" * 60)

# 2a. Anthology ↔ MGD: the elephant in the room
anth = df[df['dataset'] == 'anthology_chinese_folk_songs']
mgd = df[df['dataset'] == 'mgd']

shared_titles = set(anth['title'].dropna()) & set(mgd['title'].dropna())
print(f"\nAnthology ↔ MGD overlap: {len(shared_titles):,} shared titles")

# What does MGD add that Anthology doesn't?
mgd_shared = mgd[mgd['title'].isin(shared_titles)]
anth_shared = anth[anth['title'].isin(shared_titles)]

# Check metadata enrichment
mgd_has_key = mgd_shared['key'].notna().sum()
anth_has_key = anth_shared['key'].notna().sum()
mgd_has_subgenre = mgd_shared['sub_genre'].notna().sum()
mgd_has_folk_type = mgd_shared['folk_song_type'].notna().sum()

print(f"\nFor {len(shared_titles):,} shared items:")
print(f"  MGD provides key: {mgd_has_key}")
print(f"  MGD provides sub_genre: {mgd_has_subgenre}")
print(f"  Anthology provides MIDI: {(anth_shared['has_midi']==True).sum()}")
print(f"  Anthology provides MusicXML: {(anth_shared['has_musicxml']==True).sum()}")

print(f"\n→ After merging: {len(shared_titles):,} unified folk song entries,")
print(f"  each with BOTH metadata (from MGD) AND symbolic data (from Anthology)")

# 2b. Duplicate unified_ids
uid_dupes = df[df.duplicated('unified_id', keep=False)]
print(f"\n⚠ {uid_dupes['unified_id'].nunique()} duplicate unified_ids ({len(uid_dupes)} rows)")
print(f"  All in: {uid_dupes['dataset'].unique()}")
print(f"  These are Anthology items appearing in both lyrics-included and melody-only subsets")

# 2c. M4Singer ↔ GTSinger ↔ POP909 overlap
singing_ds = df[df['dataset'].isin(['m4singer', 'gtsinger', 'pop909'])]
singing_titles = singing_ds.groupby('title')['dataset'].apply(set)
singing_multi = singing_titles[singing_titles.apply(len) > 1]
print(f"\nSinging dataset overlaps: {len(singing_multi)} shared titles")
print("  → Same songs recorded by different singers — NOT duplicates, but linkable")
for title, datasets in singing_multi.head(10).items():
    print(f"    「{title}」→ {', '.join(sorted(datasets))}")

# ═══════════════════════════════════════════════════════════════
# 3. METADATA IMPUTATION ANALYSIS
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("METADATA IMPUTATION POTENTIAL")
print("=" * 60)

# 3a. Which fields are most empty and most fillable?
fillable_fields = {
    'key': ('MIDI/XML key detection', df['key'].isna().sum(),
            ((df['has_midi']==True) | (df['has_musicxml']==True)).sum()),
    'mode': ('Chinese mode detection', df['mode'].isna().sum(),
             ((df['has_midi']==True) | (df['has_musicxml']==True)).sum()),
    'year': ('MusicBrainz/Discogs lookup', df['year'].isna().sum(),
             df[(df['year'].isna()) & (df['artist'].notna())].shape[0]),
    'artist': ('Title→artist DB lookup', df['artist'].isna().sum(),
               df[(df['artist'].isna()) & (df['title'].notna()) & (df['genre']=='C-pop')].shape[0]),
    'instrument': ('Audio classification', df['instrument'].isna().sum(),
                   df[(df['instrument'].isna()) & (df['has_audio']==True)].shape[0]),
    'duration_seconds': ('Audio/MIDI analysis', df['duration_seconds'].isna().sum(),
                         ((df['has_audio']==True) | (df['has_midi']==True)).sum()),
}

print("\nField | Missing | Fillable | Method")
print("-" * 65)
for field, (method, missing, fillable) in sorted(fillable_fields.items(), key=lambda x: -x[1][2]):
    fill_pct = fillable / missing * 100 if missing > 0 else 0
    print(f"  {field:20s} | {missing:6,} | {fillable:6,} ({fill_pct:5.1f}%) | {method}")

# 3b. Pentatonic mode — the crown jewel
print("\n--- Pentatonic mode detection (the #1 opportunity) ---")
mode_items = df[df['mode'].notna()]
no_mode_symbolic = df[(df['mode'].isna()) & ((df['has_midi']==True) | (df['has_musicxml']==True))]
print(f"  Items with mode labels: {len(mode_items)} (all from CNPM)")
print(f"  Items without mode but WITH symbolic data: {len(no_mode_symbolic):,}")
print(f"    → {len(no_mode_symbolic):,} items can get pentatonic mode estimated")
print(f"    Breakdown:")
for ds, n in no_mode_symbolic['dataset'].value_counts().items():
    print(f"      {ds}: {n:,}")

# ═══════════════════════════════════════════════════════════════
# 4. COVERAGE GAPS — WHAT'S MISSING?
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("COVERAGE GAPS")
print("=" * 60)

# 4a. Musical tradition gaps
print("\n--- Missing musical traditions ---")
print("  ✗ Percussion (drums, gongs, cymbals, wooden fish) — no dataset at all")
print("  ✗ Kunqu Opera — only Jingju (Beijing Opera) represented")
print("  ✗ Cantonese Opera — no representation")
print("  ✗ Chinese orchestra/ensemble recordings — all datasets are solo or pop")
print("  ✗ Buddhist/Taoist ritual music")
print("  ✗ Minority-specific traditions beyond Xinjiang folk songs")

# 4b. Temporal gap
print("\n--- Temporal coverage ---")
items_with_time = df[df['year'].notna() | df['dynasty'].notna() | df['period'].notna()]
print(f"  Items with ANY temporal info: {len(items_with_time)} ({len(items_with_time)/len(df)*100:.1f}%)")
print(f"  → 99.8% of items have NO temporal context")

# 4c. Format diversity within genres
print("\n--- Format gaps by genre ---")
for genre in df['genre'].value_counts().head(6).index:
    g = df[df['genre'] == genre]
    mods = []
    if (g['has_audio'] == True).any(): mods.append(f"audio({(g['has_audio']==True).sum()})")
    if (g['has_midi'] == True).any(): mods.append(f"MIDI({(g['has_midi']==True).sum()})")
    if (g['has_musicxml'] == True).any(): mods.append(f"XML({(g['has_musicxml']==True).sum()})")
    if (g['has_lyrics'] == True).any(): mods.append(f"lyrics({(g['has_lyrics']==True).sum()})")
    missing = []
    if not (g['has_audio'] == True).any(): missing.append("audio")
    if not (g['has_midi'] == True).any(): missing.append("MIDI")
    if not (g['has_musicxml'] == True).any(): missing.append("XML")
    print(f"  {genre} ({len(g):,}): has [{', '.join(mods)}]" +
          (f"  MISSING: {', '.join(missing)}" if missing else ""))

# ═══════════════════════════════════════════════════════════════
# 5. ACTIONABLE LOW-HANGING FRUIT (ranked)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("RANKED LOW-HANGING FRUIT")
print("=" * 60)

fruits = [
    (1, "Merge Anthology ↔ MGD", "6,400 songs gain both MIDI/MusicXML AND province/key metadata", "~2 hours", "critical"),
    (2, "Key detection on MIDI/XML", "18,665 items get key estimated via Krumhansl-Schmuckler", "~4 hours", "high"),
    (3, "Pentatonic mode detection", "18,665 items get Chinese mode estimated, trained on 287 CNPM examples", "~1 day", "critical"),
    (4, "Fix 276 duplicate IDs", "Anthology loader bug: items in both lyrics-included/ and melody-only/ get same ID", "~30 min", "quick"),
    (5, "POP909 year lookup", "909 songs get release year via MusicBrainz (artist+title known)", "~2 hours", "medium"),
    (6, "MIDI→Audio synthesis", "9,383 folk songs get synthesized audio via FluidSynth", "~1 day", "medium"),
    (7, "Audio→MIDI transcription", "14,524 audio clips get MIDI via Basic Pitch", "~2 days", "medium"),
    (8, "Remove/flag PMEmo", "794 items are Western pop, not Chinese music — flag or exclude", "~15 min", "quick"),
    (9, "Duration extraction", "~47,000 items missing duration — extract from audio/MIDI files", "~4 hours", "medium"),
    (10, "Cross-link singing datasets", "~200 songs shared across M4Singer/GTSinger/POP909 — multi-singer linkage", "~2 hours", "medium"),
]

print(f"\n{'#':>2} {'Effort':>8} {'Impact':>8}  Action → Result")
print("-" * 80)
for rank, action, result, effort, impact in fruits:
    print(f"{rank:>2}. {effort:>8} {impact:>8}  {action}")
    print(f"{'':>22}→ {result}")

# ═══════════════════════════════════════════════════════════════
# 6. SUMMARY FIGURE — THE AQUARIUS LANDSCAPE
# ═══════════════════════════════════════════════════════════════

# Create a comprehensive summary figure
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Panel A: Items by genre with modality stacking
ax = axes[0, 0]
genre_counts = df['genre'].value_counts()
genre_audio = df[df['has_audio']==True]['genre'].value_counts().reindex(genre_counts.index, fill_value=0)
genre_midi = df[df['has_midi']==True]['genre'].value_counts().reindex(genre_counts.index, fill_value=0)
genre_xml = df[df['has_musicxml']==True]['genre'].value_counts().reindex(genre_counts.index, fill_value=0)
genre_meta = genre_counts - genre_audio - genre_midi - genre_xml
genre_meta = genre_meta.clip(lower=0)

x = np.arange(len(genre_counts))
ax.bar(x, genre_audio, label='Audio', color='#e74c3c', alpha=0.8)
ax.bar(x, genre_midi, bottom=genre_audio, label='MIDI', color='#3498db', alpha=0.8)
ax.bar(x, genre_xml, bottom=genre_audio+genre_midi, label='MusicXML', color='#2ecc71', alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(genre_counts.index, rotation=40, ha='right', fontsize=8)
ax.set_ylabel('Items')
ax.set_title('A. Items by Genre & Modality')
ax.legend(fontsize=8)

# Panel B: Instrument coverage (bayin families)
ax = axes[0, 1]
all_bayin = ['silk', 'bamboo', 'gourd', 'metal', 'stone', 'earth', 'skin', 'wood']
bayin_counts = df[df['bayin_family'].notna()]['bayin_family'].value_counts().reindex(all_bayin, fill_value=0)
colors_bayin = ['#2ecc71' if v > 0 else '#e74c3c' for v in bayin_counts.values]
bars = ax.bar(all_bayin, bayin_counts.values, color=colors_bayin, alpha=0.8, edgecolor='white')
ax.set_ylabel('Items')
ax.set_title('B. Bayin (Eight-Sound) Family Coverage')
for bar, val in zip(bars, bayin_counts.values):
    label = str(val) if val > 0 else 'MISSING'
    ax.text(bar.get_x() + bar.get_width()/2, max(val, 100), label,
            ha='center', va='bottom', fontsize=9,
            color='black' if val > 0 else 'red', fontweight='bold')

# Panel C: Conversion opportunity waterfall
ax = axes[1, 0]
items_total = len(df)
has_audio = (df['has_audio'] == True).sum()
has_midi = (df['has_midi'] == True).sum()
has_xml = (df['has_musicxml'] == True).sum()
has_any = ((df['has_audio'] == True) | (df['has_midi'] == True) | (df['has_musicxml'] == True)).sum()
meta_only_count = (df['has_metadata_only'] == True).sum()

categories = ['Total', 'Has Audio', 'Has MIDI', 'Has XML', 'Has Any\nModality', 'Metadata\nOnly']
vals = [items_total, has_audio, has_midi, has_xml, has_any, meta_only_count]
colors_wf = ['#34495e', '#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#95a5a6']
ax.bar(categories, vals, color=colors_wf, alpha=0.85)
ax.set_ylabel('Items')
ax.set_title('C. Modality Availability')
for i, v in enumerate(vals):
    ax.text(i, v + 300, f'{v:,}\n({v/items_total*100:.0f}%)', ha='center', fontsize=8)

# Panel D: What's fillable
ax = axes[1, 1]
fill_labels = ['Key\ndetection', 'Mode\ndetection', 'Duration\nextraction', 'Audio\nsynthesis', 'MIDI\ntranscription']
fill_vals = [18665, 18665, 47272, 9383, 14524]
fill_colors = ['#f39c12', '#9b59b6', '#1abc9c', '#e74c3c', '#3498db']
ax.bar(fill_labels, fill_vals, color=fill_colors, alpha=0.85)
ax.set_ylabel('Items fillable')
ax.set_title('D. Imputation & Conversion Potential')
for i, v in enumerate(fill_vals):
    ax.text(i, v + 200, f'{v:,}', ha='center', fontsize=9)

plt.suptitle('Aquarius Dataset Landscape — 60,032 Items Across 23 Datasets', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(OUT / "12_landscape_summary.png", dpi=150, bbox_inches='tight')
plt.close()
print("\n✓ 12_landscape_summary.png")

print("\n" + "=" * 60)
print("NOTEBOOK 3 COMPLETE")
print("=" * 60)
