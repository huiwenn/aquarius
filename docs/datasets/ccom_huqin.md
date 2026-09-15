# CCOM-HuQin

## Source
- URL: https://zenodo.org/records/11387046
- Paper: "CCOM-HuQin: An Annotated Multimodal Chinese Fiddle Performance Dataset" (TISMIR) — https://transactions.ismir.net/articles/10.5334/tismir.146
- License: CC-BY-4.0
- Access method: Zenodo download
- Status: ready

## Paper & Description Insights
First multimodal performance dataset of HuQin music. Created at Central Conservatory of Music (CCOM) with professional players. Contains 12,000+ single playing technique clips and 57 annotated musical excerpts.

Two subsets: (1) single playing technique recordings with various articulations (velocity, dynamics, pitch intervals); (2) classical musical excerpts with performance scores and transcription files with ground-truth note-level onset and playing technique annotations.

Provides high-quality audio AND aligned videos with multiple-camera views. Covers eight representative HuQin categories — the HuQin (胡琴) family includes bowed string instruments like erhu, zhonghu, gaohu, etc.

Highlights rich and complex playing techniques that carry regional and ethnic features.

## Content & Taxonomy Analysis
- Time period: Compositions spanning 1917 to 2017, plus pieces of ancient origin; performed by contemporary professionals
- Region: Pan-China — Guangdong (12 excerpts), Shanxi (7), Shandong (7), Henan (5), Hebei (4), Inner Mongolia (3), Shaanxi (2), Xinjiang (2), Beijing (2), Northeastern (2), Liaoning, Jiangsu, Jiangnan, Northern Shaanxi
- Genre/form: Traditional instrumental — HuQin solo playing technique clips and classical musical excerpts
- Instrumentation: 10 instrument directories (8 HuQin categories with sub-performers):
  - Erhu (二胡): 3 performers (Erhu-1, Erhu-2, Erhu-3) — 4,046 SinglePT clips + 21 excerpts
  - Soprano Banhu (高音板胡): 1,859 SinglePT clips + 7 excerpts
  - Alto Banhu (中音板胡): 1,770 SinglePT clips + 6 excerpts
  - Zhuihu (坠胡): 1,718 SinglePT clips + 3 excerpts
  - Gaohu (高胡): 1,382 SinglePT clips + 12 excerpts
  - Bass Banhu (低音板胡): 469 SinglePT clips + 5 excerpts
  - Zhonghu (中胡): 422 SinglePT clips + 0 excerpts
  - Tenor Banhu (次中音板胡): 329 SinglePT clips + 3 excerpts
- Musical system: Traditional Chinese
- Playing techniques (13 types): Port (2,844), Trill (1,572), DunG (1,461), Vibrato (1,296), PaoG (920), DuanG (842), TiaoG (840), DianG (763), Tremolo (669), Pizz (589), JiG (180), Appoggiatura (16), DaJiG (3)
- Modalities: Audio (48kHz mono WAV), video (1080p 29.97fps MP4, 3 camera angles — front/left/right), PDF scores, MusicXML scores, CSV annotations (onset, pitch, PT)
- Labels: playing technique (hierarchical: class + sub-class with BIE pattern), note-level onset/offset, frame-level F0 pitch, instrument category, velocity, dynamics, pitch interval
- Performers: 8 professional musicians, all graduates majoring in HuQin performing arts with 15+ years of experience from CCOM
- Notable: First multimodal HuQin-specific dataset; 11,995 SinglePT clips + 57 annotated excerpts; hierarchical filename naming convention encoding instrument/PT/speed/dynamics/interval

## Download Log
- Date: 2026-09-15
- Source: Zenodo record 11387046 (v2.0.1)
- Downloaded: CCOM-HuQin-v2.0.1-audios.zip (2.49 GB) — contains all audio, annotations, scores, metadata
- Extracted to: data/raw/ccom_huqin/CCOM-HuQin-v2.0.1-audios/
- Skipped (50 GB cap, total ~139.5 GB of video):
  - CCOM-HuQin-v2.0-videos-front-SinglePT.zip (35.85 GB)
  - CCOM-HuQin-v2.0-videos-right-SinglePT.zip (35.42 GB)
  - CCOM-HuQin-v2.0-videos-left-SinglePT.zip (35.12 GB)
  - CCOM-HuQin-v2.0-videos-front-Excerpts.zip (11.02 GB)
  - CCOM-HuQin-v2.0-videos-right-Excerpts.zip (11.02 GB)
  - CCOM-HuQin-v2.0-videos-left-Excerpts.zip (11.03 GB)
- Download script: src/downloaders/ccom_huqin_download.py
- Integrity: verified file size matches Zenodo API (2,677,440,110 bytes)

## Inspection Results
- Inspection script: src/inspectors/ccom_huqin_inspect.py
- Total extracted size: 5.21 GB (including zip)

### Directory Structure
```
CCOM-HuQin-v2.0.1-audios/
  metadata-v2.0.csv          (57 excerpts: name, region, date, instrument, duration, performer, composer, description)
  PTNamingConvention.pdf     (documentation of hierarchical filename encoding)
  readme-v2.0.1.pdf          (dataset documentation)
  xmlParser.py               (utility for parsing MusicXML annotations)
  SinglePT/                  (10 instrument subdirs, each with PT-type subdirs containing WAV clips)
  Excerpts/                  (9 instrument subdirs, each with piece subdirs containing 6 files each)
```

