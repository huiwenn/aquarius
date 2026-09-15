# GZ_IsoTech

## Source
- URL: https://huggingface.co/datasets/ccmusic-database/GZ_IsoTech
- Paper: Part of CCMusic (see `ccmusic.md`)
- License: CC Attribution 4.0 (via CCMusic)
- Access method: HuggingFace (`ccmusic-database/GZ_IsoTech`), ModelScope mirror
- Status: downloaded + inspected
- Parent: CSMTD / CCMusic. Download via parent or directly from HuggingFace.

## Paper & Description Insights
GZ_IsoTech is a Guzheng playing technique classification dataset. Contains 2,824 variable-length audio clips: 2,328 from virtual sound banks and 496 performed by a professional artist. Total duration ~64 minutes.

Eight Guzheng techniques: Vibrato (颤音), Upward Portamento (上滑音), Downward Portamento (下滑音), Returning Portamento (回滑音), Glissando (刮奏/花指), Tremolo (摇指), Harmonics (泛音), Plucks (勾/打/抹/托).

Class imbalance: Upward Portamento dominates at 19.0% (536 clips), Tremolo smallest at 8.1% (228 clips). Most clips 0–1.5 seconds; only 49 exceed 3 seconds.

Each entry contains: audio clip, mel spectrogram, numerical label, English name, Chinese characters, pinyin.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings
- Region: Han Chinese
- Genre/form: Traditional instrumental technique demonstration
- Instrumentation: Guzheng (silk family, 丝)
- Musical system: Traditional Chinese
- Modalities: Audio (FLAC, 44,100 Hz), mel spectrograms, CSV annotations
- Labels: playing technique (8 classes), instrument identity, Chinese+English+pinyin names
- Playing techniques explicitly labeled (key distinguishing feature)

## Download Log

## Inspection Results

Inspected 2026-09-15 from Arrow files in `data/raw/gz_isotech/`.

### Default config (audio clips)
- **Splits**: train (2,328), test (496) — total 2,824 clips
- **Features**: audio (Audio 44100 Hz), mel (Image), label (ClassLabel, 8 classes), name (string, English technique name), cname (string, Chinese name), pinyin (string)
- **Audio properties**:
  - Sample rate: 44,100 Hz (uniform)
  - Channels: mono
  - Train — duration: 0.625s–6.375s, mean 1.330s, median 1.125s, std 0.615s, est. total ~51.6 min
  - Test — duration: 0.486s–4.208s, mean 1.225s, median 1.016s, std 0.642s, est. total ~10.1 min
  - Combined estimated total: ~61.7 minutes
- **Label distribution (train)**:
  - upward_portamento (上滑音): 488 (21.0%)
  - downward_portamento (下滑音): 333 (14.3%)
  - harmonics (泛音): 318 (13.7%)
  - glissando (刮奏/花指): 316 (13.6%)
  - returning_portamento (回滑音): 272 (11.7%)
  - tremolo (摇指): 205 (8.8%)
  - plucks (勾/打/抹/托): 204 (8.8%)
  - vibrato (颤音): 192 (8.2%)
  - Imbalance ratio: 2.54:1 (moderate)
- **Label distribution (test)**: Different proportions — plucks dominates at 27.2%, tremolo lowest at 4.6%. Imbalance ratio 5.87:1. Test set distribution differs substantially from train.
- **Text fields**: 8 unique values each for name, cname, pinyin — consistent 1:1:1 mapping.

### Eval config (spectrograms)
- **Splits**: train (2,389), validation (253), test (257) — total 2,899 clips
- **Features**: mel (Image), cqt (Image), chroma (Image), label (ClassLabel, 8 classes). No audio.
- Train has 61 more clips than default train — likely augmented or includes additional clips from processing.
- Label distributions similar to default, with same 8 technique classes.

### Data on disk
- Total size: ~581 MB

## Schema Mapping

| GZ_IsoTech field | Unified schema field | Notes |
|---|---|---|
| `label` (technique name) | `original_id` | Technique class label |
| `label` | `playing_technique` | 8 guzheng technique classes |
| (dataset-level) | `instrument` = "Guzheng" | |
| (dataset-level) | `bayin_family` = "silk" | |
| (dataset-level) | `has_audio` = true | WAV, 44100 Hz |
| (dataset-level) | `granularity` = "clip" | One entry per technique class |

## Gap Assessment
- **Train/test distribution mismatch**: Train split is dominated by upward_portamento (21.0%) while test split is dominated by plucks (27.2%). This is by design — the test set contains real performer recordings (496 clips) while train contains virtual sound bank clips (2,328). This split tests generalization from synthetic to real performance.
- **No validation split in default config**: Default has only train/test. The eval config adds a validation split but without audio. For audio-based tasks, a custom validation split from train is needed.
- **Small dataset**: Only 2,824 clips, ~62 minutes total. Suitable for technique classification but may need augmentation for deep learning.
- **Moderate class imbalance**: 2.54:1 in train, manageable with standard balancing techniques.
- **Strength — complementary to Guzheng_Tech99**: GZ_IsoTech provides isolated technique clips (clip-level labels), while Guzheng_Tech99 provides frame-level technique detection in full compositions. Together they cover both classification and detection tasks for Guzheng techniques.
- **Virtual vs. real split**: The train/test split explicitly separates virtual sound bank (train) from real performer (test) — a strength for evaluating model robustness, but users must be aware of this domain gap.
