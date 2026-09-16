# Annotated Jingju Arias Dataset

## Source
- URL: http://compmusic.upf.edu/node/349
- Paper: CompMusic project, UPF Barcelona
- License: Check CompMusic/Zenodo for specifics
- Access method: CompMusic website / Zenodo
- Status: downloaded + inspected (annotations only; audio requires contacting rafael.caro@upf.edu)

## Paper & Description Insights
Contains 34 jingju arias manually segmented with annotations for role types and performance elements. Uses TextGrid annotation format. Part of the broader CompMusic Jingju research at UPF.

## Content & Taxonomy Analysis
- Time period: Traditional Beijing Opera
- Region: Beijing / northern China
- Genre/form: Jingju arias (complete aria-level performances)
- Instrumentation: Vocal (with possible accompaniment)
- Musical system: Traditional jingju
- Language: Mandarin Chinese (classical theatrical)
- Modalities: Audio, TextGrid annotations
- Labels: aria segmentation, role types, performance elements
- Related: See `jingju_singing_audio.md`, `jingju_phoneme_annotation.md`

## Download Log
- Date: 2026-09-15
- Size: 2.8 MB (annotations only; no audio)
- Method: CompMusic/Zenodo download, extracted as annotated_jingju_arias_1.0/

## Inspection Results
Inspected 2026-09-15 via `src/inspectors/jingju_arias_inspect.py`.

### TextGrid Annotations (Annotations/)
- 34 TextGrid files (UTF-16 encoded Praat TextGrids)
- 10 tiers per file:
  1. **aria** -- aria title and lyrics (Chinese)
  2. **MBID** -- MusicBrainz recording ID
  3. **artist** -- performer name (Chinese)
  4. **school** -- performance school (if applicable)
  5. **role-type** -- character role type (Chinese)
  6. **shengqiang** -- melodic mode type (Chinese)
  7. **banshi** -- metrical pattern sequence (Chinese)
  8. **lyrics-lines** -- line-level lyrics segmentation
  9. **lyrics-syllables** -- syllable-level lyrics segmentation
  10. **luogu** -- percussion pattern annotations

### Role Type Distribution (34 arias)
- laosheng (elderly male): 8 arias
- jing (painted face): 7 arias
- dan (female): 7 arias
- xiaosheng (young male): 6 arias
- laodan (elderly female): 6 arias

### Shengqiang (Melodic Mode) Distribution
- erhuang: 16 arias
- xipi: 18 arias

### ariasInfo.txt
- Detailed metadata for all 34 arias (UTF-16): aria name, MBID, artist, school, role-type, shengqiang, banshi sequence, luogu (percussion) patterns

### Tone-melody_subset.csv
- 20 entries mapping publication file names (Zhang 2014, 2015) to dataset file names
- Subset used for tone-melody relationship studies

## Schema Mapping

| Jingju Arias field | Unified schema field | Notes |
|---|---|---|
| TextGrid filename (e.g. "dan-erhuang_01") | `original_id` | Encodes role type + shengqiang + sequence |
| Filename prefix before "-" | `role_type` | dan/jing/laosheng/laodan/xiaosheng |
| Filename middle segment | `shengqiang` | erhuang/xipi |
| TextGrid tier "aria" | `title` / `lyrics_text` | Aria lyrics in Chinese (not extracted to master table) |
| TextGrid tier "artist" | `artist` | Performer name (not extracted to master table) |
| TextGrid tier "banshi" | `sub_genre` | Metrical pattern (not extracted to master table) |
| TextGrid tier "MBID" | external link | MusicBrainz recording ID |
| (dataset-level) | `genre` = "Beijing Opera" | |
| (dataset-level) | `has_audio` = false | Audio not included |
| (dataset-level) | `has_lyrics` = true | Lyrics in TextGrid tiers |

## Gap Assessment
- Annotations only -- no audio files included (audio requires contacting researchers)
- 5 role types covered (broader than singing_audio which has only 2)
- Rich structural annotations: lyrics, banshi, luogu, shengqiang per aria
- MusicBrainz IDs enable linking to external audio databases
- Useful for structural analysis of jingju arias (banshi sequences, percussion patterns)
- Relatively small (34 arias) but covers all major role types and both shengqiang systems
