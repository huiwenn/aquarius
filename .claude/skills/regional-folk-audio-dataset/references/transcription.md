# Transcription: choosing, validating and running audio → MIDI/MusicXML

## Contents
1. Framing the problem
2. Benchmark design (and how it misled at first)
3. Candidate models and results
4. Accompaniment and separation
5. Our own improvement: offset trim
6. The production pipeline
7. Instrumental fallback and primary selection
8. MusicXML conversion
9. Throughput
10. Adapting to other targets

---

## 1. Framing

Folk recordings are mostly **solo voice + accompaniment** (ensemble, orchestra, 马头琴/冬不拉/扎木聂) with heavy
ornament (滑音, 颤音, 甩腔), free rhythm (散板, 长调, 信天游 openings), non-tempered intonation and minority
languages. The target is the **vocal melody**. Accompaniment transcription is secondary, and instrumental
recordings are a fallback case.

## 2. Benchmark design

`src/transcription/build_benchmark.py` → `data/transcription/benchmark/` (160 clips):
- **M4Singer:** 60 random phrases (seed 0), wav + GT MIDI (Mandarin pop, studio)
- **GTSinger-Chinese:** 60 random phrases, wav + JSON notes (technique groups: glissando, vibrato …)
- **vocadito** (Bittner et al. 2021, CC BY 4.0, Zenodo 5578807): all 40 clips, 7 languages, two annotators.
  GT = A1; A2 is scored as a "model" (`human_A2`), which gives the **human ceiling**.

`build_mix_benchmark.py` → `benchmark_mix/` mixes each vocal with a random ChMusic excerpt at +3 dB
vocal-to-accompaniment. Unaligned accompaniment, so instrument notes count as false positives. It is seed-stable
and skips existing files while still consuming RNG draws, so adding clips doesn't change the old mixes.

`evaluate.py` (mir_eval) reports:
- COnPOff (onset ±50 ms, pitch ±50 c, offset)
- COnP (onset and pitch)
- COn (onset only)
- `_100` variants (onset ±100 ms)
- **bias_ms:** the median signed onset offset

Always report bias. It is what exposed the problem below.

**How it misled.** On M4Singer/GTSinger every non-ZJU model had a **+60–75 ms onset bias**, while ROSVOT (same
ZJU lab) had ~0. ZJU labels start a note at the syllable's consonant; OpenVPI and others start it at the vowel.
Combined with training leakage, this made ROSVOT look 3× better. Adding the independently annotated vocadito
subset reversed the ranking. Rule: include at least one control subset annotated by an unrelated group, and check
each model's training data against every benchmark subset.

## 3. Candidates and results

COnP on each subset, plus vocadito COnPOff and bias:

| Model (config) | M4Singer | GTSinger | **vocadito** | vocadito COnPOff | vocadito bias | Training overlap |
|---|---|---|---|---|---|---|
| human A2 (ceiling) | – | – | **0.723** | 0.633 | −0.1 | – |
| GAME-1.0-medium, zh, seg 0.1 | 0.242 | 0.251 | **0.588** | 0.297 | −2.6 | none known (private data) |
| SOME 0119 | 0.220 | 0.224 | 0.572 | 0.278 | +7.1 | none known |
| Basic Pitch | 0.237 | 0.206 | 0.486 | 0.308 | +12.8 | none |
| YourMT3+ MoE-PS | 0.215 | 0.242 | 0.469 | 0.266 | −5.1 | none |
| ROSVOT | **0.750** | **0.699** | 0.261 | 0.184 | −45.5 | trained on ~all of M4Singer; same lab as GTSinger |
| VocalParse (Qwen3-ASR-1.7B) | 0.164 | 0.244 | 0.020 | 0.006 | – | **all 120 M4/GT clips in its training set** |

Model notes:
- **GAME** (openvpi, MIT, commit f423934, GAME-1.0 release):
  - trained on ~32 h private zh/yue/ja/en singing with noise and accompaniment augmentation (incl. Asian ethnic
    instruments)
  - output is stochastic (D3PM): ±0.005 between runs
  - medium beats large; seg-threshold 0.1 beats 0.2 and 0.35; `lang zh` made no measurable difference
  - ~5 s per audio-minute on MPS; *slower* on long songs under memory pressure
