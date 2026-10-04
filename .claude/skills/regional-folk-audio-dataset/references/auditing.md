# Auditing & correcting transcriptions without ground truth

## Contents
1. Why the benchmark is not enough
2. The critic (pitch-evidence auditor)
3. Critic agreement with ground truth (benchmark calibration)
4. First-principles in-domain checks
5. Human-audited gold set
6. Correction policy
7. Status of this section

---

## 1. Why the benchmark is not enough

| | Benchmark | Collected dataset |
|---|---|---|
| Recording | studio, dry, isolated; synthetic mixes | field/stage, reverb, real ensembles, varied quality |
| Singing | Mandarin pop, some en/es/tl | 原生态 folk, melisma, falsetto, polyphony |
| Language | zh/en/es… | + Tibetan, Uyghur, Kazakh, Mongolian, Miao, Zhuang, Bai, Lisu, 客家, 闽南 |
| GT | intended score notes, or sung-pitch averages | none |
| Rhythm | metered | often free |

Use the benchmark to **compare tools** under controlled conditions. Estimate **quality** in-domain, with checks that
each have a chance baseline, and ultimately with a small human-rated gold set.

## 2. The critic: `src/transcription/critic/`

**Evidence** (10 ms frames, on separated vocals, independent of the transcriber):
- `f0_rmvpe.py`: RMVPE, bundled with ROSVOT (`third_party/ROSVOT/checkpoints/rmvpe`). CPU, rosvot env; 60 s chunks.
- `f0_pesto.py`: PESTO (`mir-1k_g7`), sep env, MPS. Use `pesto.predict(x, sr, step_size=10)`, which returns
  (time, pitch, confidence, activations). Calling the model object directly returned outputs in a different order,
  and the first run produced garbage.
- **Confident frame:** both trackers voiced (PESTO conf > 0.5) and within 0.5 st of each other.
- `validate_f0.py` checks the trackers against GT notes on the benchmark:

| subset | RMVPE acc | PESTO acc | confident-frame acc | GT frames confident | tracker agreement | RMVPE false voicing |
|---|---|---|---|---|---|---|
| GTSinger | 0.69 | 0.73 | 0.73 | 0.79 | 0.86 | 0.12 |
| M4Singer | 0.66 | 0.72 | 0.72 | 0.74 | 0.83 | 0.08 |
| vocadito | 0.80 | 0.83 | 0.83 | 0.74 | 0.68 | 0.32 |

(acc = voiced frames within ±0.5 st of the GT note pitch. With PESTO conf > 0.5.)

Even confident frames match the note value only ~0.72–0.83 of the time: vibrato, slides and transitions leave the
note's nominal pitch. So **judge each note by the median of confident frames in its core (middle 60%)**, never
frame by frame.

**Per-note verdicts** (`critic.py`):
- **ok:** |dev| < 0.5 st
- **wrong_pitch / octave_error:** ≥5 confident core frames and |dev| ≥ 0.5 (≈12 for octave)
- **unvoiced:** RMVPE voiced fraction < 0.2
- **uncertain:** too little evidence
- **missed segments:** confident-voiced runs ≥150 ms with no note

**Corrections**, each switchable so its effect can be measured separately:
- repitch
- delete unvoiced notes
- fill missed segments, split at stable pitch steps ≥0.7 st lasting ≥60 ms

Options added after the first calibration:
- tuning-offset compensation (circular mean of fractional semitones)
- consensus: repitch only if a second transcriber (ROSVOT) has an overlapping note at the target pitch

## 3. Critic agreement with ground truth (`eval_critic.py`)

The first calibration covered 3,949 predicted notes (GAME + trim on separated benchmark mixes). GT labels:
- correct: a GT note covers ≥50% of the note, same pitch
- wrong: a GT note covers ≥50% of the note, different pitch
- spurious: no GT note covers ≥20% of the note

| | value |
|---|---|
| "ok" notes that are actually correct | 0.85 |
| wrong-pitch flag precision / recall | 0.53 / 0.29 (vocadito 0.47 / 0.30; M4 0.68 / 0.37) |
| repitch lands on GT pitch | 0.48 |
| unvoiced flag precision / recall | 0.79 / 0.40 (vocadito 0.96 / 0.44) |
| notes wrong per GT but "ok" per the critic | 328 (~8% of notes) |

