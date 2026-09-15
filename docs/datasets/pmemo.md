# PMEmo

## Source
- URL: https://github.com/HuiZhangDB/PMEmo
- Paper: "The PMEmo Dataset for Music Emotion Recognition" (ACM ICMR 2018) — https://dl.acm.org/doi/10.1145/3206025.3206037
- License: Research use (check paper for specifics)
- Access method: GitHub repository
- Status: downloaded + inspected
- Parent: Listed under CSMTD (see `csmtd.md`)

## Paper & Description Insights
PMEmo contains 794 songs with emotion annotations from 457 subjects. Designed for music emotion recognition/retrieval benchmarking.

Data includes: song metadata (title, artists, chorus timestamps), manually selected chorus clips (MP3), pre-computed audio features, manually annotated emotion labels (static labels for whole clips AND dynamic labels per 0.5-second segment), EDA physiological signals, song lyrics, and song comments from online Chinese and English music websites.

Notable for combining audio with physiological signals (EDA) — rare in MIR datasets. The dynamic emotion labeling at 0.5s granularity enables time-varying emotion analysis. Despite being created by a Chinese research group and listed under CSMTD, the actual song catalog is predominantly Western/international pop (only 5 of 794 artists have CJK names). The Chinese connection is the annotation context (Chinese university subjects, Netease Music comments in Chinese), not the music content itself.

## Content & Taxonomy Analysis
- Time period: Contemporary popular music (primarily 2016-2018 era)
- Region: International — despite being created in China, the song catalog is overwhelmingly Western/international pop. Only 5 of 794 artists have CJK names. Lyrics are 522 English-only, 107 mixed Chinese+English, 0 Chinese-only.
- Genre/form: Pop, hip-hop, R&B, electronic, dance (Western popular music). SoundCloud metadata includes a `genre` field.
- Instrumentation: Full pop arrangements (not separated, chorus clips only)
- Musical system: Western diatonic
- Language: Primarily English lyrics; Chinese text present in Netease Music comments (4.5M comment lines) and some mixed lyrics; SoundCloud comments in English (333K comment lines)
- Modalities: Audio (MP3 chorus clips), pre-computed audio features (OpenSMILE), EDA physiological signals, timestamped lyrics (LRC), online comments (Netease + SoundCloud)
- Labels: Emotion (static valence-arousal per song + dynamic per-0.5s frame), song metadata (title, artist, album, chorus timestamps)
- Notable: 401 unique EDA annotators (10-11 per song), 50 Hz EDA sampling, physiological signals rare in MIR, time-varying continuous emotion labels

**Taxonomy correction**: Earlier description said "Chinese popular music" — actual inspection shows the catalog is predominantly Western/international pop. The Chinese connection is the annotation context (Chinese university subjects, Netease Music comments) not the music itself.

## Download Log
- Date: 2026-09-15
- Source: Google Drive (updated 2019 version)
  - URL: https://drive.google.com/drive/folders/1qDk6hZDGVlVXgckjLq9LvXLZ9EgK9gw0?usp=sharing
- Method: `gdown --folder` via `src/downloaders/pmemo_download.py`
- Downloaded: PMEmo2019.zip (680 MB) + README.txt
- Extracted to: `data/raw/pmemo/dataset/PMEmo/PMEmo2019/`
- Unzipped size: 1,184 MB (1.2 GB)
- Status: Complete, all expected files present

## Inspection Results
Inspected via `src/inspectors/pmemo_inspect.py`.

### Directory Structure
```
PMEmo2019/
  metadata.csv (59 KB) — song metadata, 794 rows
  netease_soundcloud.csv (78 KB) — cross-platform music IDs, 646 data rows
  chorus/ (794 MP3 files, 460 MB)
  annotations/ (4 CSVs, 3 MB)
  EDA/ (794 CSVs, 150 MB)
  features/ (2 CSVs, 341 MB)
  comments/
    netease/ (514 TXT files)
    soundcloud/ (514 TXT files)
  lyrics/ (629 LRC files, 2 MB)
```

### Metadata (metadata.csv)
- 794 songs, IDs range 1-1000 (not contiguous, 794 of 1000 IDs used)
- Columns: musicId, fileName, title, artist, album, duration, chorus_start_time, chorus_end_time
- 403 unique artists, 784 unique titles
- 7 songs missing album info
- Only 5 artists with CJK characters (rest are Western artists)

