# 色彩区 Audio Collection & Transcription — Research Log

Goal: download ≥30 traditional/folk songs per region for all 15 regions (11 Han 色彩区 + 4 minority regions)
from `data/regions/*.json`, then transcribe every recording to MIDI (and MusicXML) as accurately as possible.
All code lives in `src/secaiqu/` (collection) and `src/transcription/` (transcription). This file records
what was tried, what worked, and what didn't, in the order it happened.

---

## 1. Audio collection

### 1.1 First pass (2026-09-28): `src/secaiqu/download_audio.py`

- Input: 453 links (≈30 per region) in `data/regions/<region>.json → youtube_links`.
- Tool: `yt-dlp 2026.08.19`, `bestaudio/best`, no transcoding (native opus/webm or m4a), `.info.json` kept
  for provenance (uploader, upload date, license, duration).
- Output: `data/regions_audio/<region>/<video_id>.<ext>`, manifest `data/regions_audio/manifest.csv`.

Result: stopped early. There were three problems:

| Problem | Count | Notes |
|---|---|---|
| Dead links ("Video unavailable", "not available", private, members-only) | ~86 | Many of the collected IDs no longer resolve. Some may never have existed, so collected links must be checked, not trusted. |
| Bot wall ("Sign in to confirm you're not a bot") | 190 | Started after ~150 successful downloads with 6 parallel workers. The IP is now flagged for every player client (web, android_vr, tv, web_safari, mweb, ios). Search (`ytsearch`, flat) still works. |
| Non-video links (8 playlist/channel URLs) | 8 | `noplaylist` doesn't stop these, so whole playlists were pulled into 藏族/闽台/新疆. |

Lessons:
1. Check every link with a metadata-only request before counting it toward a region's 30.
2. Allow single-video URLs only.
3. Throttle hard: 1 worker, randomized sleeps between requests.
4. Find replacement candidates with `yt-dlp "ytsearchN:<query>"`, which returns real, resolvable IDs. Don't let an LLM recall IDs.

### 1.2 Re-curation (2026-09-28): `data/regions_curated/<region>.json`

Three agents (5 regions each) rebuilt every region's list using **search only**, via
`src/secaiqu/search_candidates.py`. Every query and its hits are in `data/regions_curated/search_log.jsonl`.
Builder scripts are in `src/secaiqu/curation/`. The builder for 东北部平原/西北部高原/江淮/江浙平原/闽台 was
overwritten in a shared scratchpad, so for those regions the per-candidate `source_query` and `note` fields
are the provenance.

Each region has a ranked list of 40 single-video candidates, so that ≥30 survive download failures:
- 60–720 s long, ≤3 recordings of any one song
- field or tradition-bearer (原生态) recordings ranked above 民族唱法 stage performances
- pop, remixes, 广场舞, karaoke, tutorials and compilations excluded
- newly composed "folk-style" songs excluded (天路, 青藏高原, 太湖美, 乌苏里船歌 …), except a few canonical
  representative songs, which are flagged in `genre`/`note` (浏阳河, 十送红军, 望春风, 雨夜花, 洪湖水浪打浪)

| Region | Distinct songs | Region | Distinct songs | Region | Distinct songs |
|---|---|---|---|---|---|
| 东北部平原 | 25 | 粤 | 34 | 西南高原 | 26 |
| 西北部高原 | 38 | 客家特区 | 38 | 西南多民族 | 40 |
| 江淮 | 32 | 江汉 | 28 | 藏族 | 40 |
| 江浙平原 | 31 | 湘 | 35 | 新疆 | 37 |
| 闽台 | 33 | 赣 | 31 | 北方草原 | 34 |

What the curation turned up:
- **Most original links were fabricated.** None of the 60 original 湘/赣 IDs, and none of the undownloaded
  闽台 IDs, appear in any search result.
- **The playlist/channel pulls were mostly unusable.** 藏族 had 92 files: dance videos, exile pop, full albums.
  Only 1 was kept.
- **Best sources:** 中国音乐地图 / Rhymoi (short tradition-bearer recordings across nearly every region and
  ethnic group), dbadagna field recordings, CCTV 民歌大会 clips of tradition-bearers.
