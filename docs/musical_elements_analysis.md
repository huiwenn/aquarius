# Musical elements by colour region and over time

Exploratory analysis, 2026-10-17. Script: `src/analysis/musical_elements.py`. Tables: `notebooks/elements_results/`. Figures: `notebooks/figures/elements_*.png`.

All results here are **exploratory** (see the evidence rule in `CLAUDE.md`). They describe patterns in the data. They do not prove causes.

## 1. Question

Which musical elements differ between colour regions, and which change over time?

The analysis uses the eight elements of the project checklist: melody, rhythm, tonality, form, timbre, dynamics, texture and harmony.

## 2. Data

| Source | Items | Elements it can measure |
|---|---|---|
| Essen Folksong Collection, China subset (Humdrum **kern) | 2,189 songs mapped to 13 regions with at least 20 songs | Melody, rhythm, tonality (pentatonic mode), form |
| `metadata/recordings.csv`, core subset | 1,544 recordings, 15 regions | Performance practice: performance type, accompaniment, group singing, genre, length |
| `composition_period` and `composition_year` in `recordings.csv` | 101 recordings with a dated period; 87 with a year | Change over time |

- Essen songs get a region with the same rules as `src/regionclf/corpus.py` (province from `!!!ARE`, or ethnic group for minorities). Tibetan has only 6 Essen songs, so the region tests leave it out.
- The Essen data is not in the repo. Get it from `github.com/ccarh/essen-folksong-collection` (`asia/china`) into `data/raw/essen/asia/china/`. Its licence restricts redistribution, so the per-song feature table goes to `data/analysis/` (not tracked). The repo keeps only region-level tables.
- **Not measured:** timbre, dynamics and texture need audio. Harmony does not apply, because these songs are monophonic.

## 3. Method

