# Anonymized Subset of Anthology of Chinese Folk Songs

## Source
- URL: https://github.com/m-july/Anonymized-Subset-of-Anthology-of-Chinese-Folk-Songs
- Paper: Same as parent (see `anthology_chinese_folk_songs.md`)
- License: Not specified
- Access method: GitHub clone
- Status: ready
- Parent: Anthology of Chinese Folk Songs (see `anthology_chinese_folk_songs.md`). Anonymized/curated subset.

## Paper & Description Insights
An anonymized subset of the full Anthology, created for double-blind review of the CSMT 2025 paper (arXiv: 2512.14758). Contains two subsets from Volume Jiangsu II only:

1. **Curated subset**: 334 individual songs (numbers 786-1100, 315 unique songs + 19 variation pieces) with lyrics, MIDI, MusicXML, and original scanned Jianpu images (316 JPGs, research-use only)
2. **Melody-only subset**: all songs from Jiangsu II merged into a single MIDI and MusicXML file (52,651 note events, ~251 minutes)

"Anonymized" means the repository and file naming were stripped of author/institution identification for double-blind review — the musical content and song titles are identical to the parent dataset.

## Content & Taxonomy Analysis
- Time period: Traditional Chinese folk music (historical through 20th century collections)
- Region: Jiangsu province only (Volume Jiangsu II, songs 786-1100 curated + full volume merged)
- Genre/form: Folk songs (民歌) from Jiangsu. Song titles suggest xiaodiao (小调), work songs, children's songs, narrative songs
- Instrumentation: Monophonic vocal melodies, single part "简谱旋律" (Jianpu melody)
- Musical system: Chinese traditional. Key/time in files report C/4-4 (OMR defaults). Actual modes must be inferred from pitch content
- Language: Chinese — curated subset has lyrics (character-level, 1-6 lyric lines per note, median 1)
- Modalities: MIDI (.mid), MusicXML (.musicxml), original scanned images (.jpg, curated subset only)
- Labels available:
  - Song number within volume (from filename)
  - Song title in Chinese with optional tune name in brackets (from filename, e.g. "song_786《孟姜女（一）》.mid")
  - Lyrics text (character-by-character, curated subset)
  - Work title in MusicXML (format: "曲目_N《title》")
  - Original scanned page images (316 JPGs, sequentially numbered)
- Labels NOT available: composer/collector, exact date, sub-genre classification, mode/scale
- Notable: Only subset with original scanned Jianpu images. Curated subset is a high-quality selection suitable for OMR evaluation

## Download Log
- Method: `git clone` from GitHub
- URL: https://github.com/m-july/Anonymized-Subset-of-Anthology-of-Chinese-Folk-Songs
- Date: 2026-09-15
- Size on disk: ~607 MB (289 MB .git, 308 MB Curated, 10 MB Melody-only)
- Version: For CSMT 2025 reviewers (dated 2025-09-01 per parent README)

## Inspection Results

**File counts:**

| Subset | MIDI | MusicXML | JPG |
|--------|------|----------|-----|
| Curated | 334 | 334 | 316 |
| Melody-only | 1 (merged) | 1 (merged) | -- |
| **Total unique files** | **335** | **335** | **316** |

**Curated subset details:**
- Song number range: 786 to 1100 (from Volume Jiangsu II)
- 315 unique song numbers, 334 total files (19 are variation pieces sharing a song number)
- 316 original scanned JPGs (sequentially numbered 000010-000325, page-based not song-based)
- 18 fewer JPGs than songs: some songs share a page or a page image is missing

**Anonymization analysis:**
- What was anonymized:
  - Repository name: generic, no author identification
  - File naming changed from `{N}_{title}` to `song_{N}《title》`
  - MusicXML work titles changed from "页面_song_N" to "曲目_N《title》"
  - JPG files use sequential page numbers instead of song-keyed names
  - No author/institution metadata in MusicXML (same as parent — none to remove)
- What was NOT anonymized:
  - Song titles (Chinese folk song names preserved in full)
  - Musical content (MIDI/MusicXML data identical to parent)
  - Regional attribution (Jiangsu II identifiable from content)

**Curated MIDI properties (100-file sample):**
- Format: MIDI type 1, 2 tracks, 1024 ticks/beat
- Channel: all channel 0, no program change
- Tempo: uniform 80 BPM
- Key/time: C major, 4/4 (OMR defaults)
- Note counts: min=25, max=630, mean=89, median=73
- Duration: 14-252 seconds, mean=39s, median=30s

**Merged melody-only MIDI:**
- 2 tracks, 52,651 note_on events
- Duration: 15,070 seconds (~251 minutes / ~4.2 hours)
- Contains all Jiangsu II songs concatenated sequentially

**Curated MusicXML properties (100-file sample):**
- 1 part ("简谱旋律"), score-partwise format
- Work titles: all present, format "曲目_N《title》"
- Key/time: fifths=0, 4/4 (OMR defaults)
- Mean 86 notes per song, mean 51 with lyrics
- Lyric lines per note: min=1, max=6, median=1

**File naming convention:** `song_{number}《Chinese_title》[tune_name].mid/.musicxml`

Inspector script: `src/inspectors/anthology_chinese_folk_songs_inspect.py`

## Schema Mapping

## Gap Assessment
- **Subset only**: Contains only Volume Jiangsu II songs. Not representative of the full 10-province, 11-volume Anthology. Geographic coverage limited to one province.
- **No audio**: Symbolic-only (MIDI + MusicXML). Original scanned JPGs are page images, not audio.
- **No sub-genre labels**: No classification of songs by form (shan'ge, haozi, xiaodiao). Must be inferred from titles or content.
- **No real key/mode information**: All files report C/4-4 as OMR defaults. Actual musical keys and Chinese modes must be computationally inferred.
- **Monophonic only**: Single melodic line, no harmony or accompaniment.
- **Merged melody-only file**: The melody-only subset is a single concatenated file, making individual song extraction non-trivial (no song boundary markers in MIDI).
- **JPG-song mismatch**: 316 JPGs for 334 songs — some songs lack page images, or multiple songs share a page.
- **OMR artifacts**: Same recognition pipeline as parent dataset; potential errors in pitch/rhythm transcription.
- **Redundant with parent**: All curated songs (786-1100) are present in the full Anthology under lyrics-included/jiangsu2. This subset adds only the original scanned JPGs and the merged melody-only file.
- **Copyright restriction on images**: Original scanned JPGs are "research-use only" per README and will not be in the final public dataset.
