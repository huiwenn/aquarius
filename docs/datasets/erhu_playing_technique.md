# Erhu Playing Technique (ErhuPT)

## Source
- URL: https://huggingface.co/ccmusic-database
- Paper: Part of CCMusic (see `ccmusic.md`)
- License: CC Attribution 4.0 (via CCMusic)
- Access method: HuggingFace (ccmusic-database)
- Status: downloaded + inspected
- Parent: CCMusic (see `ccmusic.md`)

## Paper & Description Insights
ErhuPT contains 1,253 Erhu performance recordings for playing technique classification. Audio segmented at 550 milliseconds. Part of the six core datasets described in the CCMusic TISMIR paper.

The Erhu (二胡) is the most widely played Chinese bowed string instrument. This dataset captures its distinctive playing techniques including vibrato, glissando, and various bowing articulations.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings
- Region: Han Chinese
- Genre/form: Traditional instrumental technique demonstration
- Instrumentation: Erhu (bowed string, silk family)
- Musical system: Traditional Chinese
- Modalities: Audio (segmented clips), mel spectrograms
- Labels: playing technique classes, instrument identity
- Note: 1,253 clips (train/val/test: 748/251/254) — smaller than GZ_IsoTech (2,824) but covers the most important Chinese bowed instrument

## Download Log
- 2026-09-15: Downloaded via `load_dataset("ccmusic-database/erhu_playing_tech")` + `save_to_disk()`
- HF repo name: `ccmusic-database/erhu_playing_tech` (not `erhu_playing_technique`)
- On-disk size: 135 MB at `data/raw/erhu_playing_technique/`

## Inspection Results
- **Total clips**: 1,253 (train: 748, validation: 251, test: 254)
- **Columns**: audio, mel, label, name, cname, pinyin
- **Audio**: 44,100 Hz sampling rate
- **Mel spectrograms**: included as images
- **11 playing technique classes** (train split counts):
  - vibrato / 揉弦 (rou2_xian2): 59
  - trill / 颤音 (chan4_yin1): 149
  - tremolo / 震音 (zhen4_yin1): 104
  - staccato / 断弓 (duan4_gong1): 106
  - ricochet / 抛弓 (pao1_gong1): 39
  - pizzicato / 拨弦 (bo1_xian2): 66
  - percussive / 击弓 (ji1_gong1): 22
  - legato_slide_glissando / 连弓、滑音、连音: 98
  - harmonic / 泛音 (fan4_yin1): 18
  - diangong / 垫弓 (dian4_gong1): 30
  - detache / 分弓 (fen1_gong1): 57
- Labels include English name, Chinese name (cname), and pinyin transliteration

## Schema Mapping

## Gap Assessment
