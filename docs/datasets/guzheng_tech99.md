# Guzheng_Tech99

## Source
- URL: https://huggingface.co/datasets/ccmusic-database/Guzheng_Tech99
- Paper: Part of CCMusic (see `ccmusic.md`)
- License: CC Attribution 4.0 (via CCMusic)
- Access method: HuggingFace (`ccmusic-database/Guzheng_Tech99`), ModelScope mirror
- Status: downloaded + inspected
- Parent: CSMTD / CCMusic. Download via parent or directly from HuggingFace.

## Paper & Description Insights
Frame-level annotation dataset for Guzheng playing technique detection. 99 solo compositions by professional musicians in studio settings. 63,352 annotated labels total. Average duration 91.56s per composition, total ~151 minutes. Size ~2.16 GB.

Seven labeled techniques: Vibrato (chanyin 颤音), Plucks (boxian 拨弦), Upward Portamento (shanghua 上滑), Downward Portamento (xiahua 下滑), Glissando (huazhi/guazou/lianmo/liantuo), Tremolo (yaozhi 摇指), Point Note (dianyin 点音).

Each note annotated with: onset time, offset time, pitch, technique classification. Data splits: train 79 / val 10 / test 10 compositions.

Notable class imbalance: Plucks represent 74.88% of all labels.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings of traditional repertoire
- Region: Han Chinese
- Genre/form: Traditional Guzheng solo
- Instrumentation: Guzheng (silk family)
- Musical system: Traditional Chinese
- Modalities: Audio (FLAC, 44,100 Hz), CSV annotations, mel spectrograms
- Labels: playing technique (7 classes), onset/offset times, pitch
- Key feature: Frame-level technique annotations with pitch — enables fine-grained temporal analysis

## Download Log

## Inspection Results

Inspected 2026-09-15 from Arrow files in `data/raw/guzheng_tech99/`.

### Default config (full compositions with note-level annotations)
- **Splits**: train (79), validation (10), test (10) — total 99 compositions
- **Features**: audio (Audio 44100 Hz), mel (Image), label (Sequence of {onset_time: float32, offset_time: float32, IPT: ClassLabel(7 classes), note: int8})
- **Audio properties**:
  - Sample rate: 44,100 Hz (uniform)
  - Train — duration: 32.89s–327.80s, mean 95.20s, median 80.15s, est. total ~125.4 min
  - Validation — duration: 50.39s–117.42s, mean 81.87s, est. total ~13.7 min
  - Test — duration: 45.27s–164.76s, mean 91.62s, est. total ~15.3 min
  - Combined estimated total: ~154.3 minutes (~2.6 hours)
- **Annotation statistics (train, 79 compositions)**:
  - Total annotations: 12,551 note-level labels
  - Per composition: 30–443 annotations, mean 158.9
  - **Technique distribution (severe imbalance)**:
    - boxian/Plucks: 9,439 (75.21%) — dominates
    - chanyin/Vibrato: 1,604 (12.78%)
    - shanghua/Upward Portamento: 563 (4.49%)
    - huazhi/Glissando: 555 (4.42%)
    - xiahua/Downward Portamento: 174 (1.39%)
    - dianyin/Point Note: 160 (1.27%)
    - yaozhi/Tremolo: 56 (0.45%) — rarest
  - Distribution consistent across train/val/test: Plucks ~72-75%, Vibrato ~10-14%.
- **Pitch (MIDI note) range**: 38–86 (D2 to D6), mean 64.4, 35 unique pitches
- **Annotation duration**: 0.035s–6.823s, mean 0.624s, median 0.499s

### Eval config (windowed frame-level features)
- **Splits**: train (2,486), validation (278), test (311) — total 3,075 windowed segments
- **Features**: mel (Array3D, 128x258x1 float32), cqt (Array3D, 88x258x1 float32), chroma (Array3D, 12x258x1 float32), label (Array2D, 7x258 float32)
- Pre-computed spectrogram windows with frame-level multi-label technique activation. No audio.
- Label shape [7, 258]: 7 technique channels, 258 time frames per window.
- Frame-level technique proportions (sampled from train): boxian active in ~69% of frames, chanyin ~22%, others each <6%.

### Data on disk
- Total size: ~2.0 GB

## Schema Mapping

## Gap Assessment
- **Extreme class imbalance**: Plucks account for 75% of all annotations. Tremolo has only 56 annotations across 79 compositions. Frame-level metrics must be class-weighted. Standard accuracy metrics would be misleading.
- **Small composition count**: Only 99 compositions (79 train, 10 val, 10 test). While the total annotation count (15,838 across all splits) is decent, the effective sample diversity is limited by the small number of independent compositions.
- **Strength — note-level temporal annotations**: Each note has onset/offset times, pitch, and technique class. This enables onset detection, pitch tracking, and technique detection as distinct or joint tasks — a rare combination in MIR datasets.
- **Strength — complements GZ_IsoTech**: GZ_IsoTech has isolated clips for technique classification; this dataset has full compositions for technique detection/segmentation. Together they form a comprehensive Guzheng technique benchmark.
- **Pitch coverage**: 35 unique MIDI pitches spanning D2–D6 covers the standard Guzheng range well (21-string Guzheng spans approximately D2–D6).
- **Eval config design**: The windowed segments in eval are ready for frame-level classification models. The multi-label format (label shape [7, 258]) supports simultaneous technique detection, reflecting that some techniques co-occur (e.g., vibrato on a plucked note).