- **Features per Essen song:**
  - Melody: range in semitones (ambitus), mean absolute interval, step share (≤ 2 semitones), leap share (≥ 5), descending-interval share, and how far the final note lies below the song's mean pitch.
  - Tonality: the pentatonic collection that covers the most sounding time, the mode given by the role of the final note (gong, shang, jue, zhi, yu), and the share of time on notes outside the collection.
  - Rhythm: number of distinct note lengths, duration entropy, dotted-note share, short-note share (≤ a sixteenth), meter type (duple, triple, free) and meter changes.
  - Form: number of phrases (from the editors' `{ }` marks), notes per phrase, phrase repetition and the share of phrases that end on the final.
- **Tests:** Kruskal–Wallis for numbers and chi-square for categories, across regions with at least 20 items. Benjamini–Hochberg FDR inside each family. Effect sizes: epsilon squared (ε²) and Cramér's V. Spearman ρ against province latitude.
- **Effect size matters more than p.** With 2,189 songs, a small difference can still be significant. Read ε² ≈ 0.01 as small, 0.06 as medium and 0.14 as large; V ≈ 0.1 small, 0.3 medium.
- **Confound check.** The Essen `shanxi` subset is one collection of 802 songs from one province. It is most of the Northwest Plateau. Every Essen test is repeated inside the mixed `han` subset only (`p_han_subset_only`, `effect_han_subset_only`).

## 4. Results: regions

### 4.1 Robust (large effect, and holds inside the `han` subset)

1. **Melodic range is wider in the north.** Median range is 17 semitones in the Northeast Plain, Northwest Plateau and Northern Steppe. It is 12 semitones in Min–Tai and Yue. ε² = 0.17 overall and 0.17 inside the `han` subset. Range rises with latitude (ρ = 0.38).
2. **Northern songs end low.** The final note lies a median 7.1 semitones below the mean pitch in the Northwest Plateau and 6.4 in the Northeast Plain, but 3.0 in Min–Tai. Northern melodies also have more descending steps. ε² = 0.15 overall, 0.11 in `han`; ρ with latitude = 0.36.
3. **The mode of the final note changes by region.** Cramér's V = 0.21 overall and 0.21 in `han`.
   - Zhi (徵) finals are the most common in the Han central and northern regions: Jiang–Huai and Jiang–Han 58%, Gan 56%, Northwest Plateau 54%.
   - Yu (羽) finals lead in the Southwest Plateau (52%), Northern Steppe (48%) and Southwest Multi-ethnic (46%). Yu is also common in Yue (34%) and Min–Tai (31%).
   - Shang (商) finals are most common in the Northwest Plateau (20%) among Han regions.
4. **Notes outside the pentatonic scale are a northern and Xinjiang feature.** Southern regions have a median of 0% of time on such notes. The north has a small share (2%). Xinjiang has 12%, but only 22 songs. ε² = 0.17 overall, 0.14 in `han`; ρ with latitude = 0.34.
5. **Triple meter is a southern and minority feature; free meter is a steppe feature.** Cramér's V = 0.27 overall, 0.16 in `han`.
   - Triple meter: Southwest Multi-ethnic 42%, Xinjiang 36%, Southwest Plateau 26%, Yue 26%. Northeast Plain 5%, Northwest Plateau 7%.
   - Free meter (no time signature): Northern Steppe 19%, which matches the long song (长调). Other regions have 0–5%.

### 4.2 Weaker or not robust

- **Leaps and interval size.** Northern Steppe melodies leap most (median leap share 0.23). The overall effect is medium (ε² = 0.10), but it drops to small (0.04) inside `han`.
- **Phrase count.** The overall effect is large (ε² = 0.26), but most of it comes from the `shanxi` collection (0.09 inside `han`). Phrase marks come from different editors, so treat this as a property of the editions.
- **Rhythmic variety, dotted notes and phrase repetition.** These are small overall and not significant, or near zero, inside `han`. Make no claim.

## 5. Results: performance practice (recordings)

All six tests are significant after FDR.

- **Singing style.** The conservatory "national" style (民族唱法) is most common in Gan (39%), Southwest Plateau (33%) and Northeast Plain (30%). It is almost absent in the Northwest Plateau (4%), Tibetan (2%) and Southwest Multi-ethnic (0%). Cramér's V = 0.28.
- **Group singing.** Southwest Multi-ethnic has the most recordings with several singers (24%), which matches its multipart songs. V = 0.25.
- **Genre.** Mountain songs lead in Hakka (71%) and the Northwest Plateau (66%). Ditties (小调) lead in the Northeast Plain (63%). Long songs make up 34% of the Northern Steppe. V = 0.37.
- **Accompaniment.** V = 0.56, the largest effect. But only 536 recordings have an accompaniment flag, and nearly all come from the Musical Map of China series. Read it as a property of that series, not of the regions.
- **Length.** It differs by region, but the effect is small (ε² = 0.03).

## 6. Results: over time

The data on time is thin. Most songs are traditional and undated. Upload year is when a video was posted, not when the song was made or sung.

- **Songs from 1949–1965 differ from older songs.** Of 34 dated songs from 1949–1965, 31 are folk songs adapted in that period and 24 are sung in the conservatory style. Songs from the Qing and the Republic are mostly traditional songs sung in the traditional style. Performance type by period: V = 0.31, q = 0.007. Genre by period: V = 0.36, q = 0.002. Only 101 dated songs, so this is a lead, not a result.
- **No trend with upload year.** The share of traditional-style singing (ρ = 0.03) and recording length (ρ = −0.04) do not change with upload year.
- **No trend of length with composition year** (ρ = 0.12, n = 87, not significant).

## 7. Limits

- Essen is a set of printed editions from the 1980s–1990s, transcribed by many editors. Some regional differences can come from editors, not singers. The `han`-subset check reduces this risk but does not remove it.
- The mode rule assumes that the final note is the tonic. Songs that end on another degree are mislabelled.
- Essen has few songs for Xinjiang (22), Southwest Multi-ethnic (24) and Tibetan (6).
- The recordings were collected on purpose to cover each region evenly. Their genre and style shares describe this corpus, not all folk song in a region.
- Timbre, dynamics and texture are missing (see 8).

## 8. Next steps

1. **Run the same features on the corpus transcriptions** (GAME primary MIDI in `data/regions_transcription/`). This gives all 15 regions from audio, and tests if the Essen patterns also appear in performed songs.
2. **Timbre, dynamics and texture from audio.** Compute spectral centroid, MFCC statistics, loudness range and vocal-to-accompaniment energy on the separated stems that the pipeline already writes.
3. **Time from the Anthology.** The Anthology volumes record when each song was collected. Linking them (`metadata/anthology_overlap.csv`) can give dated melodies.
