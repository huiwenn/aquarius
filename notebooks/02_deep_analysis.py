"""
Notebook 2: Deep Analysis — Deduplication, Cross-Dataset Matching, Hidden Patterns
====================================================================================
Title-based dedup, metadata enrichment via cross-matching, embedding-based clustering,
and statistical anomaly detection.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = ['Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
import re
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "figures"
OUT.mkdir(exist_ok=True)

df = pd.read_parquet(ROOT / "data" / "unified" / "master_table.parquet")
print(f"Loaded {len(df):,} items\n")

# ═══════════════════════════════════════════════════════════════
# PART 1: DEDUPLICATION ANALYSIS
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("PART 1: DEDUPLICATION")
print("=" * 60)

# 1a. Exact title matches across datasets
titled = df[df['title'].notna() & (df['title'].str.strip() != '')].copy()
titled['title_clean'] = titled['title'].str.strip().str.replace(r'[「」『』""''（）()]', '', regex=True)

title_to_datasets = titled.groupby('title_clean')['dataset'].apply(set)
cross_dataset = title_to_datasets[title_to_datasets.apply(len) > 1]
print(f"\nExact title matches across datasets: {len(cross_dataset)}")

# Breakdown by dataset pair
pair_counts = Counter()
for title, datasets in cross_dataset.items():
    ds_list = sorted(datasets)
    for i in range(len(ds_list)):
        for j in range(i+1, len(ds_list)):
            pair_counts[(ds_list[i], ds_list[j])] += 1

print("\nTop cross-dataset overlaps (by shared titles):")
for (d1, d2), count in pair_counts.most_common(15):
    print(f"  {d1} ↔ {d2}: {count} shared titles")

# Visualize overlap matrix
datasets_with_titles = sorted(titled['dataset'].unique())
n_ds = len(datasets_with_titles)
overlap_matrix = np.zeros((n_ds, n_ds), dtype=int)
ds_idx = {d: i for i, d in enumerate(datasets_with_titles)}
for (d1, d2), count in pair_counts.items():
    if d1 in ds_idx and d2 in ds_idx:
        overlap_matrix[ds_idx[d1], ds_idx[d2]] = count
        overlap_matrix[ds_idx[d2], ds_idx[d1]] = count

fig, ax = plt.subplots(figsize=(12, 10))
mask = overlap_matrix > 0
im = ax.imshow(np.log1p(overlap_matrix), cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(n_ds))
ax.set_xticklabels(datasets_with_titles, rotation=45, ha='right', fontsize=8)
ax.set_yticks(range(n_ds))
ax.set_yticklabels(datasets_with_titles, fontsize=8)
for i in range(n_ds):
    for j in range(n_ds):
        if overlap_matrix[i, j] > 0:
            ax.text(j, i, str(overlap_matrix[i, j]), ha='center', va='center', fontsize=7)
ax.set_title('Cross-Dataset Title Overlap (number of shared titles)')
plt.colorbar(im, ax=ax, label='log(count + 1)', shrink=0.6)
plt.tight_layout()
plt.savefig(OUT / "07_title_overlap_matrix.png", dpi=150)
plt.close()
print("✓ 07_title_overlap_matrix.png")

# 1b. Fuzzy title matching — find near-duplicates within datasets
print("\n--- Fuzzy near-duplicates (within datasets) ---")
# Look for titles that differ only in punctuation, numbering, or minor variations
within_dupes = {}
for ds in titled['dataset'].unique():
    ds_titles = titled[titled['dataset'] == ds]['title_clean'].dropna().tolist()
    # Normalize further: remove digits, whitespace
    normalized = {}
    for t in ds_titles:
        norm = re.sub(r'[\d\s_\-]', '', t)
        if norm and len(norm) > 2:
            normalized.setdefault(norm, []).append(t)
    dupes = {k: v for k, v in normalized.items() if len(v) > 1}
    if dupes:
        within_dupes[ds] = dupes

for ds, dupes in sorted(within_dupes.items()):
    if len(dupes) > 3:
        print(f"\n  {ds}: {len(dupes)} fuzzy duplicate groups")
        for norm, titles in list(dupes.items())[:5]:
            print(f"    {titles}")

# 1c. Anthology ↔ MGD deep matching
print("\n--- Anthology ↔ MGD matching (the big overlap) ---")
anth = df[df['dataset'] == 'anthology_chinese_folk_songs'].copy()
mgd = df[df['dataset'] == 'mgd'].copy()

anth_titles = set(anth['title'].dropna())
mgd_titles = set(mgd['title'].dropna())
both = anth_titles & mgd_titles
only_anth = anth_titles - mgd_titles
only_mgd = mgd_titles - anth_titles

print(f"  Anthology titles: {len(anth_titles):,}")
print(f"  MGD titles: {len(mgd_titles):,}")
print(f"  Shared: {len(both):,}")
print(f"  Only in Anthology: {len(only_anth):,}")
print(f"  Only in MGD: {len(only_mgd):,}")

# Check if shared titles also share province
shared_items = titled[titled['title_clean'].isin([t.strip().replace('「','').replace('」','') for t in both])]
if len(shared_items) > 0:
    province_match = 0
    province_mismatch = 0
    for title in list(both)[:500]:
        a_prov = anth[anth['title'] == title]['province'].dropna().unique()
        m_prov = mgd[mgd['title'] == title]['province'].dropna().unique()
        if len(a_prov) > 0 and len(m_prov) > 0:
            if set(a_prov) & set(m_prov):
                province_match += 1
            else:
                province_mismatch += 1
    print(f"  Province agreement on shared titles (sample): {province_match}/{province_match+province_mismatch}")
    if province_mismatch > 0:
        print(f"  Province DISAGREEMENT: {province_mismatch} — these may be different songs with same title!")

# Modality enrichment opportunity
anth_has_midi = anth[anth['title'].isin(both) & (anth['has_midi'] == True)]
mgd_no_midi = mgd[mgd['title'].isin(both)]
print(f"\n  Enrichment opportunity: {len(anth_has_midi)} Anthology items with MIDI match MGD metadata-only items")
print(f"  → Can add MIDI modality to {len(mgd_no_midi)} MGD entries via title matching")


# ═══════════════════════════════════════════════════════════════
# PART 2: HIDDEN PATTERNS IN METADATA
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 2: HIDDEN PATTERNS")
print("=" * 60)

# 2a. Genre × modality availability patterns
print("\n--- Genre × Modality patterns ---")
genre_mod = df.groupby('genre').agg(
    n=('unified_id', 'count'),
    pct_audio=('has_audio', lambda x: (x == True).mean() * 100),
    pct_midi=('has_midi', lambda x: (x == True).mean() * 100),
    pct_xml=('has_musicxml', lambda x: (x == True).mean() * 100),
    pct_lyrics=('has_lyrics', lambda x: (x == True).mean() * 100),
).sort_values('n', ascending=False)
print(genre_mod.round(1).to_string())

fig, ax = plt.subplots(figsize=(10, 6))
genres = genre_mod.index.tolist()
x = np.arange(len(genres))
w = 0.2
for i, (mod, color) in enumerate([('pct_audio', '#e74c3c'), ('pct_midi', '#3498db'),
                                    ('pct_xml', '#2ecc71'), ('pct_lyrics', '#f39c12')]):
    ax.bar(x + i*w, genre_mod[mod], w, label=mod.replace('pct_', '').upper(), color=color, alpha=0.85)
ax.set_xticks(x + 1.5*w)
ax.set_xticklabels(genres, rotation=30, ha='right', fontsize=9)
ax.set_ylabel('Coverage (%)')
ax.set_title('Modality Coverage by Genre')
ax.legend()
plt.tight_layout()
plt.savefig(OUT / "08_genre_modality.png", dpi=150)
plt.close()
print("✓ 08_genre_modality.png")

# 2b. Title character analysis — what can titles tell us?
print("\n--- Title character patterns ---")
titles_all = df['title'].dropna()
char_counter = Counter()
for t in titles_all:
    char_counter.update(t)
print(f"Total unique characters in titles: {len(char_counter)}")
top_chars = char_counter.most_common(30)
print(f"Most common characters: {''.join(c for c, _ in top_chars)}")

# Musical keywords in titles
keywords = {
    '调': 0, '歌': 0, '曲': 0, '舞': 0, '唱': 0,
    '山': 0, '水': 0, '花': 0, '月': 0, '风': 0,
    '情': 0, '爱': 0, '春': 0, '秋': 0, '夜': 0,
    '小': 0, '大': 0, '长': 0, '新': 0, '老': 0,
}
for t in titles_all:
    for k in keywords:
        if k in t:
            keywords[k] += 1

print("\nMusical/Nature keywords in titles:")
sorted_kw = sorted(keywords.items(), key=lambda x: -x[1])
for k, n in sorted_kw:
    if n > 0:
        print(f"  {k}: {n} titles ({n/len(titles_all)*100:.1f}%)")

fig, ax = plt.subplots(figsize=(10, 5))
kw_sorted = sorted(keywords.items(), key=lambda x: -x[1])
chars = [k for k, v in kw_sorted if v > 0]
vals = [v for k, v in kw_sorted if v > 0]
ax.bar(chars, vals, color=plt.cm.Set2(np.linspace(0, 1, len(chars))))
ax.set_ylabel('Number of titles containing character')
ax.set_title('Common Characters in Song Titles')
for i, v in enumerate(vals):
    ax.text(i, v + 20, str(v), ha='center', fontsize=8)
plt.tight_layout()
plt.savefig(OUT / "09_title_keywords.png", dpi=150)
plt.close()
print("✓ 09_title_keywords.png")

# 2c. Instrument family coverage analysis
print("\n--- Bayin (Eight-Sound) family coverage ---")
bayin = df[df['bayin_family'].notna()]['bayin_family'].value_counts()
print(f"Items with bayin family: {df['bayin_family'].notna().sum()}")
for b, n in bayin.items():
    print(f"  {b}: {n}")
missing_bayin = ['stone', 'earth', 'skin', 'wood']
print(f"\nMissing bayin families: {missing_bayin}")
print("→ No percussion (skin/wood), no clay ocarinas (earth), no stone chimes")

# 2d. Key distribution anomalies
print("\n--- Key distribution analysis ---")
key_items = df[df['key'].notna()].copy()
if len(key_items) > 100:
    # Compare folk song key distributions
    kaggle_keys = key_items[key_items['dataset'] == 'traditional_chinese_folk_music_kaggle']['key'].value_counts()
    cnpm_keys = df[df['mode'].notna()].copy()
    print(f"Kaggle folk key distribution (n={len(kaggle_keys.index)}):")
    for k, n in kaggle_keys.items():
        print(f"  {k}: {n} ({n/kaggle_keys.sum()*100:.1f}%)")
    print("\nNote: remarkably uniform distribution across D, A, F, E, G, C")
    print("This is UNUSUAL for Chinese folk music — expect pentatonic bias toward G, D, C")

# 2e. Dataset temporal coverage gaps
print("\n--- Temporal coverage ---")
year_items = df[df['year'].notna()].copy()
print(f"Items with year: {len(year_items)}")
if len(year_items) > 0:
    print(f"  Range: {year_items['year'].min()} - {year_items['year'].max()}")
    print(f"  Datasets: {year_items['dataset'].unique()}")

# 2f. Province × genre cross-tabulation
print("\n--- Province × Genre patterns ---")
prov_genre = df[df['province'].notna()].groupby(['province', 'genre']).size().unstack(fill_value=0)
# Find provinces dominated by a single genre
for prov in prov_genre.index:
    total = prov_genre.loc[prov].sum()
    if total > 50:
        dominant = prov_genre.loc[prov].idxmax()
        pct = prov_genre.loc[prov].max() / total * 100
        if pct > 90:
            print(f"  {prov}: {pct:.0f}% {dominant} (n={total})")

# ═══════════════════════════════════════════════════════════════
# PART 3: TITLE EMBEDDING CLUSTERING
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 3: TITLE EMBEDDING ANALYSIS")
print("=" * 60)

# Use character n-gram TF-IDF for Chinese title similarity (no tokenizer needed)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans

# Sample titles for clustering (use all titled items but cap at 30k for speed)
sample = titled.copy()
if len(sample) > 30000:
    sample = sample.sample(30000, random_state=42)

print(f"Clustering {len(sample)} titled items using character n-gram TF-IDF...")
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), max_features=5000)
X = vectorizer.fit_transform(sample['title_clean'].fillna(''))

# Reduce to 50D with SVD
svd = TruncatedSVD(n_components=50, random_state=42)
X_reduced = svd.fit_transform(X)
print(f"SVD explained variance: {svd.explained_variance_ratio_.sum():.1%}")

# K-means clustering
n_clusters = 15
km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
sample['cluster'] = km.fit_predict(X_reduced)

# Analyze clusters
print(f"\n--- {n_clusters} title clusters ---")
for c in range(n_clusters):
    cluster_items = sample[sample['cluster'] == c]
    n = len(cluster_items)
    top_datasets = cluster_items['dataset'].value_counts().head(3)
    top_genres = cluster_items['genre'].value_counts().head(2)
    sample_titles = cluster_items['title'].head(5).tolist()

    # Find common characters
    char_counter = Counter()
    for t in cluster_items['title_clean'].dropna():
        char_counter.update(t)
    common_chars = ''.join(c for c, _ in char_counter.most_common(8))

    print(f"\n  Cluster {c} (n={n}):")
    print(f"    Common chars: {common_chars}")
    print(f"    Datasets: {', '.join(f'{d}({n})' for d, n in top_datasets.items())}")
    print(f"    Genres: {', '.join(f'{g}({n})' for g, n in top_genres.items())}")
    print(f"    Samples: {sample_titles[:3]}")

# 2D visualization with SVD
svd2d = TruncatedSVD(n_components=2, random_state=42)
X_2d = svd2d.fit_transform(X)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Color by dataset
ax = axes[0]
ds_colors = {d: plt.cm.tab20(i/20) for i, d in enumerate(sample['dataset'].unique())}
for ds in sample['dataset'].unique():
    mask = sample['dataset'] == ds
    ax.scatter(X_2d[mask, 0], X_2d[mask, 1], s=3, alpha=0.4,
              label=ds, color=ds_colors[ds])
ax.set_title('Title Embeddings by Dataset')
ax.legend(fontsize=6, markerscale=3, loc='upper right', ncol=2)

# Color by genre
ax = axes[1]
genre_colors = {g: plt.cm.Set1(i/10) for i, g in enumerate(sample['genre'].unique())}
for g in sample['genre'].unique():
    mask = sample['genre'] == g
    ax.scatter(X_2d[mask, 0], X_2d[mask, 1], s=3, alpha=0.4,
              label=g, color=genre_colors[g])
ax.set_title('Title Embeddings by Genre')
ax.legend(fontsize=7, markerscale=3, loc='upper right')

plt.tight_layout()
plt.savefig(OUT / "10_title_embeddings.png", dpi=150)
plt.close()
print("✓ 10_title_embeddings.png")


# ═══════════════════════════════════════════════════════════════
# PART 4: CROSS-DATASET ENRICHMENT POTENTIAL
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 4: ENRICHMENT POTENTIAL")
print("=" * 60)

# 4a. Items where we can add modalities via cross-matching
print("\n--- Cross-dataset modality enrichment ---")

# For each shared title, what modalities exist in each dataset?
enrichment_ops = []
for title in list(both)[:2000]:  # Anthology ↔ MGD overlap
    a_items = anth[anth['title'] == title]
    m_items = mgd[mgd['title'] == title]

    a_mods = set()
    if (a_items['has_audio'] == True).any(): a_mods.add('audio')
    if (a_items['has_midi'] == True).any(): a_mods.add('midi')
    if (a_items['has_musicxml'] == True).any(): a_mods.add('musicxml')

    m_mods = set()
    if (m_items['has_audio'] == True).any(): m_mods.add('audio')
    if (m_items['has_midi'] == True).any(): m_mods.add('midi')
    if (m_items['has_musicxml'] == True).any(): m_mods.add('musicxml')

    # What can Anthology add to MGD?
    a_can_add = a_mods - m_mods
    m_can_add = m_mods - a_mods

    if a_can_add:
        enrichment_ops.append(('anthology→mgd', title, a_can_add))
    if m_can_add:
        enrichment_ops.append(('mgd→anthology', title, m_can_add))

print(f"Enrichment operations from title matching:")
direction_counts = Counter(op[0] for op in enrichment_ops)
mod_counts = Counter()
for _, _, mods in enrichment_ops:
    for m in mods:
        mod_counts[m] += 1
for d, n in direction_counts.items():
    print(f"  {d}: {n} items")
print(f"  Modalities addable: {dict(mod_counts)}")

# 4b. Folk song metadata enrichment: MGD province → match Anthology songs
print("\n--- Province metadata enrichment ---")
anth_no_prov = anth[(anth['province'].isna()) & (anth['title'].notna())]
mgd_has_prov = mgd[mgd['province'].notna()]
can_add_prov = anth_no_prov[anth_no_prov['title'].isin(mgd_has_prov['title'].dropna())]
print(f"  Anthology items without province: {len(anth_no_prov)}")
print(f"  Of those, matchable to MGD with province: {len(can_add_prov)}")

# 4c. POP909 enrichment potential
print("\n--- POP909 potential enrichment ---")
pop = df[df['dataset'] == 'pop909']
print(f"  POP909 songs: {len(pop)}")
print(f"  With artist: {pop['artist'].notna().sum()}")
print(f"  Without year: {pop['year'].isna().sum()} → lookup via artist+title in MusicBrainz")
print(f"  Without audio: {(pop['has_audio'] != True).sum()} → MIDI→audio synthesis candidate")
print(f"  With chord labels: {(pop['chord_labels'] == True).sum()}")

# ═══════════════════════════════════════════════════════════════
# PART 5: ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PART 5: ANOMALIES & SURPRISES")
print("=" * 60)

# 5a. Unified IDs that aren't unique
uid_dupes = df[df.duplicated('unified_id', keep=False)]
if len(uid_dupes) > 0:
    print(f"\n⚠ Duplicate unified_ids: {uid_dupes['unified_id'].nunique()} IDs, {len(uid_dupes)} rows")
    for uid in uid_dupes['unified_id'].unique()[:5]:
        rows = uid_dupes[uid_dupes['unified_id'] == uid]
        print(f"  {uid} → {len(rows)} rows: {rows['dataset'].tolist()}")
else:
    print("\n✓ All unified_ids are unique")

# 5b. Items flagged as metadata-only but actually have modalities
meta_only = df[df['has_metadata_only'] == True]
meta_but_has = meta_only[(meta_only['has_audio'] == True) | (meta_only['has_midi'] == True) | (meta_only['has_musicxml'] == True)]
if len(meta_but_has) > 0:
    print(f"\n⚠ {len(meta_but_has)} items marked metadata-only but HAVE modalities!")
else:
    print("✓ metadata-only flag consistent")

# 5c. Very short or very long durations
dur = df[df['duration_seconds'].notna() & (df['duration_seconds'] > 0)]
if len(dur) > 0:
    print(f"\nDuration stats (n={len(dur)}):")
    print(f"  Min: {dur['duration_seconds'].min():.1f}s")
    print(f"  Max: {dur['duration_seconds'].max():.1f}s")
    print(f"  Mean: {dur['duration_seconds'].mean():.1f}s")
    print(f"  Median: {dur['duration_seconds'].median():.1f}s")
    short = dur[dur['duration_seconds'] < 1]
    if len(short) > 0:
        print(f"  ⚠ {len(short)} items < 1 second")

# 5d. Language distribution surprise
print(f"\nLanguage distribution:")
for lang, n in df['language'].value_counts().items():
    print(f"  {lang}: {n:,}")
print(f"  (unlabeled): {df['language'].isna().sum():,}")

# 5e. Country anomaly
non_china = df[df['country'] != 'China']
if len(non_china) > 0:
    print(f"\nNon-China items: {len(non_china)}")
    print(f"  Countries: {non_china['country'].value_counts().to_dict()}")
    print(f"  Datasets: {non_china['dataset'].value_counts().to_dict()}")
    print(f"  → PMEmo is Western pop music used for emotion research — not Chinese music per se")

# 5f. Singleton datasets (very small contributions)
ds_counts = df['dataset'].value_counts()
small_ds = ds_counts[ds_counts < 20]
print(f"\nSmall datasets (<20 items): {len(small_ds)}")
for ds, n in small_ds.items():
    print(f"  {ds}: {n} items")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