- **SOME** (CC BY-NC-SA): trained on clean vocals, so it needs separated input. Checkpoint 0119 beats 0918.
- **ROSVOT** (ACL'24, commit 3c8332b): the released checkpoint is M4Singer-only, holding out just the first 200 items.
  - Word boundaries come from RWBD, which is also Mandarin-trained, so it fails on other languages.
  - Its output on MPS is wrong: CPU only. ~6.7 s per audio-minute. Batch size >1 is slower and changes notes.
  - It caps inputs at ~160 s; its runner chunks at 60 s.
- **VocalParse:** predicts note *values* plus one global BPM, not timestamps, so onsets drift and free rhythm is
  unrepresentable. Pitch is compressed toward the middle of the range. 80–120 s per audio-minute. Its lyrics output
  may still be useful as metadata.
- **YourMT3+:** the MoE-PS checkpoint beats the Space default (noPS). The vocal track is named "Singing Voice".
  CPU is faster than MPS (autoregressive decoding).

## 4. Accompaniment and separation

| GAME input | vocadito COnP |
|---|---|
| clean vocal | 0.588 |
| mix | 0.532 |
| mix → BS-RoFormer | 0.594 |
| mix → **htdemucs** | 0.587 |

ROSVOT loses more on mixes (−18% on its in-domain data).

Speed on a real 152 s folk song (M1 Pro, MPS):
- BS-RoFormer: 370 s at default overlap, 196 s at overlap 2 (autocast made no difference)
- **htdemucs: 25 s**

So production uses htdemucs. It returns 4 stems; the accompaniment is saved as the sum of drums + bass + other.

Pitfall: audio-separator renames `__vocals` to `_vocals` in output names. An exact-name match silently deleted
every vocal file on the first try. Match on suffix.

## 5. Our own improvement: offset trim (`postprocess.py`)

Error analysis of matched notes: GAME's notes end **late**.
- median offset error: +39 ms (vocadito), +58 ms (M4Singer), +67 ms (GTSinger)
- 45–57% of notes more than 50 ms too long, only 8–13% too short

A constant trim was chosen by **2-fold singer-disjoint CV on vocadito**:
- the two folds picked 40 and 60 ms; held-out COnPOff went 0.299 → 0.357
- M4/GT agree: 0.115 → 0.150
- **50 ms** is used; onsets and pitch are untouched

Pattern worth reusing: look at the signed error distribution before reaching for a new model, and choose
post-processing constants with held-out folds, never on the test clips.

## 6. The production pipeline

`src/transcription/transcribe_regions.py` (`--models`, `--steps sep,midi,xml`, `--regions`, `--only-ready`):
1. stage audio as symlinks: `data/regions_transcription/audio/<class>/`
2. htdemucs → `vocals/<class>/<id>.wav`, `accomp/<class>/<id>.wav`
3. GAME → `midi/game/…`; trim → `midi/game_pp/…` (primary)
4. MusicXML → `musicxml/game_pp/…`
5. ROSVOT → `midi/rosvot/…` (secondary, QC)

`run_all.sh` runs the GPU side (steps 2–4) and the CPU side (ROSVOT, `--only-ready`) in parallel.
`follow_downloads.sh` repeats: rebuild the manifest → `run_all.sh` → sleep 15 min, until the downloader exits,
then a final pass + index. Every runner skips existing outputs (GAME needed a patch for this), so kill/rerun is safe.

## 7. Instrumental fallback and primary selection

Some curated "songs" are instrumental or instrumental-dominant: separated vocals at −50 to −87 dB, or 3–8%
vocal activity (堆谐 song-and-dance with brief calls). GAME then writes **no MIDI or an empty MIDI**. Handle both.

`select_primary.py` rules, with coverage = total note duration / recording duration:
1. **instrumental:** GAME empty, or GAME cov < 0.05 and ROSVOT cov < 0.10 → YourMT3+ on the full mix
2. **vocal_rosvot:** GAME cov < 0.15 and ROSVOT cov > max(0.20, 2 × GAME cov) → ROSVOT
3. **vocal_game:** everything else

Worked example: 586 / 12 / 2. Dataset medians: GAME cov 0.58, ROSVOT cov 0.78. Lowering GAME's est-threshold to
0.1 or 0.05 barely helped sparse recordings (+0–1% coverage, except one).

## 8. MusicXML (`midi_to_musicxml.py`)

1. Beat grid from librosa beat tracking on the **full mix**; the accompaniment carries the pulse better than the
   voice.
2. Note times mapped to beats by interpolation along the grid, which follows tempo drift.
3. Quantized to 16ths + eighth-triplets.
4. Forced monophonic: a note is cut at the next onset; notes shorter than a 16th are dropped.
5. Rests fill the gaps; written with music21.

Caveat: the `free_rhythm_suspect` flag (beat-interval CV > 0.25) fired on **0/600**, because librosa imposes a
steady pulse. For free-rhythm genres the metre is nominal. Treat the MIDI as authoritative, and consider a
genre-based flag instead.

## 9. Throughput (M1 Pro, 32 GB)

| Step | Device | Speed |
|---|---|---|
| htdemucs | MPS | ~6–8× real time |
| GAME medium | MPS | ~5 s per audio-minute (short clips); slower on long files |
| ROSVOT | CPU | ~6.7 s per audio-minute |
| YourMT3+ | CPU | ~35–45 s per audio-minute |
| Basic Pitch | CoreML | ~2 s per audio-minute |

The 600 recordings (32.6 h) finished alongside the ~14 h download run.

## 10. Adapting to other targets

- **Other vocal traditions:** re-run the benchmark with a control set in or near the target language. GAME supports
  en/ja/yue/zh.
- **Instrumental traditions:** YourMT3+ or Basic Pitch on the full mix, a monophonic skeleton for melody, and an
  instrument-specific benchmark (e.g. CCOM-HuQin for erhu).
- **Polyphonic singing** (侗族大歌): single-line vocal models will pick one voice. Flag these for special handling.
