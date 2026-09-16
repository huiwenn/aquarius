# Jingju Lyrics Datasets

## Source
- URL: https://compmusic.upf.edu/jingju-lyrics-datasets
- Paper: CompMusic project, UPF Barcelona
- License: Check CompMusic
- Access method: CompMusic website
- Status: downloaded + inspected

## Paper & Description Insights
Multiple datasets for analyzing expressive functions of metrical patterns through Beijing Opera lyrics. Includes NLP annotations for studying the relationship between text structure and musical expression in jingju.

## Content & Taxonomy Analysis
- Time period: Traditional Beijing Opera
- Region: Beijing / northern China
- Genre/form: Jingju lyrics / libretti
- Instrumentation: N/A (text only)
- Musical system: Jingju metrical patterns
- Language: Mandarin Chinese (classical theatrical Chinese)
- Modalities: Text (lyrics), NLP annotations
- Labels: metrical patterns, expressive function annotations, linguistic analysis
- Related: See other jingju datasets

## Download Log
- Date: 2026-09-15
- Size: 57 MB (jingju_lyrics_1.0.zip)
- Method: CompMusic website download

## Inspection Results
Inspected 2026-09-15 via `src/inspectors/jingju_lyrics_inspect.py`.

### Directory Structure (jingju_lyrics_1.0/)

#### plbs/ -- Per-Lyric by Banshi (1,247 files)
Individual aria lyrics organized by banshi (metrical pattern) type:
- Filename format: `{banshi}_{aria_name}.txt` (e.g., `慢板_武家坡.txt`)
- Banshi distribution:
  - 摇板 (yaoban, free meter): 449 files
  - 原板 (yuanban, original meter): 372 files
  - 快板 (kuaiban, fast meter): 233 files
  - 慢板 (manban, slow meter): 193 files
- Content: space-segmented lyrics text, one aria per file

#### plsqbs/ -- Per-Lyric by Shengqiang-Banshi (1,429 files)
Individual aria lyrics organized by shengqiang + banshi combination:
- Filename format: `{shengqiang}{banshi}_{aria_name}.txt`
- Distribution:
  - 西皮摇板: 380, 西皮原板: 283, 西皮快板: 233
  - 西皮慢板: 125, 二黄原板: 163, 二黄摇板: 160, 二黄慢板: 85

#### sqbs7_all_docs/ -- Aggregated by 7 Shengqiang-Banshi Types (7 files)
All lyrics of each shengqiang-banshi type concatenated into one file:
- 西皮摇板: 5,536 lines
- 二黄摇板: 1,390 lines
- 西皮原板: 1,253 lines
- 西皮快板: 1,249 lines
- 二黄原板: 818 lines
- 西皮慢板: 333 lines
- 二黄慢板: 138 lines
- Total: ~10,717 lines of lyrics

#### bs4_all_docs/ -- N-gram Analysis (14 files + data/ subdirectory)
- Pattern frequency analysis files (2-pattern through 10-pattern n-grams)
- `data/` subdirectory with raw per-banshi aggregated text (原板, 快板, 慢板, 摇板, all_concat)
- `ngrams-lyrics.py` + `run_ngrams.sh`: analysis scripts
- Top patterns: "我 这 里" (128), "但 愿 得" (124), "到 如 今" (100)

## Schema Mapping

| Jingju Lyrics field | Unified schema field | Notes |
|---|---|---|
| Filename (e.g. "西皮原板_三家店") | `original_id` | Encodes shengqiang+banshi + aria name |
| Filename prefix "西皮"/"二黄" | `shengqiang` | xipi or erhuang |
| Filename prefix after shengqiang | `sub_genre` | Banshi: 原板/快板/慢板/摇板 |
| Filename after "_" | `title` | Aria/opera name in Chinese |
| Text file content | `has_lyrics` = true | Space-segmented lyrics text |
| (dataset-level) | `genre` = "Beijing Opera" | |
| (dataset-level) | `has_audio` = false | Text-only dataset |
| (dataset-level) | `language` = "Chinese" | Classical theatrical Chinese |

## Gap Assessment
- Text-only dataset -- no audio, no musical notation
- Very large lyrics collection: ~2,700 unique arias across all directories
- Covers all 4 main banshi types and both shengqiang systems (xipi + erhuang)
- Word segmentation already applied (space-separated)
- Valuable for NLP analysis of jingju text patterns, metrical structure, formulaic expressions
- Complements the audio-focused jingju datasets for text-music relationship studies
- The 7-type aggregated files and n-gram analysis suggest prior research on formulaic language in jingju