Effect on note F1 (vocadito COnP):

| variant | vocadito COnP |
|---|---|
| base | 0.587 |
| + delete | 0.591 |
| + repitch | 0.585 |
| + fill | 0.587 |
| all three | 0.588 |

Interpretation, the key insight:
- A pitch-tracker critic measures **fidelity to the performance**.
- Score-style GT (M4Singer/GTSinger) encodes the **intended** note. When a singer is consistently sharp or flat,
  "fixing" toward the sung pitch moves away from the intended note.
- vocadito's GT is per-note sung-pitch averages, so it is non-integer and sits in between.
- So: use the critic to (a) certify notes, (b) delete notes in unvoiced regions (high precision), and (c) flag
  notes for review. Don't let it overwrite pitches unless a second, independent transcriber agrees *and* the
  tuning offset is compensated.

Tuning compensation (circular mean of fractional semitones) and ROSVOT consensus are now built into `critic.py`
(`Params.tuning`, `Params.consensus`). The benchmark was not re-scored with them: once the domain gap was measured
(§4A) the benchmark stopped being the judge, and the decision moved to in-domain checks and the human gold set.

## 4. First-principles in-domain checks: `src/transcription/audit/`

Shared utilities in `melody.py`:
- skeletonize the melody: drop notes <80 ms, keep the top voice at shared onsets, merge repeats
- transposition-invariant best shift: pitch-class histogram, then octave by median
- Needleman–Wunsch alignment; **semi-global** mode for a one-verse score inside a multi-verse performance

Every check reports a **chance baseline**. Absolute numbers mean little on their own.

**B. Score reference** (`score_reference.py`)
- References: 《中国民间歌曲集成》 Anthology scores (8,658 MIDI/MusicXML files, 10 province volumes) with the same
  title *and* a region-consistent volume. A same-titled song from another province is usually a different tune:
  对花 has 30 scores and 送情郎 has 18.
- Title matching found 109 recordings / 72 songs; the region-consistent subset is **62 recordings**.
- Compare: max agreement over the k same-title scores vs max over k random scores from the same volumes.
- Result:

| variant | matched | chance | gap | beats chance |
|---|---|---|---|---|
| GAME/primary | 0.58 | 0.45 | 0.13 | 71% of recordings |
| ROSVOT | 0.55 | 0.43 | 0.11 | 68% |

  GAME beats ROSVOT on 55% of recordings. That is in-domain confirmation of the benchmark's model choice.
- Caveat: chance is high (pentatonic material plus free alignment), so this check is weak at telling
  transcriptions apart. Use it for relative comparisons.

**D. Cross-performance consistency** (`cross_performance.py`)
- 121 pairs of recordings of the same song in the same region, vs 121 random different-song pairs from the same
  region. Global alignment over the first 120 skeleton notes.

| variant | same song | different song | gap |
|---|---|---|---|
| GAME/primary | 0.434 | 0.286 | 0.148 |
| ROSVOT | 0.400 | 0.283 | 0.116 |

  GAME again preserves more melodic identity.

**A. Domain-gap statistics** (`domain_gap.py`, same evidence for benchmark and dataset; medians + KS)

| property | benchmark | dataset | KS |
|---|---|---|---|
| RMVPE/PESTO agreement on voiced frames | 0.87 | **0.44** | **0.74** |
| pitch range (p95−p5, st) | 9.0 | 12.8 | 0.53 |
| voiced fraction | 0.80 | 0.74 | 0.29 |
| wobble around a 150 ms median (st) | 0.26 | 0.34 | 0.31 |
| tuning offset from A440 (st) | 0.19 | 0.13 | 0.16 |
| glide fraction | 0.33 | 0.34 | 0.08 |

- **The minority regions are furthest out:** tracker agreement is 0.10 for 西南多民族, 0.16 for 藏族 and 0.18 for
  新疆. Measure this before trusting any benchmark number for them.
- **Decompose the disagreement before reacting to it.** Here it was almost all "RMVPE voiced, PESTO
  under-confident"; when both are voiced they disagree on pitch in only 3–14% of frames.
