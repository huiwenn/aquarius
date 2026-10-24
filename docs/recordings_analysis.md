# Analysis of the transcribed recordings: scales, intonation, rhythm, melody

Exploratory analysis, 2026-10-23. Code: `src/analysis/recordings/` (see its `README.md` for the run order). Results: `data/analysis/recordings/` (not tracked). Companion: `docs/musical_elements_analysis.md` analyses the Essen scores and the metadata with the same question.

All results here are **exploratory** (see the evidence rule in `CLAUDE.md`). They describe patterns in the data. They do not prove causes. They say nothing about transcription friction, notation or cultural interaction.

## 1. Question

How do the 15 colour regions differ in scale, intonation, rhythm and melody? How far do the regions follow geography? How well does the music predict the region?

This follows item 1 of "Next" in the worklog entry of 2026-10-17: run the same kind of features on the corpus transcriptions.

## 2. Data

- **Recordings:** the `core` recordings of `metadata/recordings.csv` that have a transcription. This run had F0 and primary MIDI for Rounds 1 and 2 only. The 358 Round 3 recordings (Musical Map of China) had no transcription in the shared package, so they are not included. Each analysis uses 1,149–1,173 recordings; the geography analysis uses the 694 with a place at county or prefecture level.
- **Measures:** scales and intonation come from the RMVPE F0 of the separated voice. Rhythm and melody come from the note onsets and pitches of the primary MIDI. Every measure is computed per recording, then averaged per region.
- **Uncertainty:** intervals resample whole groups (`group_id`: channel or singer), 1,000 times.
- **Folds:** `add_folds` from `src/colour_regions/build_release.py`. A training set also drops recordings whose `song_key` occurs in the test fold.

## 3. Results

| Analysis | Result | How far to trust it |
|---|---|---|
| Scales | Northern Steppe (86% of singing inside one pentatonic scale), Tibetan (80%) and Northwest Plateau (79%) are the most pentatonic. Yue (68%), Min–Tai and Xinjiang (71% each) are the least. Non-pentatonic notes are 6–17% of singing | The ten middle regions overlap. The note a song ends on (mode) is only suggestive: one pentatonic scale fits clearly for 47% of recordings |
| Intonation | 14–22% of singing falls between the piano keys (random pitch: 30%). Northern Steppe and Northwest Plateau are closest, Yue and Min–Tai furthest. Singers drift 10–20 cents over a song | Differences between regions are small. Pitch tracking adds noise |
| Rhythm | Northern Steppe is the slowest and most spacious: 1.9 notes/s, 10% held notes, 50% of the time in pauses. Southwest Multi-ethnic and Tibetan follow (2.0 notes/s, 46–48% pauses). The Northeast Plain is fastest (2.9 notes/s, 26% pauses) | Beats per minute and metre are not measured (section 4) |
| Melody | Xinjiang has the narrowest range (13 semitones), the smallest typical interval (2.0) and the fewest leaps (9%). Yue (20%) and Southwest Multi-ethnic (19%) have the most leaps. Descending is the commonest phrase shape in every region (38–55%) | Transcription errors can inflate ranges. Compare regions with each other |
| Region profiles | Two groups plus Xinjiang: five highland, steppe and southwest regions, and nine eastern and southern Han regions | Stable in 1,000 resamples: mean pair stability 0.71 and 0.83. The Southwest Plateau is the borderline member |
| Geography | Nearer regions sound more alike (Spearman r = 0.73, p < 0.001; leave-one-region-out 0.66–0.78). Melody follows geography most (r = 0.61; typical interval 0.63; leaps 0.52). Single recordings follow it weakly: mean musical distance 4.2 under 50 km, 4.9 over 3,000 km | The regions are drawn geographically, so part of this is built in. Among the 11 Han regions alone r = 0.51 (interval 0.08 to 0.62) |
| Region classifier | Macro-F1 0.238 (interval 0.20–0.26; chance 0.067), accuracy 25%, right region in the top three for 49%. A model that sees only longitude and latitude reaches 0.84 | Strict protocol. Best model is logistic regression on 54 measures; gradient boosting reaches 0.227 and the 12 main measures 0.19–0.20 |
| Genre | Only 小调 (191), 山歌 (171) and 号子 (42) occur across many regions. With the region fixed, 号子 has more leaps (+0.73 standard deviations), more non-pentatonic notes (+0.70) and less pentatonic fit (−0.84) than 小调; 山歌 has more held notes (+0.57) | The other genres are one region each, so genre and region cannot be separated. The three genres have 42–191 recordings |
| Folk vs trained style | Trained (民族唱法) singing is closer to the grid (−0.50 standard deviations, interval −0.72 to −0.27; same channel −0.40) and varies more in speed (+0.38; same channel +0.46; same song +0.52). Even spacing does not change (+0.06) | Only two channels hold both styles, and 11–17 songs exist in both. Recording quality may play a part |