### File Counts
- Total files: 12,341
  - .wav: 12,052 (11,995 SinglePT + 57 Excerpts)
  - .csv: 172 (3 per excerpt: onset, pitch, PT)
  - .pdf: 59 (57 excerpt scores + 2 documentation PDFs)
  - .musicxml: 57 (one per excerpt)
  - .py: 1 (xmlParser.py)

### Audio Specifications
- Format: WAV, 48 kHz, mono
- SinglePT bit depth: PCM_32 (32-bit integer)
- Excerpts bit depth: FLOAT (32-bit float)
- SinglePT durations: 0.13s to 2.77s (mean 0.77s)
- Excerpt durations: 19.02s to 285.35s (mean 81.46s, total 77.4 min)
- Total audio duration: 4h 10min (2h 52min SinglePT + 77min Excerpts)

### SinglePT Clips per Instrument (11,995 total)
| Instrument | Clips | PT Types |
|---|---|---|
| Soprano Banhu | 1,859 | 11 (incl. JiG) |
| Alto Banhu | 1,770 | 11 (incl. JiG) |
| Zhuihu | 1,718 | 9 |
| Erhu-2 | 1,406 | 10 |
| Gaohu | 1,382 | 11 (incl. Appoggiatura, DaJiG) |
| Erhu-1 | 1,347 | 10 |
| Erhu-3 | 1,293 | 11 (incl. JiG) |
| Bass Banhu | 469 | 10 |
| Zhonghu | 422 | 10 |
| Tenor Banhu | 329 | 9 |

### Playing Technique Totals (13 types)
| PT | Count | Description |
|---|---|---|
| Port | 2,844 | Portamento (sliding) |
| Trill | 1,572 | Trills (DaYin, ShTrill, LoTrill) |
| DunG | 1,461 | Bowing: sharp attack |
| Vibrato | 1,296 | Vibrato (RVib, PVib, SVib) |
| PaoG | 920 | Bowing: galloping |
| DuanG | 842 | Bowing: constant pressure |
| TiaoG | 840 | Bowing: bouncing |
| DianG | 763 | Bowing: rapid wrist swing |
| Tremolo | 669 | Bowing: tremolo |
| Pizz | 589 | Pizzicato |
| JiG | 180 | Bowing: rarely used special effect |
| Appoggiatura | 16 | Grace note (Gaohu only) |
| DaJiG | 3 | Bowing: variant of JiG (Gaohu only) |

### Annotation File Formats
Each excerpt directory contains 6 files:
1. **{name}.wav** — audio recording
2. **{name}.pdf** — performance score with PT symbols
3. **{name}.musicxml** — symbolic score (MusicXML, score-partwise format)
4. **{name}-onset.csv** — note onset/offset/F0 (columns: onset_time, f0, duration)
5. **{name}-pitch.csv** — frame-level pitch trajectory (columns: time, f0; ~23ms hop)
6. **{name}-PT.csv** — note-level PT annotations (columns: onset, f0, duration, PT, PT1-1, PT1-2, PT1-3)
   - PT column: short code (e.g., "dp" for DPort)
   - PT1-1: PT class (e.g., "Port")
   - PT1-2: PT sub-class (e.g., "DPort")
   - PT1-3: PT sub-class detail
   - Uses BIE pattern for multi-note techniques (Begin/Intermediate/End)

### Metadata (metadata-v2.0.csv)
- 57 entries (one per excerpt)
- Fields: Name (CH), Filename (Pinyin), Region, Date, Instrument, Duration, Performer, Composers (CH/EN), Description
- Excerpts per instrument: Erhu (21), Gaohu (12), Soprano Banhu (7), Alto Banhu (6), Bass Banhu (5), Tenor Banhu (3), Zhuihu (3)
- No excerpts for Zhonghu

### SinglePT Naming Convention
- Files use hierarchical numerical naming: e.g., `1_1_8_1_1_1_1_1_1.wav`
- Each position encodes a parameter (instrument, PT class, sub-class, speed, dynamics, pitch interval, etc.)
- Full documentation in PTNamingConvention.pdf

## Schema Mapping

## Gap Assessment
- **Video not downloaded**: 6 video zips (~139.5 GB) skipped due to 50 GB cap. Video provides synchronized multi-camera views (front, left-hand, right-hand) at 1080p 29.97fps. Can be downloaded later if needed for multimodal analysis.
- **Zhonghu has no excerpts**: 422 SinglePT clips exist but zero annotated musical excerpts in the dataset.
- **Uneven instrument representation**: Soprano Banhu and Alto Banhu have the most clips; Tenor Banhu and Zhonghu have the fewest (329 and 422 respectively).
- **Rare techniques**: DaJiG (3 clips, Gaohu only) and Appoggiatura (16 clips, Gaohu only) are extremely sparse.
- **Onset CSV lacks header**: The onset CSVs appear to lack a proper header row (first row contains data, not column names), unlike the PT and pitch CSVs.
- **Rich metadata for excerpts only**: The metadata CSV covers only the 57 excerpts. SinglePT clip metadata is encoded solely in filenames via the naming convention.
- **Regional coverage**: Excerpts are heavily weighted toward Guangdong (12), Shanxi (7), Shandong (7), and Henan (5). Some regions have only 1-2 pieces.
- **Good for**: Playing technique classification/detection, onset detection, pitch tracking, instrument recognition, performance analysis.
- **Aquarius relevance**: Provides detailed playing technique taxonomy for HuQin family instruments; complements other Chinese music datasets that lack technique-level annotations. The hierarchical PT annotation (class/sub-class/BIE) is unique among our cataloged datasets.
