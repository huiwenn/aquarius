# Jingju A Cappella Singing Audio and Boundary Annotation Dataset

## Source
- URL: https://zenodo.org/record/1245941
- Paper: CompMusic project, UPF Barcelona
- License: Creative Commons (check Zenodo for specifics)
- Access method: Zenodo download
- Status: downloaded + inspected

## Paper & Description Insights
Hierarchical boundary annotations for Beijing Opera (Jingju) a cappella singing at line, syllable, and phoneme levels. Part of the CompMusic Jingju research ecosystem at UPF Barcelona.

Related datasets from the same research group: Jingju Phoneme Annotation, Jingju Pitch Contour, Jingju Music Scores, Jingju Lyrics, Annotated Jingju Arias, BOPP. The extended dataset (zenodo.org/record/1245942 and zenodo.org/record/1286350) contains 120 arias / 1,265 melodic lines with metadata for singing evaluation.

## Content & Taxonomy Analysis
- Time period: Traditional Beijing Opera repertoire
- Region: Beijing / northern China opera tradition
- Genre/form: Jingju (京剧, Beijing Opera) — a cappella singing
- Instrumentation: Vocal only (opera singing)
- Musical system: Traditional Chinese (jingju melodic system with banshi rhythmic patterns)
- Language: Mandarin Chinese (classical theatrical pronunciation)
- Modalities: Audio (WAV), boundary annotations (TextGrid)
- Labels: line boundaries, syllable boundaries, phoneme boundaries, role type
- Related: See `jingju_phoneme_annotation.md`, `jingju_pitch_contour.md`, `jingju_arias.md`

## Download Log
- Date: 2026-09-15
- Size: 1.5 GB (wav_mono.zip + textgrid.zip + catalogues)
- Method: Zenodo download (record 1245941)

## Inspection Results
Inspected 2026-09-15 via `src/inspectors/jingju_singing_audio_inspect.py`.

### Audio (wav_left/)
- 65 mono WAV files total (44.1 kHz, 16-bit)
  - danAll (dan role type): 42 files
  - laosheng (elderly male role type): 23 files
- Total duration: 10,073 s (2.80 hours)
- Average duration per file: ~155 s

### TextGrid Annotations (textgrid/)
- 65 TextGrid files (1:1 match with WAV files)
  - danAll: 42 TextGrids
  - laosheng: 23 TextGrids
- Encoding: UTF-16
- 5 tiers per file (some files have up to 8):
  1. **line** -- line (phrase) boundary with Chinese lyrics
  2. **pinyin** -- syllable boundaries in pinyin (without padding)
  3. **dian** -- syllable boundaries (with padding characters)
  4. **dianSilence** -- syllable boundaries (silence merged with preceding syllable)
  5. **details** -- phoneme boundaries in X-SAMPA

### Catalogues
- `catalogue_dan.csv`: 39 entries (27 phonetically annotated)
  - Columns: File name, Work, Phonetically annotated, Details, Legend
- `catalogue_laosheng.csv`: 28 entries (23 phonetically annotated)
  - Columns: File name, Work, Phonetically annotated, Details, Legend
- Note: catalogue entries do not 1:1 match WAV count -- some entries share the same work (different recordings), and the directory contains additional files
- Legend encodes role-type abbreviation and shengqiang (melodic mode): erhuang, fan erhuang, gao bo zi, bang zi, si ping diao, xi pi

## Schema Mapping

## Gap Assessment
- Audio + annotations are complete and well-matched (65 WAV files, 65 TextGrids)
- Only 2 role types covered (dan, laosheng) -- no jing, laodan, xiaosheng
- Annotations are rich (line/syllable/phoneme levels) -- good for boundary detection, phoneme recognition, singing analysis
- No pitch or note-level annotation in this dataset (see jingju_pitch_contour for that)
- Complementary to the broader phoneme annotation dataset (same files, same format)