### 3.1 Region profiles and groups

- 12 measures (two scale, one intonation, four rhythm, five melody), z-scored across regions, equal weights, Ward clustering.
- **Highland, steppe and southwest:** Northern Steppe, Tibetan, Southwest Multi-ethnic, Northwest Plateau, Southwest Plateau. Strongly pentatonic, many held notes, long pauses.
- **Eastern and southern Han:** Yue, Min–Tai, Hakka, Xiang, Gan, Jiang–Han, Northeast Plain, Jiangsu–Zhejiang Plain and Jiang–Huai. Faster notes, shorter pauses.
- **Xinjiang:** alone.

### 3.2 Region classifier

- Models: multinomial logistic regression and histogram gradient boosting, both on 12 or 54 measures, balanced class weights. Settings are fixed in advance, not tuned on test data.
- **Regions recognised:** Xinjiang (F1 0.57), Northern Steppe (0.36), Tibetan (0.36), Southwest Multi-ethnic (0.29). Near chance: Gan (0.05), Jiang–Han (0.08), Xiang (0.10).
- **Measure families** (logistic regression on 54 measures): melody alone 0.17, scales 0.15, rhythm 0.12, intonation 0.07. Leaving melody out drops the score to 0.17, scales to 0.21 and rhythm to 0.23. Leaving intonation out does not lower it (0.25).
- **Errors stay inside the groups:** 74% of eastern and southern Han recordings are guessed as one of those nine regions (57% of all guesses land there), and 59% of highland recordings stay in their group (35% of guesses). Scores per fold range from 0.17 to 0.29.
- **Genre:** the music separates 号子 from 小调 and 山歌 better than the region alone does (F1 0.48 against 0.00). It does not separate 小调 from 山歌 better than the region does (0.66 and 0.64 against 0.74 and 0.73).

### 3.3 Folk against trained singing

- Three predictions were fixed before the test: trained singing is closer to the grid, varies less in speed and has more evenly spaced notes.
- **Supported:** closer to the grid (pooled, same channel, and 6 of the 7 regions with at least 10 recordings of each style).
- **Contradicted:** trained singing varies *more* in speed, in every view and in all 7 of those regions.
- **Not supported:** more even spacing.
- Field recordings go the other way (further from the grid +0.40, less pentatonic −0.52).

## 4. Measures that were tried and dropped

- **Beat and tempo.** A pulse detector found free rhythm in 97% of songs. On synthetic songs with a known beat it missed clearly metered music, because transcribed note timings are off by tens of milliseconds and singers drift in tempo. The measure "evenly spaced notes" cannot tell metered from free singing either (synthetic songs with mixed note values score 0.19–0.31, random spacing 0.21). Speed is therefore reported as notes per second.
- **Glide share** from the F0 tracks: 60–79% in every region. This is tracker noise, not ornamentation.
- **Large deviations on rare scale degrees.** Degrees below 5% of singing mostly hold passing notes and lean toward the neighbouring scale note. Only degrees above 5% are used.
- **Recordings above 8 notes per second** (8 of about 1,170) are dropped as transcription errors.

## 5. Limits

- Every measure comes from automatic transcription.
- The 15 regions are drawn geographically, so the link with geography is partly built in.
- Several comparisons rest on 11–45 recordings: genres, the same-channel and same-song views, the regions with trained singing.
- One channel (the Musical Map of China series) holds about a quarter of Rounds 1 and 2. Its link in `group_id` is why the resampling uses groups.
- Composed pieces are not in `core`, so folk against composed could not be tested. Performance type is a style proxy, not a date.

## 6. Next

1. Add the 358 Round 3 recordings once their transcriptions are in the shared package. Rerun the ten scripts (about two minutes).
2. Compare these measures with the Essen features of `docs/musical_elements_analysis.md`: do the regional differences in range, intervals and tonality agree between scores and performances?
3. Add timbre, dynamics and texture from the separated stems (not measured so far).