- **Check the stems to tell soft singing from bleed.** At the tracked pitch the vocal stem sat +19 dB over the
  accompaniment in RMVPE-only frames, against +33 dB where the trackers agreed, so those were soft or breathy
  singing, not bleed. The exceptions were heterophonic regions (新疆, 北方草原: +6–8 dB), where instruments double
  the melody.
- **In-domain evidence rule:** RMVPE voiced AND (PESTO agrees OR vocal-stem dominance ≥ 12 dB,
  `critic/stem_dominance.py`). This raised usable evidence from 44% to 85% of voiced frames.
- Gotcha: a NaN-unaware running median (gaps counted as 0 Hz) turned "wobble" into 5 semitones. Use a rolling
  median with `min_periods`.

**C. Invariance tests** (`invariance.py`, 45 recordings = 3 per region, first 60 s)
- GAME rerun vs itself: note F1 **0.835** (0.68–0.96). ~16% of notes change between identical runs. On the benchmark
  this showed up only as ±0.005 in aggregate F1, which hid it.
- ±2 st pitch-shift (librosa phase vocoder): 0.69, partly from shift artifacts. A cleaner shifter (rubberband)
  would give a tighter bound.
- Remedy under test: majority-vote ensembles of GAME runs (`ensemble.py`). Criterion: two disjoint 3-run
  ensembles should agree far more than two single runs.
  - **Result:** 0.897 vs 0.841, with note counts almost unchanged.
  - **Independent check:** vocadito COnP 0.587 → 0.600 and COnPOff 0.366 → 0.380.
  - **Adopted:** a 3-run ensemble for every vocal recording (`src/transcription/ensemble_dataset.sh`).
  - **General lesson:** with a stochastic decoder, always measure run-to-run agreement per note, not just
    aggregate F1. A ±0.005 aggregate change can hide 16% per-note churn.

## 5. Human-audited gold set

Why: on the full dataset the critic flags 21% of notes as wrong pitch (twice the benchmark rate), but none of its
corrections (repitch, delete, fill, all) moves the in-domain checks beyond noise. Skeleton-melody checks are too
coarse to judge note-level edits, so only a human can settle whether a repitch is right.

Build it (`audit/gold_sample.py` + `audit/gold_page.html`, published as an artifact with the `db` + `user`
capabilities):
- **Sample:** 150 notes stratified by critic decision (repitch 60 / ok 30 / uncertain 20 / fill 25 / delete 15),
  round-robin over regions.
- **Clips:** separated vocals, note ±1 s, mp3 64 kbps (3.1 MB total).
- **Tones:** two per item, *blinded and randomized* A/B, synthesized in the page with WebAudio (a few harmonics) at
  MIDI pitch + the recording's tuning offset, so the rater compares scale steps in the singer's own tuning.
  - repitch: original vs corrected
  - everything else: the note vs a ±1 st foil, which measures the originals' absolute accuracy
- **Answers:** A / B / neither / no singing / can't tell. Never show the critic's category (it biases the rater).
  Offer "can't tell" explicitly.
- **Storage:** ratings go to the `ratings` collection (doc id `<item>__<rater>`), which Claude reads back with
  `ArtifactData`.
- **Outputs:** absolute note accuracy (ok/uncertain strata), repitch precision, and fill/delete correctness, per
  region. These decide which corrections to apply.

## 6. Correction policy (current recommendation)

- **Apply:** delete unvoiced notes. Precision is high and the F1 effect positive.
- **Flag, don't apply:** wrong_pitch without consensus; missed segments (fill was neutral on the benchmark, and
  in folk recordings uncovered voiced frames are often ornaments or other voices).
- **Record in the index:** per-recording critic stats (share of ok/uncertain/wrong/unvoiced notes), GAME–ROSVOT
  agreement, and coverage. These are QC columns for downstream users.
- Revisit after the gold set exists: calibrated thresholds may justify applying more corrections.

## 7. Status

- **Done:** critic (§2–3), all four in-domain checks (§4 A–D), the dataset-wide critic run, and the gold-set page.
- **Waiting on:** human ratings, and the GAME ensemble result.
- **Current policy:** no corrections applied to the released MIDI. `midi/critic_*` variants are kept for after
  the gold set.
