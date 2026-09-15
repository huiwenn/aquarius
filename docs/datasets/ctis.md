# Chinese Traditional Instrument Sound (CTIS)

## Source
- URL: https://huggingface.co/datasets/ccmusic-database/CTIS
- Paper: Part of CCMusic (see `ccmusic.md`)
- License: CC-BY-NC-ND-4.0
- Access method: HuggingFace (`ccmusic-database/CTIS`), ModelScope mirror
- Status: downloaded + inspected
- Parent: CCMusic platform (see `ccmusic.md`)

## Paper & Description Insights
CTIS contains 4,956 recordings covering 209 instrument varieties with 219 labeled classes (some instruments have variants). Total duration ~32.63 hours, average 23.7 seconds per recording (range: 0.28–494.25s). Size ~18.1 GB.

Includes traditional instruments, reformed versions, and ethnic minority instruments. Data cleaned to remove non-instrumental audio and unlabeled recordings.

Two subsets: default (4,956 original recordings) and eval (43,054 processed 2-second clips with silence removal). Audio at 44,100 Hz WAV. Labels include numeric class IDs, Chinese characters, and pinyin.

This is the most comprehensive Chinese instrument sound dataset available — 219 instrument classes is exceptional coverage including instruments from minority ethnic traditions.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings
- Region: Pan-China — includes Han and ethnic minority instruments
- Genre/form: Instrument sound recordings (isolated)
- Instrumentation: 219 instrument types spanning traditional bayin (八音) categories plus reformed and minority instruments
- Musical system: Various (instrument demonstrations, not mode-specific)
- Modalities: Audio (WAV, 44,100 Hz), mel spectrograms
- Labels: instrument identity (219 classes), Chinese+pinyin names
- Key feature: Broadest Chinese instrument coverage of any dataset (219 types)

## Download Log

## Inspection Results

Inspected 2026-09-15 from Arrow files in `data/raw/ctis/`.

### Default config (original recordings)
- **Split**: train only — 4,956 examples
- **Features**: audio (Audio 44100 Hz), mel (Image), label (ClassLabel, 219 classes), cname (string, 219 unique), pinyin (string, 219 unique)
- **Audio properties** (sampled 150 items):
  - Sample rates: 44,100 Hz and 48,000 Hz (mixed)
  - Channels: mono and stereo (mixed)
  - Duration: 0.50s–191.63s, mean 20.79s, median 11.23s, std 25.22s
  - Estimated total duration: ~28.6 hours
- **Label distribution**: 219 instrument classes. Highly imbalanced (ratio 108:1). Most common: L0266 (108 items), C0296 (70), L0045 (56). Least common: C0201 (1 item), D0284 (2), C0200 (2). Mean 22.6 items/class, median 20.
- **Label codes**: Prefixed by category — C=Chordophones (45 classes), D=Wind/drums (82 classes), L=Plucked/other (63 classes), T=Various (31 classes)
- **Chinese names sample**: 三弦, 中胡, 中阮, 丝弦, 中国大鼓, 二胡, etc.

### Eval config (processed 2-second clips)
- **Splits**: train (34,630), validation (4,212), test (4,212) — total 43,054 clips
- **Features**: mel (Image), cqt (Image), chroma (Image), label (ClassLabel, 219 classes). No audio — spectrograms only.
- **Label distribution**: Same 219 classes. Severe imbalance (ratio 292:1 in train). Most common: T0260 (1,170 clips), C0263 (745). Least common: several classes with only 4 clips.

### Data on disk
- Total size: ~17 GB (default: ~14 GB in 30 Arrow shards, eval: ~3.4 GB)

## Schema Mapping

| CTIS field | Unified schema field | Notes |
|---|---|---|
| `label` (class name) | `original_id` | Instrument class label |
| `label` | `instrument_code` | Same instrument class code |
| (dataset-level) | `has_audio` = true | WAV, 44100 Hz |
| (dataset-level) | `genre` = "traditional instrumental" | |
| (dataset-level) | `granularity` = "clip" | One entry per instrument class (219 classes) |

## Gap Assessment
- **Severe class imbalance**: 219 classes but some have only 1–4 recordings. Many rare instrument types (especially ethnic minority instruments). Will need careful handling in any classification benchmark — stratified sampling or class weighting needed.
- **Mixed sample rates**: Both 44,100 Hz and 48,000 Hz detected. Will need resampling to a uniform rate during preprocessing.
- **Mixed channels**: Both mono and stereo audio. Should standardize to mono.
- **No train/val/test split in default**: The default config has only a train split with all 4,956 recordings. The eval config provides train/val/test but only spectrograms — no audio. For audio-based tasks, a custom split strategy is needed.
- **Opaque label codes**: Label codes (C0090, D0015, etc.) are not self-documenting; Chinese names (cname) and pinyin provide the human-readable instrument identity. Mapping to standard instrument taxonomy (e.g., bayin categories) requires external reference.
- **Large storage footprint**: 17 GB for ~28.6 hours of audio — acceptable given WAV format at 44.1/48 kHz.
- **Strength — unique breadth**: 219 instrument types including ethnic minority instruments — unmatched coverage in any other Chinese instrument dataset. Complements GZ_IsoTech/Guzheng_Tech99 (single-instrument technique datasets) with pan-instrument identity classification.
