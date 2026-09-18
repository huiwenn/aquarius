# Aquarius EDA: What 60,000 Items of Chinese Music Actually Look Like

## The Big Picture

Aquarius pulls together 23 datasets into a single table of 60,032 items spanning folk songs, traditional instrumental music, C-pop, Beijing Opera, and a handful of smaller traditions. On paper, that sounds like a lot. In practice, the picture is more complicated — and more interesting — than raw numbers suggest.

The dataset is dominated by two collections: MGD (31,761 folk song metadata entries) and FolkMusic/Zenodo (11,966 instrument clips). Together they account for 73% of everything. The remaining 21 datasets split the other 16,000 items across a wide range of genres and formats (Figure 1).

![Dataset sizes](figures/01_dataset_sizes.png)
*Figure 1: Dataset sizes on a log scale. MGD dwarfs everything else, but it's metadata-only — no audio, no scores.*

This creates a strange asymmetry: the biggest chunk of the database has no actual music data attached to it. 57% of all items (34,135) are metadata-only, with no audio, MIDI, or score files. The items that do have music data tend to be small, specialized collections.

## The Modality Problem

The metadata sparsity heatmap (Figure 2) tells the real story. Each row is a dataset, each column is a metadata field, and the color shows how complete it is. The sea of red is striking.

![Metadata sparsity](figures/06_metadata_sparsity.png)
*Figure 2: Metadata coverage across datasets. Green cells are fully populated, red cells are completely empty. Most of the table is red.*

A few things jump out:

- **Title** is well-covered (74%) but everything else drops off fast: artist (3%), key (4%), mode (0.5%), year (0.1%).
- **Province** looks great at 71%, but that's almost entirely MGD contributing its geographic labels.
- **Instrument** is at 25%, boosted by FolkMusic/Zenodo's 11,966 labeled clips.
- **Temporal data is nearly absent.** Only 41 items in the entire database have a year attached (all from CCOM-HuQin, ranging 1917–2017). We know roughly *nothing* about when 99.8% of these pieces were composed or recorded.
- **CCOM-HuQin** is the only dataset with meaningful coverage across multiple metadata fields — title, artist, composer, year, province, key, instrument, playing technique. It only has 159 items, but it's the richest per-item.

The genre-by-modality breakdown reveals a structural gap: **folk songs have MIDI but no audio, while instrumental recordings have audio but no MIDI.** Almost no genre has all modalities covered (Figure 3).

![Genre × modality](figures/08_genre_modality.png)
*Figure 3: Modality coverage by genre. Folk songs are rich in symbolic data; instrumental music is rich in audio. Barely any overlap.*

## The Anthology–MGD Elephant

The single most important finding is the massive overlap between two folk song collections. The Anthology of Chinese Folk Songs and the MGD dataset share **6,402 song titles** — that's 74% of Anthology's 8,654 items appearing in MGD's 31,761.

But they're not duplicates in the traditional sense. They're complementary:

- **Anthology** has the music: MIDI files and MusicXML scores for each song.
- **MGD** has the metadata: province, location, and (in some cases) genre sub-type labels.

Right now they sit as separate entries in the table. Merging them would instantly create 6,400 richly annotated folk songs with both symbolic music data *and* geographic metadata. That's arguably the single highest-impact operation we can do.

There's a catch, though. When we checked province agreement on shared titles, **56 out of 500 sampled pairs disagreed on province**. That means roughly 11% of the "matches" might actually be different songs that happen to share a title. (Folk song titles are often generic — "Mountain Song," "Work Song," "Love Song" — so this isn't surprising.) Any merge pipeline needs to cross-validate on province, not just title.

## Title Embeddings: The Shape of Chinese Music

We embedded all 30,000 titled items using character n-gram TF-IDF and projected them into 2D (Figure 4). The structure is revealing.

![Title embeddings](figures/10_title_embeddings.png)
*Figure 4: Title embeddings colored by dataset (left) and genre (right). Folk songs form a broad cloud; PMEmo's English titles cluster tightly in a separate region.*

The left panel shows MGD (blue) and Anthology (orange) heavily overlapping — confirming the title-matching analysis. PMEmo's English-language pop songs (orange dots near the origin) form a tight, completely separate cluster. They're literally in a different language, and the embedding picks that up immediately.

The clustering analysis found 15 natural groupings, each with a distinct thematic flavor:

- **Cluster 0**: Love songs (妹/哥/心/情 — "sister/brother/heart/feeling")
- **Cluster 2**: Work songs about tamping/pounding (夯/打/号子 — construction chants)
- **Cluster 3**: "Flying a Kite" songs (放风筝 — a common folk theme across provinces)
- **Cluster 5**: English pop titles (the PMEmo outlier)
- **Cluster 7**: Embroidery songs (绣荷包 — "embroidered pouch," a classic folk theme)
- **Cluster 8**: Peddler songs (卖 — "selling" things)
- **Cluster 13**: Work chants/号子 (labor songs with rhythmic shouting)

The fact that title text alone produces thematically coherent clusters suggests that Chinese folk song titles are *highly* informative about content. A title-based classifier could probably do a reasonable job at sub-genre classification without looking at any musical features.

## Instrument Coverage: Half the Bayin Is Missing

