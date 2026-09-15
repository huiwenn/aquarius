# GZ_IsoTech

## Source
- URL: https://huggingface.co/datasets/ccmusic-database/GZ_IsoTech
- Paper: Part of CCMusic (see `ccmusic.md`)
- License: CC Attribution 4.0 (via CCMusic)
- Access method: HuggingFace (`ccmusic-database/GZ_IsoTech`), ModelScope mirror
- Status: ready
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

## Schema Mapping

## Gap Assessment
