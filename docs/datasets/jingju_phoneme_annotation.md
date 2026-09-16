# Jingju Phoneme Annotation

## Source
- URL: https://github.com/MTG/jingjuPhonemeAnnotation
- Paper: CompMusic project, UPF Barcelona / Queen Mary University of London
- License: CC-BY-NC-SA-4.0
- Access method: GitHub clone; audio via Zenodo (DOI: 10.5281/zenodo.344932)
- Status: downloaded + inspected

## Paper & Description Insights
Hierarchical boundary annotations for Beijing Opera a cappella singing. Covers two role types: dan (female roles) and laosheng (elderly male roles). Audio files are stereo/mono WAV at 44.1 kHz from two recording sources (Queen Mary University and MTG-UPF).

Annotations use Praat TextGrid format with 5 tiers per file: line boundaries with Chinese lyrics, pinyin syllable boundaries (with and without padding), and phoneme boundaries using X-SAMPA notation.

## Content & Taxonomy Analysis
- Time period: Traditional Beijing Opera
- Region: Beijing / northern China
- Genre/form: Jingju a cappella singing
- Instrumentation: Vocal only (dan and laosheng role types)
- Musical system: Traditional jingju
- Language: Mandarin Chinese (classical theatrical pronunciation, annotated in pinyin + X-SAMPA)
- Modalities: Audio (WAV, 44.1 kHz), Praat TextGrid annotations
- Labels: line boundaries, syllable boundaries, phoneme boundaries, role type (dan/laosheng), lyrics (Chinese), pinyin
- Related: See `jingju_singing_audio.md`, `jingju_pitch_contour.md`

## Download Log
- Date: 2026-09-15
- Size: 11 MB (GitHub clone, TextGrids only; audio at Zenodo DOI 10.5281/zenodo.344932)
- Method: `git clone https://github.com/MTG/jingjuPhonemeAnnotation`

## Inspection Results
Inspected 2026-09-15 via `src/inspectors/jingju_phoneme_annotation_inspect.py`.

### TextGrid Annotations
- 65 TextGrid files total (UTF-16 encoded Praat TextGrids)
  - dan/: 42 TextGrids
  - laosheng/: 23 TextGrids
- 5 tiers per file:
  1. **line** -- line (phrase) boundary with Chinese lyrics
  2. **pinyin** -- syllable boundary (without padding), silence annotated
  3. **dian** -- syllable boundary (with padding characters), silence annotated
  4. **dianSilence** -- syllable boundary, silence follows previous syllable
  5. **details** -- phoneme boundary in X-SAMPA notation

### Catalogues
- `catalogue - dan.csv`: 39 entries (27 phonetically annotated)
- `catalogue - laosheng.csv`: 28 entries (23 phonetically annotated)
- Columns: File name, Work, Phonetically annotated, Details, Legend
- Legend decodes abbreviation scheme: role-type prefix + shengqiang abbreviation
  - daeh = dan erhuang, daxp = dan xipi, lseh = laosheng erhuang, lsxp = laosheng xipi, etc.

### Included Code
- `pycode/`: demo.py, demo.ipynb (parsing examples), textgrid.py, textgridParser.py

### Phoneme Inventory
- Initials: m, f, n, l, g, h, r, y, w + grouped stops/affricates (b/p/d/t/k/j/q/x/zh/ch/sh/z/c/s -> "c")
- Special: v, N, J (non-pinyin pronunciations)
- Medial vowels: i, u, y
- Finals: simple (a, o, e, E, i, u, y, 1, M), compound (aI^, eI^, AU^, oU^), nasal (an, @n, in, AN, 7N, iN, UN), retroflexed (er)

## Schema Mapping

| Jingju Phoneme field | Unified schema field | Notes |
|---|---|---|
| TextGrid filename | `original_id` | Full filename without extension |
| Parent directory (dan/laosheng) | `role_type` | dan or laosheng |
| Filename prefix (daeh/daxp/lseh/lsxp/etc.) | `shengqiang` | Decoded via prefix map: daeh=erhuang, daxp=xipi, etc. |
| Catalogue CSV "Work" | `title` | Aria title + opera name (not extracted to master table) |
| TextGrid tier "details" | `phonemes` = true | X-SAMPA phoneme annotations |
| TextGrid tier "line" | `has_lyrics` = true | Line-level lyrics |
| (dataset-level) | `genre` = "Beijing Opera" | |
| (dataset-level) | `has_audio` = false | Audio on Zenodo separately |
| (dataset-level) | `license` = "CC-BY-NC-SA-4.0" | |

## Gap Assessment
- This is the **same set of 65 recordings** as jingju_singing_audio, with identical TextGrid annotations
- Audio not included in the GitHub clone (must be fetched separately from Zenodo)
- For Aquarius purposes, this dataset and jingju_singing_audio share the same underlying data
- Only 2 role types (dan, laosheng) -- 50 of 67 catalogue entries have phonetic-level annotations
- Strong phoneme-level labels suitable for singing pronunciation analysis, phoneme segmentation