- **Thinnest regions:** 江淮, 粤 (results flooded by 广东音乐 instrumentals, 粤语 pop and 粤剧), 赣 (heavy
  reliance on one singer's 赣南民歌 album) and 西南高原 (few Han field recordings online).

### 1.3 Second download pass: `src/secaiqu/download_curated.py`

- Firefox cookies (`cookiesfrombrowser`), 1 request at a time, 10–25 s randomized sleeps, regions round-robin.
- First run: 85 downloads, then the bot wall came back even with cookies.
- Added:
  - JS runtime for yt-dlp challenge solving (`yt-dlp[default]` + Node 26 in the arm64 conda env `node`; the
    system Node 15 is broken, missing ICU)
  - bgutil PO-token HTTP provider (`third_party/bgutil-ytdlp-pot-provider`, commit 2d758ea)
  - automatic 40-minute cooldown-and-resume when the wall appears
- Neither the PO-token provider nor the JS runtime lifted the wall right away, and it hit without cookies too, so
  it's a timed IP-level rate limit. Two 40-minute cooldowns weren't enough.
- The run was restarted at a slower pace: **45–90 s between downloads, 1-hour cooldowns**. The wall cleared
  ~1 h later, and at ~45 downloads per hour it hasn't come back since.
- Remaining failures are sporadic `HTTP Error 403: Forbidden` (~5%), retried at the end with a different player
  client (`--player-client`).

**Environment note:** the default `conda` (`/usr/local/Caskroom/miniforge`) is **x86_64 under Rosetta**, so
PyTorch there has no MPS. All model envs live in the native arm64 conda at `~/miniforge3`.

---

## 2. Transcription model survey

Context: most recordings are **solo voice with accompaniment** (folk ensemble, orchestra, or a single instrument
such as 马头琴, 冬不拉 or 扎木聂), often with heavy ornamentation (滑音, 颤音, 甩腔), free rhythm (散板, 长调, 信天游)
and non-tempered intonation. The melody that matters most is the **vocal line**. Accompaniment transcription is secondary.

Candidates (from web search, 2026-09):

| Model | Type | Why considered |
|---|---|---|
| **GAME** (openvpi, 2026) | singing → MIDI, generative | Successor to SOME. Claims robustness to noisy, reverberant or accompanied voice. Built by a Chinese SVS community with a Mandarin focus. |
| **SOME** (openvpi) | singing → MIDI | Widely used for Mandarin SVS data labelling. Handles vibrato and slides. |
| **ROSVOT** (ACL 2024) | singing → MIDI | Built for robustness to noisy input. Trained partly on M4Singer, so it has a **benchmark leakage risk** (see §3). |
| **VocalParse** (arXiv 2605.04613, 2026) | LALM singing transcription (lyrics + notes) | Claims SOTA on several singing datasets. Code and checkpoint released. |
| **YourMT3+** (2024) | multi-instrument, mixture → multi-track MIDI | Transcribes vocals directly from mixtures and also covers the accompaniment. |
| **Basic Pitch** (Spotify) | instrument-agnostic polyphonic | Lightweight baseline. |
| Vocal separation front-end (BS-RoFormer / htdemucs) | source separation | Isolating vocals before a singing-specific model is likely to help. |

Sources: [GAME](https://github.com/openvpi/GAME), [SOME](https://github.com/openvpi/SOME),
[ROSVOT](https://github.com/RickyL-2000/ROSVOT), [VocalParse](https://arxiv.org/abs/2605.04613),
[YourMT3+](https://arxiv.org/abs/2407.04822) / [code](https://github.com/mimbres/YourMT3),
[STARS](https://arxiv.org/abs/2507.06670).

---

## 3. Benchmark

We can't hand-annotate folk recordings, so models are compared on Chinese singing with note-level ground truth
that we already have locally:

- `src/transcription/build_benchmark.py` → `data/transcription/benchmark/` holds 160 clips:
  - 60 M4Singer phrases (wav + GT MIDI), sampled with seed 0
  - 60 GTSinger-Chinese phrases (wav + JSON notes, technique groups such as glissando and vibrato included),
    sampled with seed 0
  - all 40 vocadito clips, added in §3.1
- `src/transcription/evaluate.py` gives mir_eval note F1: **COnPOff** (onset ±50 ms, pitch ±50 c, offset),
  **COnP** (onset and pitch), **COn** (onset only).

Caveats: studio pop singing isn't field folk recording, and some models were trained on M4Singer/GTSinger/Opencpop,
so scores on those subsets are optimistic. Each model's training data is noted next to its result.

---

### 3.1 Third subset: vocadito (independent annotation)

The first round of scores (§4) showed that every non-ZJU model starts notes ~+60–75 ms after the M4Singer/GTSinger
ground truth, while ROSVOT (made by the same ZJU lab) has ~0 ms bias. The likely cause is labelling convention:
ZJU labels a note from the syllable's consonant, OpenVPI and others from the vowel. To separate
"transcribes well" from "shares the benchmark's labelling convention", we added
**vocadito** (Bittner et al. 2021, CC BY 4.0, Zenodo 5578807): 40 solo-vocal excerpts in 7 languages, each
annotated by two annotators. GT = A1. A2 is scored as a "model" (`human_A2`) to give the human-agreement ceiling.
`evaluate.py` now also reports ±100 ms-onset variants and the median onset bias.

---

## 4. Results

Note-level F1 (mean over clips). COnP = onset ±50 ms and pitch ±50 cents. COnPOff also requires the offset.
`_100` = onset ±100 ms. bias = median (est − ref) onset in ms.

| Model (best config) | M4Singer COnP | GTSinger COnP | **vocadito COnP** | vocadito COnPOff | vocadito bias | Training data overlap with the benchmark |
|---|---|---|---|---|---|---|
| human A2 (ceiling) | – | – | **0.723** | 0.633 | −0.1 | – |
| GAME-1.0-medium, zh, seg 0.1 | 0.242 | 0.251 | **0.588** | 0.297 | −2.6 | none known (private data) |
| SOME 0119 | 0.220 | 0.224 | 0.572 | 0.278 | +7.1 | none known (private data) |
| Basic Pitch | 0.237 | 0.206 | 0.486 | 0.308 | +12.8 | none |
| YourMT3+ MoE-PS | 0.215 | 0.242 | 0.469 | 0.266 | −5.1 | none (MIR-ST500, CMedia are the only vocals) |
| ROSVOT | **0.750** | **0.699** | 0.261 | 0.184 | −45.5 | trained with M4Singer; same lab and labelling convention as GTSinger |
| VocalParse (Qwen3-ASR-1.7B) | 0.164 | 0.244 | 0.020 | 0.006 | – | **all 120 M4Singer/GTSinger clips are in its training set** |

Reading:
- **On the independent subset, GAME is best** (0.59, 81% of human agreement), with SOME close behind.
  On M4Singer/GTSinger, their +65–75 ms bias alone pushes most onsets outside the ±50 ms window.
- **ROSVOT's M4Singer/GTSinger scores don't carry over.** On vocadito it falls to 0.26. Its lead comes from
  in-domain training and matching the ZJU labelling convention, which probably wouldn't hold for field recordings
  of Tibetan, Uyghur or Mongolian singing.
- YourMT3+ (on a vocal-only input) and Basic Pitch are instrument-agnostic and trail the singing-specific models.

Model details (from the setup agents; runners are in `src/transcription/models/<model>/`):
- **ROSVOT** (commit 3c8332b; Google Drive checkpoint sha256 b6055e81…):
  - The released checkpoint is trained on **M4Singer only**. Its `config.yaml` holds out only the first 200 items,
    so treat all M4Singer benchmark clips as seen in training.
  - Word boundaries come from its RWBD model, which is also Mandarin/M4Singer-trained. That probably explains the
    vocadito collapse (onsets ~45 ms early, over-segmentation).
  - CPU only: on MPS (torch 2.1) the output is wrong. Runs at 6.7 s per audio minute.
- **VocalParse** (arXiv 2605.04613):
  - Qwen3-ASR-1.7B fine-tuned on ~2000 h of web-crawled Mandarin singing pseudo-labelled by ROSVOT, plus
    M4Singer and GTSinger.
  - It predicts note *values* plus one global BPM rather than timestamps, so onsets drift and free rhythm is
    impossible to represent. Pitch is compressed toward the middle of the range.
  - Slow: ~80–120 s per audio minute on MPS.
  - Not usable for melody. Its lyrics output could be useful metadata later.
- **YourMT3+** (HF Space commit 5e66c1e, MoE-PS checkpoint):
  - The vocal track is named "Singing Voice".
  - Faster on CPU than MPS: ~35–45 s per audio minute.
- **GAME** (commit f423934, GAME-1.0 release, MIT):
  - Trained on ~32 h of private labelled singing in zh/yue/ja/en, with noise and accompaniment augmentation
    (including a private Asian ethnic-instrument set).
  - ~5 s per audio minute on MPS.
- **SOME** (commit e523eef, 0119 checkpoint, CC BY-NC-SA 4.0):
  - Private DiffSinger-community singers, trained on clean vocals.

### 4.1 Accompaniment robustness (benchmark_mix / benchmark_sep)

Same 160 clips, each vocal mixed with a ChMusic instrumental excerpt at +3 dB vocal-to-accompaniment
(`build_mix_benchmark.py`). "sep" = BS-RoFormer vocals (`model_bs_roformer_ep_317_sdr_12.9755`) extracted from
the mix (`separate.py`).

| Model | input | M4Singer COnP | GTSinger COnP | vocadito COnP | vocadito COnP_100 |
|---|---|---|---|---|---|
| GAME | clean vocal | 0.242 | 0.251 | 0.588 | 0.671 |
| GAME | mix | 0.218 | 0.228 | 0.532 | 0.611 |
| GAME | **mix → BS-RoFormer** | 0.238 | 0.249 | **0.594** | 0.672 |
| GAME | mix → htdemucs | 0.232 | 0.238 | 0.587 | 0.671 |
| ROSVOT | clean vocal | 0.737 | 0.709 | 0.260 | 0.484 |
| ROSVOT | mix | 0.605 | 0.602 | 0.246 | 0.430 |

GAME already copes with accompaniment (−10% relative), and separating the vocals first recovers all of that loss.
ROSVOT loses more on the mix (−18% on its in-domain data).

Separation speed on a real 152 s folk recording (M1 Pro, MPS):
- BS-RoFormer: 370 s at the model-default overlap, 196 s at overlap 2 (autocast makes no difference)
- **htdemucs: 25 s**

Downstream accuracy is the same within GAME's run-to-run noise (0.587 vs 0.594), so the full dataset uses
**htdemucs**. BS-RoFormer would have taken ~30 h on this machine.

### 4.2 Decision

**Pipeline: htdemucs vocal separation → GAME-1.0-medium (lang zh, seg-threshold 0.1) → MIDI → MusicXML.**
- It is the best on the only benchmark independent of both training data and labelling convention (vocadito),
  at ~81% of human inter-annotator agreement on COnP.
- It is robust to accompaniment, and separation recovers what it loses.
- It is multilingual and has explicit accompaniment/noise augmentation, which matters for Tibetan, Uyghur,
  Mongolian and other minority-language field recordings.
- It is fast.

ROSVOT MIDI is also produced for every recording as a secondary transcription. It is the strongest model on
Mandarin studio singing under the ZJU labelling convention, and a second opinion is useful for later
quality control (agreement between the two can flag unreliable transcriptions).

### 4.3 Our own improvement: offset trim (`postprocess.py`)

GAME's offsets are its weak point: COnPOff 0.30 on vocadito, against 0.63 between human annotators.
Error analysis of matched notes shows its notes end systematically **late**. Median offset error was
+39 ms on vocadito, +58 ms on M4Singer and +67 ms on GTSinger; 45–57% of notes were more than 50 ms too long,
and only 8–13% too short.

We trim a constant from each offset, choosing the amount without touching test data:
- 2-fold cross-validation over singer-disjoint vocadito folds picked 40 ms and 60 ms.
- Held-out COnPOff went **0.299 → 0.357**.
- The M4Singer/GTSinger subsets agree: 0.115 → 0.150 at 40–60 ms.
- **50 ms** is used. Onsets and pitches are untouched, so COnP is unchanged.

Final pipeline (mix → htdemucs → GAME → trim) on the benchmark mixtures:

| subset | COnPOff | COnP | COn | COnP_100 |
|---|---|---|---|---|
| vocadito (independent) | **0.366** | **0.587** | 0.748 | 0.671 |
| human A2 vs A1 | 0.633 | 0.723 | 0.816 | 0.760 |
| M4Singer | 0.141 | 0.232 | 0.282 | 0.448 |
| GTSinger | 0.150 | 0.238 | 0.280 | 0.461 |

(M4Singer/GTSinger scores are limited by the +60–75 ms consonant-vs-vowel onset convention; see §3.1.)

### 4.4 MusicXML (`midi_to_musicxml.py`)

Model MIDI is in absolute seconds, so the conversion works like this:
1. A beat grid comes from librosa beat tracking on the **full mix**. Accompaniment carries the pulse better than
   the voice.
2. Note times are mapped onto that grid by interpolation, which follows tempo drift.
3. Notes are quantized to 16ths and eighth-triplets and forced into a single line: a note is cut at the next
   onset, and ornaments shorter than a 16th are dropped.
4. Gaps are filled with rests, and the result is written with music21.

The beat-interval CV is recorded in `_musicxml_stats.json`. CV > 0.25 sets `free_rhythm_suspect`: for 散板,
长调 and 信天游-style free rhythm, the metrical score is only an approximation, and the MIDI is the authoritative
transcription.

---

## 5. Full-dataset run

`src/transcription/run_all.sh` runs `transcribe_regions.py` as two parallel processes:
- **GPU side:** htdemucs → GAME → trim → MusicXML
- **CPU side:** ROSVOT, restricted to regions whose separation is complete (`--only-ready`)

`build_dataset_index.py` then writes `data/regions_transcription/dataset_index.csv` with metadata, paths and
QC columns (vocal-vs-accompaniment dB, notes/s, GAME–ROSVOT agreement, tempo, free-rhythm flag).

Pitfalls hit:
- **Architecture inheritance.** The first launch was started from the x86 `py312` Python. Its arm64 children
  then reported `platform.processor() == "i386"`, so audio-separator silently used the CPU (a 417 s song took
  278 s). Launched from an arm64 Python, the same song takes 53 s.
- **Output renaming.** audio-separator turns `__vocals` into `_vocals` in output names. The first
  `separate.py` didn't recognize the renamed file and deleted the vocals. Fixed.
- **Four stems.** htdemucs returns drums/bass/other/vocals. The accompaniment is saved as the sum of the three
  non-vocal stems.
- **Sequential throughput.** Running every step in order took ~40 min per region, with the GPU idle during
  ROSVOT (CPU-only). Splitting GPU and CPU work into parallel processes fixed that.

**Instrumental fallback.** 2 of the first 170 recordings came out with near-silent separated vocals
(−70 and −87 dB, against −17 and −33 dB accompaniment): the 客家 天公落水 and a Bai 背盐调 rendition, both
instrumental. GAME wrote no MIDI and ROSVOT gave 0 notes. For any recording where GAME finds no singing,
`transcribe_regions.py` now transcribes the full mix with YourMT3+ (multi-instrument).
`dataset_index.csv` records which model produced each primary transcription (`transcription_model`).

**First pass (2026-09-29, 170 recordings, 9.6 h of audio):** all 170 transcribed (168 GAME, 2 YourMT3+).
Median GAME–ROSVOT agreement per region, as note F1 with onset ±100 ms and pitch ±50 c, ranges from 0.35
(北方草原, Mongolian long-song melisma) to 0.51 (客家). That fits how differently the two models behave on the
benchmark. Low per-recording agreement is kept in the index as a QC flag.

`follow_downloads.sh` then keeps running passes every 15 minutes until the downloader finishes, and finally
rebuilds the index.

Sanity check on real recordings (东北部平原, first 90 s, GAME notes vs a pYIN median per note on the separated
vocals): 71–80% of notes within ±0.5 semitone, 0–2% octave errors.

### 5.1 Recovering the last failed downloads (`src/secaiqu/download_fallbacks.py`)

After the throttled pass, 27 of 600 candidates had failed, nearly all with transient `HTTP 403`.
- A retry with the `tv,web_safari` player clients recovered only 2. Every other video failed with "The page needs
  to be reloaded", which that client causes.
- `download_fallbacks.py` then tries a cascade per video: yt-dlp + cookies with player clients
  default/mweb/ios/web_embedded/android_vr/tv_simply, then yt-dlp without cookies, then Invidious and Piped API
  proxies, and optionally search-based replacement.
- It recovered **all 25**: 23 with the default client on a plain retry (the 403s were transient), 1 with `mweb`,
  1 with `web_embedded`.
- The proxy and replacement stages were never needed. Every attempt is logged in
  `data/regions_audio/fallback_log.csv`.

### 5.2 Choosing the primary transcription (`select_primary.py`)

QC on the finished run turned up recordings whose GAME transcription covers almost none of the audio:
- **Instrumental-dominant tracks.** 堆谐/歌舞 song-and-dance where only 3–8% of the separated vocal stem is
  active, and pieces the curators labelled as songs that are really instrumental (e.g. 耍龙调, 天公落水).
  One of these got an *empty* GAME MIDI, which the first fallback (no file) missed.
- **Sung recordings GAME under-transcribes.** 2 cases where GAME covers 6% of the duration and ROSVOT 33–67%.
  Lowering GAME's `est-threshold` to 0.1 or 0.05 barely helped (+0–1%, except one recording).

Explicit rules, with coverage = total note duration / recording duration:
1. **instrumental:** GAME found nothing, or GAME cov < 0.05 and ROSVOT cov < 0.10 → YourMT3+ on the full mix.
2. **vocal_rosvot:** GAME cov < 0.15 and ROSVOT cov > max(0.20, 2 × GAME cov) → ROSVOT.
3. **vocal_game:** everything else → GAME + 50 ms offset trim.

Result: 586 GAME, 12 YourMT3+ (instrumental), 2 ROSVOT. Across the dataset, median coverage is 0.58 for GAME and
0.78 for ROSVOT.

Known limitation: `free_rhythm_suspect` never fires (0/600). librosa's beat tracker imposes a steady pulse,
so the beat-interval CV stays low even for 散板/长调. For free-rhythm genres, treat the MusicXML metre as
nominal and use the MIDI timing.

---

## 6. Final dataset (2026-09-29)

`data/regions_transcription/dataset_index.csv`: **600 recordings, 15 regions × 40, 32.6 h of audio,
all transcribed to MIDI + MusicXML.**

| Region | Recordings | Distinct songs | Hours | 原生态 recordings | Median GAME–ROSVOT agreement |
|---|---|---|---|---|---|
| 东北部平原 | 40 | 26 | 2.21 | 8 | 0.46 |
| 西北部高原 | 40 | 38 | 2.00 | 32 | 0.47 |
| 江淮 | 40 | 32 | 2.35 | 25 | 0.46 |
| 江浙平原 | 40 | 31 | 2.10 | 25 | 0.48 |
| 闽台 | 40 | 33 | 2.65 | 21 | 0.47 |
| 粤 | 40 | 34 | 2.31 | 24 | 0.49 |
| 客家特区 | 40 | 38 | 1.91 | 32 | 0.50 |
| 江汉 | 40 | 28 | 2.19 | 15 | 0.48 |
| 湘 | 40 | 35 | 1.82 | 21 | 0.47 |
| 赣 | 40 | 31 | 1.98 | 5 | 0.47 |
| 西南高原 | 40 | 26 | 1.71 | 9 | 0.44 |
| 西南多民族 | 40 | 40 | 2.31 | 39 | 0.42 |
| 藏族 | 40 | 40 | 2.07 | 35 | 0.41 |
| 新疆 | 40 | 37 | 2.64 | 28 | 0.41 |
| 北方草原 | 40 | 34 | 2.29 | 30 | 0.38 |

Per recording, the index gives:
- curation metadata: song, genre, performance type, ethnic group, area, URL, channel, upload date, licence
- paths to audio, separated vocals/accompaniment, primary MIDI + MusicXML, GAME MIDI and ROSVOT MIDI
- QC columns: vocal-vs-accompaniment dB, notes/s, GAME–ROSVOT agreement, selection reason

Reproduce (all code kept):
1. `search_candidates.py` / `curation/*`
2. `download_curated.py`, then `download_fallbacks.py`
3. `run_all.sh` (or `follow_downloads.sh`)
4. `select_primary.py`
5. `build_dataset_index.py`

Caveats for release:
- The audio is third-party YouTube content, so the redistributable part is the URLs, metadata and
  transcriptions, plus the download scripts.
- Songs a curator flagged as composed-in-folk-style (§1.2) remain in the dataset and are marked in `note`/`genre`.
- Items flagged "verify" by the curators (possible narration or multi-song concert excerpts) still need a listening
  check.

Run notes:
- GAME output varies by ±0.005 between runs (D3PM sampling).
- GAME-large is worse than medium.
- seg-threshold 0.1 beats the default 0.2 and 0.35.
- YourMT3+ is faster on CPU than on MPS on the M1 Pro (autoregressive decoding).

---

## 7. Critic and first-principles auditing (2026-09-29/30)

### 7.1 Critic (`src/transcription/critic/`)
Evidence, independent of the transcriber, on separated vocals (10 ms frames):
- **RMVPE F0** (ROSVOT's bundled pitch extractor), run on CPU in the rosvot env: `f0_rmvpe.py`
- **PESTO F0 + confidence** (mir-1k_g7), run on MPS: `f0_pesto.py`
- **stem dominance**: vocal-vs-accompaniment dB at f0 and its first harmonics: `stem_dominance.py`

Per note it takes the median pitch of the *core* (middle 60%, so attack and release glides are excluded) on
confident frames, with a tuning compensation (circular mean of the fractional semitones). Verdicts are ok,
wrong_pitch, octave_error, unvoiced and uncertain. Corrections are repitch (only when ROSVOT agrees), delete
unvoiced notes, and fill uncovered voiced segments (`critic.py`).

Pitfall: `pesto.load_model(...)(x)` returns its outputs in a different order from `pesto.predict`. Use
`pesto.predict`, and fold sub-second tails into the previous chunk, because PESTO's CQT padding fails on tiny inputs.

**Critic vs benchmark ground truth** (`eval_critic.py`, 3,949 GAME notes, first version):

| Verdict | Agreement with ground truth |
|---|---|
| ok | 85% of these notes are actually correct |
| unvoiced | precision 0.79 (0.96 on vocadito), recall 0.40 |
| wrong_pitch | precision 0.47–0.68, recall 0.23–0.37; the repitched value equals the GT only 48% of the time |

Net effect on benchmark F1: about +0.003, i.e. neutral. The underlying reason is that **a pitch-tracker critic
audits fidelity to the performance, not to the intended score**. 12% of notes agree with the singing but differ
from the annotated score note (M4Singer and GTSinger annotate intended notes). A critic built this way can't
catch those.

### 7.2 How different is the dataset from the benchmark? (`audit/domain_gap.py`)
Same evidence for the 160 benchmark clips and the 600 recordings. Medians, with the KS distance between them:

| Property | Benchmark | Dataset | KS |
|---|---|---|---|
| RMVPE/PESTO agreement on voiced frames | 0.87 | **0.44** | **0.74** |
| Pitch range (p95−p5, st) | 9.0 | 12.8 | 0.53 |
| Voiced fraction | 0.80 | 0.74 | 0.29 |
| Pitch wobble around a 150 ms median (st) | 0.26 | 0.34 | 0.31 |
| Tuning offset from A440 | 0.19 | 0.13 | 0.16 |
| Glide fraction | 0.33 | 0.34 | 0.08 |

The minority regions are the furthest from the benchmark: tracker agreement is 0.10 for 西南多民族, 0.16 for 藏族
and 0.18 for 新疆.

Decomposing the disagreement shows it is almost entirely *RMVPE voiced, PESTO under-confident*. When both
trackers are voiced they rarely disagree on pitch (3–14% of frames). In those RMVPE-only frames the vocal stem is
still +19 dB over the accompaniment at the tracked pitch (+33 dB in agreed frames), about 9 dB quieter: soft,
breathy or reverberant singing, not bleed. The exceptions are 新疆 and 北方草原 (+6–8 dB), where instruments double
the melody heterophonically.

**In-domain evidence rule:** a frame counts as confident when RMVPE is voiced AND (PESTO agrees OR the vocal stem
dominates the accompaniment by ≥ 12 dB). That covers 85% of voiced frames, against 44% from PESTO agreement alone.

### 7.3 Reference-free, in-domain checks
| Check | Script | Result |
|---|---|---|
| Score reference: same-title Anthology scores in a region-consistent province volume vs random scores from the same volume | `audit/score_reference.py` | 62 recordings. GAME 0.58 vs chance 0.45 (gap 0.13), beating chance on 71% of recordings. ROSVOT gap 0.11 |
| Cross-performance: same song, different performances vs different songs in the same region | `audit/cross_performance.py` | 121 pairs. GAME same 0.43 vs different 0.29 (gap 0.148). ROSVOT gap 0.116 |
| Invariance: 45 recordings (3/region), first 60 s | `audit/invariance.py` | GAME rerun vs itself: note F1 **0.835** (range 0.68–0.96). ±2 st pitch-shift: 0.69 (partly phase-vocoder artifacts) |

Both independent in-domain checks confirm the benchmark's model choice (GAME > ROSVOT). But GAME's stochastic
decoder changes ~16% of notes between identical runs. The benchmark only showed ±0.005 in aggregate F1, which hid
this.

### 7.4 Critic on the full dataset (`critic/run_dataset.py`)
Note verdicts over 586 vocal recordings (GAME primary):

| ok | wrong_pitch | octave_error | unvoiced | uncertain |
|---|---|---|---|---|
| 56.1% | 21.4% | 0.9% | 0.7% | 20.9% |

The wrong_pitch rate is about double the benchmark's. "All" corrections would repitch 14,858 notes (with ROSVOT
consensus), delete 1,681 and add 20,290. Missed confident-voiced time is 53 of 1,395 voiced minutes (3.8%).

**None of the corrections moves the in-domain checks beyond noise:**

| Variant | Score-reference gap | Cross-performance gap |
|---|---|---|
| GAME (no correction) | 0.130 | 0.148 |
| + repitch | 0.127 | 0.153 |
| + delete | 0.128 | 0.148 |
| + fill | 0.134 | 0.136 |
| + all | 0.127 | 0.144 |

These checks compare skeleton melodies (short notes dropped, repeats merged), which is too coarse for note-level
edits. Automatic evidence can't show whether a repitch is right, so corrections are **not applied** to the released
transcriptions until the human gold set (7.5) measures the critic's in-domain precision. The corrected variants are
kept in `midi/critic_*`.

### 7.5 Human-audited gold set (`audit/gold_sample.py`, `audit/gold_page.html`)
The sample is 150 notes, stratified by critic decision (repitch 60, ok 30, uncertain 20, fill 25, delete 15) and
round-robin over regions (seed 0).
- **Page:** each item is a separated-vocal clip with the note highlighted, plus two tones in blinded, randomized
  A/B order, played in the singer's own tuning.
- **Tone pairs:** repitch items compare the original with the corrected pitch. ok, uncertain, fill and delete items
  compare the note with a ±1 st foil.
- **Answers:** A, B, neither, no singing, or can't tell. The critic's category isn't shown, so the rater stays blind.
- **Storage:** ratings go to the artifact's database (collection `ratings`).
- **Artifact:** https://claude.ai/artifact/2d22Duf8owkvFQFx4xvYUU

Pending: ratings. From them we compute the absolute accuracy of the original notes (ok/uncertain strata), the
critic's repitch precision, and whether fill/delete are right. Those numbers then decide which corrections to apply.

### 7.6 GAME run-ensembling (`audit/ensemble.py`, `ensemble_vote.py`, `ensemble_dataset.sh`)
The invariance test showed that GAME's stochastic decoder changes ~16% of notes between identical runs. A
majority vote over runs needs no reference to justify it:
- **Voting rule:** same pitch, onsets within ±50 ms, present in ≥ half the runs; median times; monophony enforced.
- **Reference-free test:** 45 recordings, 6 runs. Two *disjoint* 3-run ensembles agree on **0.897** of notes, against
  0.841 for single runs, so about a third of the run-to-run noise is gone. Note counts barely change (103 vs 105 per
  recording), so the vote isn't just discarding hard notes.
- **Independent check:** 3-run ensemble + 50 ms trim on benchmark vocadito gives COnP 0.587 → **0.600** and
  COnPOff 0.366 → **0.380**, with small gains on M4Singer/GTSinger too.
- **Decision:** the dataset's vocal transcriptions become 3-run ensembles (`midi/game_ens3_pp`). Cost is 2 extra GAME
  passes, ~5–6 h on the M1 Pro.
