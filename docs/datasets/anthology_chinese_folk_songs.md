# Anthology of Chinese Folk Songs

## Source
- URL: https://github.com/m-july/Anthology-of-Chinese-Folk-Songs-v251103
- Paper: Associated with research on optical recognition of printed Jianpu musical scores (2025)
- License: Not specified (original scanned images are copyrighted; MIDI/MusicXML derived data may have different terms)
- Access method: GitHub clone
- Status: downloaded + inspected

## Paper & Description Insights
Derived from 11 volumes of the *Anthology of Chinese Folk Songs* (《中国民间歌曲集成》). Contains 8,659 songs: 2,498 with lyrics and 6,161 melody-only pieces. Provided in MIDI and MusicXML formats — symbolic notation, not audio. Also includes debug visualization images.

Created through optical recognition of printed Jianpu (numbered notation) scores. Original scanned images not made available due to copyright.

This is one of the largest symbolic Chinese folk music collections. The geographic breadth (10 provinces) and folk song focus make it invaluable for melodic analysis and regional variation studies.

Anonymized subset also available separately: see `anonymized_anthology_folk_songs.md`.

## Content & Taxonomy Analysis
- Time period: Traditional Chinese folk music (historical through 20th century collections)
- Region: 10 provinces across 11 volumes — Jiangsu (2 vols), Guangdong, Hainan, Hebei (2 vols), Henan, Jilin, Shanghai, Sichuan, Tianjin
- Genre/form: Folk songs (民歌) — shan'ge (山歌), haozi (号子), xiaodiao (小调) likely represented. Song titles suggest work songs, love songs, narrative ballads, seasonal/agricultural songs, children's songs
- Instrumentation: Monophonic vocal melodies, single MIDI channel (channel 0), single part named "简谱旋律" (Jianpu melody)
- Musical system: All files report key of C and 4/4 time (OMR defaults). Actual pitch content spans MIDI notes 38-91 (D2-G6). Pitch analysis needed to determine actual modal content (pentatonic gong/shang/jue/zhi/yu modes likely)
- Language: Chinese — 2,497 songs have lyrics (character-level syllables aligned to notes, up to 55 lyric lines in some Guangdong songs due to known parsing bug)
- Modalities: MIDI (.mid), MusicXML (.musicxml), debug visualization PNG (.png) — symbolic only, no audio
- Labels available:
  - Province/volume (from directory structure)
  - Song number within volume (from filename prefix)
  - Song title in Chinese (from filename)
  - Lyrics text (character-by-character, lyrics-included subset only)
  - Work title in MusicXML (format: "页面_song_N")
- Labels NOT available: composer/collector, exact date, sub-genre classification, mode/scale, original page reference
- Notable: 8,658 MusicXML files verified (README states 8,659; 1 missing). Largest Chinese folk song symbolic dataset known

## Download Log
- Method: `git clone` from GitHub
- URL: https://github.com/m-july/Anthology-of-Chinese-Folk-Songs-v251103
- Date: 2026-09-15
- Size on disk: ~1.5 GB (436 MB .git, 310 MB lyrics-included, 756 MB melody-only)
- Version: v251103 (archive version, tagged for CSMT 2025 paper)

## Inspection Results

**File counts by volume:**

| Subset | Volume | MIDI | MusicXML | PNG |
|--------|--------|------|----------|-----|
| lyrics-included | Guangdong | 1,073 | 1,073 | 1,073 |
| lyrics-included | Jiangsu I | 788 | 788 | 788 |
| lyrics-included | Jiangsu II | 636 | 636 | 636 |
| melody-only | Hainan | 959 | 959 | 959 |
| melody-only | Hebei I | 513 | 513 | 513 |
| melody-only | Hebei II | 687 | 687 | 687 |
| melody-only | Henan | 987 | 987 | 987 |
| melody-only | Jilin | 865 | 867 | 867 |
| melody-only | Shanghai | 831 | 831 | 831 |
| melody-only | Sichuan I | 707 | 707 | 707 |
| melody-only | Tianjin | 608 | 610 | 610 |
| **Total lyrics-included** | | **2,497** | **2,497** | **2,497** |
| **Total melody-only** | | **6,157** | **6,161** | **6,161** |
| **Grand total** | | **8,654** | **8,658** | **8,658** |