Chinese musicology traditionally classifies instruments into eight categories (八音/bayin): silk, bamboo, metal, stone, earth, skin, gourd, and wood. Aquarius covers only four of them (Figure 5, Panel B):

- **Silk** (strings): 5,724 items — erhu, pipa, guzheng, etc.
- **Bamboo** (flutes): 3,135 — dizi, dongxiao, hulusi
- **Gourd** (free-reed): 2,335 — sheng
- **Metal** (bells/gongs): 1,175 — suona (classified here for its metal bell)

Completely absent: **stone** (chimes), **earth** (clay ocarinas), **skin** (drums), and **wood** (clappers/woodblocks). This means no percussion of any kind — a major gap for a database that aims to represent Chinese music broadly. Drum patterns are central to Beijing Opera, festival music, and ensemble performance.

## A Few Surprises

**The Kaggle key distribution is suspiciously uniform.** The 2,374 items from the Traditional Chinese Folk Music dataset on Kaggle show an almost perfectly flat distribution across six keys (D: 15.8%, A: 16.3%, F: 17.3%, E: 17.2%, C: 16.8%, G: 16.7%). Real folk music doesn't behave this way — Chinese folk songs cluster heavily around G, D, and C due to pentatonic tuning conventions. This uniformity suggests the keys may have been randomly assigned or derived from a model rather than from ground-truth analysis.

**PMEmo doesn't belong.** 794 items are Western pop music (English-language titles like "Stay," "Head Over Boots," "America's Sweetheart"). They're from the PMEmo emotion recognition dataset, which happens to be listed under CSMTD but isn't Chinese music at all. These should be flagged or excluded from any analysis of Chinese musical traditions. The title embedding visualization separates them cleanly.

**276 unified IDs are duplicated** in the Anthology dataset. This is a loader bug: songs that appear in both the `lyrics-included/` and `melody-only/` subdirectories get assigned the same ID. Quick fix, but it inflates the item count by about 680 rows.

**173 songs appear across the singing datasets** (M4Singer, GTSinger, POP909). These aren't duplicates — they're the *same songs performed by different singers*. Songs like「不再见」and「匆匆那年」appear in all three datasets. This is actually valuable: it enables cross-singer comparison studies, voice conversion benchmarks, and arrangement analysis. They should be cross-linked rather than deduplicated.

## The Low-Hanging Fruit

Here's what can be done without collecting new data, ranked by effort-to-impact ratio:

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| 1 | Merge Anthology ↔ MGD by title | 6,400 songs get both MIDI and metadata | ~2 hours |
| 2 | Key detection on MIDI/MusicXML items | 10,720 items get key via Krumhansl-Schmuckler | ~4 hours |
| 3 | Pentatonic mode detection | 10,720 items get Chinese mode (train on 287 CNPM examples) | ~1 day |
| 4 | Fix duplicate IDs | Anthology loader bug, 276 duplicated IDs | ~30 min |
| 5 | POP909 year lookup | 909 songs get release year via MusicBrainz | ~2 hours |
| 6 | MIDI → audio synthesis | 9,383 folk songs get synthesized audio via FluidSynth | ~1 day |
| 7 | Audio → MIDI transcription | 13,894 audio clips get MIDI via Basic Pitch | ~2 days |
| 8 | Flag/exclude PMEmo | 794 non-Chinese items properly labeled | ~15 min |

The mode detection opportunity is especially significant. Right now, only 287 items (from CNPM) have Chinese pentatonic mode labels. But 10,720 items have MIDI or MusicXML data from which mode can be computationally estimated. CNPM's 287 ground-truth examples span all 5 modes × 12 tonics × 6 scale systems — enough to train and validate a mode classifier. This is the single most important contribution Aquarius can make: **the first large-scale Chinese pentatonic mode annotation.**

## What's Still Missing

Beyond the bayin gaps (no percussion), several major Chinese musical traditions have no representation at all:

- **Kunqu Opera** — the "mother of Chinese opera," UNESCO Intangible Cultural Heritage, zero items
- **Cantonese Opera** — one of the three major Chinese opera forms, zero items
- **Chinese orchestra/ensemble** — all datasets are solo instrument or voice recordings
- **Buddhist and Taoist ritual music** — an important scholarly field, zero items
- **Minority music beyond Xinjiang** — Tibetan, Mongolian, Dai, Miao, Yi, Bai music largely absent

The temporal dimension is almost entirely blank. Without knowing *when* music was composed or recorded, it's impossible to study historical trends, stylistic evolution, or the influence of political/cultural events on musical practice. This is the hardest gap to fill because most folk song collections simply don't record dates.

## Conclusion

Aquarius is wide but uneven. It captures a genuine breadth of Chinese musical traditions — from 31-province folk song collections to Beijing Opera phoneme annotations to Guzheng technique detection — but the depth varies wildly. The biggest quick win is merging the Anthology and MGD datasets, which would transform ~6,400 entries from partial records into richly annotated, multi-modal items. The biggest research win is pentatonic mode detection at scale. And the biggest remaining gap is the complete absence of percussion, ensemble music, and non-Beijing opera traditions.

The 12 figures generated across three analysis notebooks are in `notebooks/figures/`. The analysis code is in `notebooks/01_overview.py`, `02_deep_analysis.py`, and `03_gaps_and_opportunities.py`.