### Chorus Audio
- 794 MP3 chorus clips
- Duration: 11.0s-88.0s (mean 37.9s, median 36.0s, std 14.2s)
- Distribution: <20s: 59, 20-30s: 171, 30-45s: 357, 45-60s: 134, 60-90s: 73
- Total audio: 8.4 hours
- File sizes: 173 KB - 1,376 KB (460 MB total)

### Emotion Annotations
**Static** (767 songs, 27 songs lack annotations):
- Arousal(mean): range [0.0875, 0.9750], mean=0.6224, std=0.1848
- Valence(mean): range [0.1250, 0.9125], mean=0.5966, std=0.1620
- Arousal quartiles: Q1=0.50, Q2=0.65, Q3=0.76
- Valence quartiles: Q1=0.49, Q2=0.63, Q3=0.73
- Inter-annotator std: Arousal [0.050, 0.317], Valence [0.057, 0.314]

**Dynamic** (767 songs, 36,434 total frame rows):
- 0.5s time resolution, first 15s removed per paper design
- Frame times: 15.5s-88.0s
- Frames per song: min=2, max=146, mean=47.5
- Dynamic Arousal range: [0.0954, 0.9713]
- Dynamic Valence range: [0.1066, 0.9297]

### EDA Physiological Signals
- 794 CSV files (one per song)
- 401 unique annotator IDs across all songs
- 10-11 annotators per song (consistently)
- 50 Hz sampling rate
- Each file: time(s) column + one column per annotator with EDA values
- 150 MB total

### Pre-computed Audio Features (OpenSMILE)
- static_features.csv: 794 songs x 6,374 columns (musicId + 6,373 features)
- dynamic_features.csv: 59,755 rows x 262 columns (musicId + frameTime + 260 LLDs per 0.5s frame)
- Features include: audspec, MFCC, F0, voicing, jitter, shimmer, etc.

### Lyrics (LRC)
- 629 LRC files (165 songs have no lyrics)
- All UTF-8 encoded
- Format: timestamped lyrics with [mm:ss.xx] per line
- Language: 522 English-only, 107 mixed Chinese+English, 0 Chinese-only
- Metadata tags present: [by:], [ti:], [ar:], [al:], [offset:]

### Comments
- Netease Music: 514 files, 40-295,876 lines each (mean 8,735), 4,489,831 total lines — primarily Chinese text
- SoundCloud: 514 files, 1-13,931 lines each (mean 649), 333,379 total lines — primarily English text
- netease_soundcloud.csv: maps musicId to platform IDs (neteaseId, soundcloudId), with duration, comment counts, download counts, like counts, genre
- 229 MB total

## Schema Mapping

| PMEmo field | Unified schema field | Notes |
|---|---|---|
| `musicId` | `original_id` | Integer music ID |
| `title` | `title` | Song title |
| `artist` | `artist` | Performer name |
| `album` | `album` | Album name |
| `duration` | `duration_seconds` | Duration in seconds |
| `Valence(mean)` | `emotion_valence` | From static_annotations.csv |
| `Arousal(mean)` | `emotion_arousal` | From static_annotations.csv |
| (dataset-level) | `has_audio` = true | MP3 chorus clips |
| (dataset-level) | `genre` = "pop" | Western pop music |
| (dataset-level) | `language` = "English" | Predominantly English |

## Gap Assessment
### Coverage
- 794 songs total, but only 767 have emotion annotations (27 songs missing static/dynamic labels)
- 629 of 794 songs have lyrics (79.2% coverage)
- 514 of 794 songs have comments from both platforms (64.7% coverage)
- EDA signals available for all 794 songs

### Limitations for Chinese Music Research
- **Critical**: Despite being created by a Chinese research group and listed under CSMTD, the actual music catalog is overwhelmingly Western/international pop (only 5 CJK artists out of 794). This dataset is NOT a Chinese music dataset by content.
- The Chinese dimension comes from: (a) Chinese annotators/subjects, (b) Netease Music comments in Chinese, (c) some mixed-language lyrics
- For Aquarius's goal of a unified Chinese music database, PMEmo's value is limited to its annotation methodology and the Chinese-language comment corpus, not its music content

### Strengths
- Rare combination of audio + physiological signals (EDA) + emotion labels
- Both static (whole-clip) and dynamic (0.5s) emotion annotations
- Large annotator pool (401 unique subjects, consistently 10-11 per song)
- Multi-modal: audio + features + lyrics + comments + EDA
- Pre-computed feature sets ready for ML pipelines

### Data Quality
- Well-structured CSV format throughout
- Consistent file naming (numeric IDs)
- Some ID gaps (794 songs from ID range 1-1000)
- 7 missing album entries in metadata
- Annotation coverage: 96.6% (767/794) — good but not complete