**Count discrepancies vs README (states 2,498 lyrics + 6,161 melody = 8,659):**
- Lyrics-included: 2,497 actual vs 2,498 stated (1 file missing)
- 4 MusicXML files have no corresponding MIDI: jilin/759_祝愿歌, jilin/760_送亲, tianjin/582_卖糕干, tianjin/584_卖槟榔糕

**MIDI properties (200-file sample):**
- Format: MIDI type 1, 2 tracks (1 tempo/meta track + 1 note track), 1024 ticks/beat
- Channel: all channel 0, no program change (default piano)
- Tempo: uniform 80 BPM across all files (OMR pipeline default)
- Key signature: all report C major (OMR default, not actual musical key)
- Time signature: 4/4 throughout (may change within file per measure)
- Note counts: min=10, max=986, mean=96, median=69
- Pitch range: MIDI 38-91 (D2-G6 overall), per-file min typically 57-58, max typically 73
- Duration: 6-413 seconds, mean=51s, median=33s
- Velocity: uniform 90

**MusicXML properties (100-file samples each):**
- Structure: 1 part ("简谱旋律"), score-partwise format
- Work titles: all present, format "页面_song_N" (page_song_N)
- Key/time: all fifths=0 (C), 4/4 (OMR defaults; actual song keys vary)
- Lyrics-included subset: mean 96 notes, mean 60 with lyrics, median 2 lyric lines per note (max 55 in Guangdong due to known bug)
- Melody-only subset: mean 91 notes, 0 with lyrics, mean 22 measures

**Known issue:** Guangdong volume has spurious extra lyric lines in some songs where "attached lyrics" sections below the score were parsed as additional per-note lyric rows. The README suggests modal lyric-line count filtering as cleanup.

**File naming convention:** `{song_number}_{Chinese_title}.mid/.musicxml`, `{song_number}_{Chinese_title}_vis.png`

Inspector script: `src/inspectors/anthology_chinese_folk_songs_inspect.py`

## Schema Mapping

| Anthology field | Unified schema field | Notes |
|---|---|---|
| MIDI filename (`{num}_{title}.mid`) | `original_id` | `{volume}/{song_num}` |
| Title from filename | `title` | Part after first underscore |
| Volume directory name | `province` | Mapped via ANTHOLOGY_VOLUMES (10 provinces) |
| Subset ("lyrics-included" / "melody-only") | `has_lyrics` | true if lyrics-included subset |
| (all items) | `has_midi` = true | MIDI files |
| (all items) | `has_musicxml` = true | MusicXML alongside MIDI |
| (dataset-level) | `genre` = "folk song" | |
| (dataset-level) | `language` = "Chinese" | |

## Gap Assessment
- **No audio**: Symbolic-only dataset (MIDI + MusicXML). No audio recordings. Cannot be used for audio-related tasks (source separation, timbre analysis, ASR).
- **No sub-genre labels**: Songs are organized by province only. No genre/form classification (shan'ge vs haozi vs xiaodiao), no mood/tempo markings beyond the uniform 80 BPM default.
- **No real key/mode information**: All files report key of C and 4/4 time as OMR defaults. Actual musical keys and Chinese modes (gong/shang/jue/zhi/yu) must be computationally inferred from pitch content.
- **Monophonic only**: Single melodic line per song, no harmony, no accompaniment. Not usable for polyphonic analysis.
- **No performer/collector metadata**: No information about who collected or performed the songs, nor exact dates.
- **OMR artifacts**: Generated by optical recognition pipeline, so may contain recognition errors. The Guangdong lyric bug is documented; other subtle errors possible.
- **Incomplete coverage**: Only Sichuan I of likely multiple Sichuan volumes; provinces covered are concentrated in eastern/northern China. Western and southwestern provinces (Yunnan, Guizhou, Tibet, Xinjiang) absent.
- **4 missing MIDI files**: jilin/759, jilin/760, tianjin/582, tianjin/584 have MusicXML but no MIDI.
- **1 missing file overall**: 8,658 actual vs 8,659 stated in README.
