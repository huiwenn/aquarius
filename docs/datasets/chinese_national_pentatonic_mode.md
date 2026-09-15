# Chinese National Pentatonic Mode Database

## Source
- URL: https://ccmusic-database.github.io/en/database/csmtd.html
- Paper: Part of CSMTD / CCMusic ecosystem
- License: CC Attribution 4.0 (via CCMusic)
- Access method: Via CSMTD platform or HuggingFace
- Status: downloaded + inspected
- Parent: CSMTD (see `csmtd.md`). Download via parent.

## Paper & Description Insights
Contains 287 recordings demonstrating the five Chinese national pentatonic modes: Gong (宫), Shang (商), Jue (角), Zhi (徵), Yu (羽). Designed for mode classification research. Part of the CCMusic paper's core datasets.

Important for understanding the Chinese pentatonic tonal system — a fundamental concept in traditional Chinese music theory that differs from Western major/minor modes.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings
- Region: Han Chinese musical tradition
- Genre/form: Mode demonstration / classification examples
- Instrumentation: Not specified (likely keyboard/synthesized demonstrations)
- Musical system: Chinese pentatonic modes — explicitly labeled with all 5 modes (gong/shang/jue/zhi/yu)
- Modalities: Audio recordings
- Labels: pentatonic mode (5 classes), Chinese+English names
- Key feature: Explicit pentatonic mode labeling (rare across datasets)

## Download Log
- 2026-09-15: Downloaded via `load_dataset("ccmusic-database/CNPM")` + `save_to_disk()`
- Saved to: `data/raw/chinese_national_pentatonic_mode/`
- 287 items, Arrow format (7 shards)
- HF repo: `ccmusic-database/CNPM`

## Inspection Results
Inspected 2026-09-15.

### Features
- `audio`: Audio waveform data (WAV)
- `mel`: Mel spectrogram (image)
- `system`: Scale system index (0-10), encodes scale type (pentatonic/hexatonic/heptatonic variants)
- `tonic`: Tonic pitch class (0-11, C=0 through B=11)
- `pattern`: Pentatonic mode pattern (0-4: 宫 gong, 商 shang, 角 jue, 徵 zhi, 羽 yu)
- `type`: Scale type index (0-5)
- `mode`: Full Chinese mode label string (e.g., "D宫五声", "B角五声", "A徵七声清乐")

### Mode Distribution (287 items)
- 角 (jue): ~40 items (most represented)
- 宫 (gong): ~50 items
- 商 (shang): ~30 items
- 徵 (zhi): ~40 items
- 羽 (yu): ~35 items
- Includes variants: 五声 (pentatonic), 六声 (hexatonic, +变宫 or +清角), 七声清乐/雅乐/燕乐 (heptatonic)
- 12 different tonics represented (C through B)

### Scale Systems Present
Beyond basic 5-tone pentatonic, includes:
- 五声调式 (5-tone pentatonic)
- 六声+变宫 (6-tone with bian-gong)
- 六声+清角 (6-tone with qing-jue)
- 七声清乐 (7-tone qingyue scale)
- 七声雅乐 (7-tone yayue scale)
- 七声燕乐 (7-tone yanyue scale)

## Schema Mapping
- `mode` → `mode` (full Chinese mode label)
- `tonic` → `key` (mapped to note name)
- `pattern` → `folk_song_type` (pentatonic mode pattern name)
- `audio` → `has_audio`

## Gap Assessment
- This is the ONLY dataset with ground-truth Chinese pentatonic mode labels
- 287 items is small but invaluable as reference/validation data for mode detection algorithms
- Covers all 5 basic modes plus hexatonic and heptatonic variants — far richer than just 5-class
- Can serve as training data for pentatonic mode classifiers to apply to other datasets
- No title, artist, or other metadata — purely mode classification examples
