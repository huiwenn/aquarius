# ChMusic

## Source
- URL: https://github.com/HaoranWeiUTD/ChMusic
- Paper: "ChMusic: A Traditional Chinese Music Dataset for Evaluation of Instrument Recognition" (2021) — https://arxiv.org/abs/2108.08470
- License: MIT (repository)
- Access method: Baidu Wangpan (pan.baidu.com/s/13e-6GnVJmC3tcwJtxed3-g, password: xk23) or Google Drive
- Status: ready

## Paper & Description Insights
ChMusic contains 55 traditional Chinese music excerpts for instrument recognition. Each of 11 instruments has 5 recordings. All recordings are single-instrument (monophonic labeling). Files are WAV format, dual-channel, 44,100 Hz, ranging 25–280 seconds. Total size ~530 MB.

The 11 instruments: Erhu, Pipa, Sanxian, Dizi, Suona, Zhuiqin, Zhongruan, Liuqin, Guzheng, Yangqin, Sheng.

Naming convention: "x.y.wav" where x = instrument number (1–11), y = music number (1–5). The dataset provides a baseline solution for instrument recognition.

Small but focused dataset. Limited to single-instrument excerpts — no ensemble or polyphonic content.

## Content & Taxonomy Analysis
- Time period: Traditional Chinese music (contemporary recordings of traditional repertoire)
- Region: Primarily Han Chinese traditions
- Genre/form: Traditional instrumental solo
- Instrumentation: 11 instruments spanning silk (Erhu, Zhongruan, Liuqin, Pipa, Sanxian, Guzheng, Yangqin), bamboo (Dizi), metal (Sheng includes metal reeds), gourd (Sheng). Covers plucked strings, bowed strings, wind instruments.
- Musical system: Traditional Chinese
- Modalities: Audio (WAV, 44,100 Hz, stereo)
- Labels: instrument identity only (single instrument per track)

## Download Log
- Date: 2026-09-15
- Source: Google Drive (file ID: 1rfbXpkYEUGw5h_CZJtC7eayYemeFMzij)
- Tool: gdown 6.2.0 + py7zr 1.1.3 (archive was 7-zip format, not zip)
- Archive size: 555 MB (529.4 MB compressed)
- Extracted to: `data/raw/chmusic/ChMusic/`
- Structure preserved: `ChMusic/Musics/` (55 WAV files) + `ChMusic/InstrumentsDescription/` (11 JPG + 2 PNG)
- Verification: all 55 expected WAV files present, naming matches x.y.wav convention
- Download script: `src/downloaders/chmusic_download.py`

## Inspection Results
- Inspection date: 2026-09-15
- Inspection script: `src/inspectors/chmusic_inspect.py`

### Directory Structure
```
data/raw/chmusic/
  ChMusic/
    InstrumentsDescription/
      1.jpg .. 11.jpg          (instrument photos, 1-4 MB each, 33.4 MB total)
      MusicsList.png           (105 KB, English music list)
      演奏曲目列表.png          (43 KB, Chinese music list)
    Musics/
      1.1.wav .. 11.5.wav      (55 WAV files, 855 MB total)
```

### Audio Properties
| Property | Value |
|----------|-------|
| Total files | 55 |
| Format | WAV (PCM_16) |
| Sample rate | 44,100 Hz (uniform) |
| Channels | 2 (stereo, uniform) |
| Bit depth | 16-bit |
| Total duration | 84.7 minutes (5,082.6 seconds) |
| Duration range | 25.9 s -- 280.5 s |
| Mean duration | 92.4 s |
| Total audio size | 855.0 MB |

### Per-Instrument Summary
| # | Instrument | Tracks | Total dur (s) | Range (s) | Size (MB) |
|---|-----------|--------|---------------|-----------|-----------|
| 1 | Erhu | 5 | 572 | 91--133 | 96.2 |
| 2 | Pipa | 5 | 436 | 56--123 | 73.4 |
| 3 | Sanxian | 5 | 253 | 33--82 | 42.6 |
| 4 | Dizi | 5 | 488 | 86--115 | 82.1 |
| 5 | Suona | 5 | 236 | 26--69 | 39.7 |
| 6 | Zhuiqin | 5 | 416 | 36--103 | 70.0 |
| 7 | Zhongruan | 5 | 479 | 71--127 | 80.7 |
| 8 | Liuqin | 5 | 359 | 37--113 | 60.4 |
| 9 | Guzheng | 5 | 585 | 78--175 | 98.4 |
| 10 | Yangqin | 5 | 355 | 52--94 | 59.7 |
| 11 | Sheng | 5 | 903 | 101--281 | 151.8 |

### Metadata
- No structured metadata files (CSV/JSON/TXT) found in the dataset.
- Labels are encoded entirely in filenames: instrument number (1--11) maps to instrument name.
- Non-audio files: 11 instrument description photographs (JPG), 2 music list images (PNG).

## Content & Taxonomy Analysis (Expanded)

### Instrument Families
- **Bowed strings (silk)**: Erhu (1), Zhuiqin (6)
- **Plucked strings (silk)**: Pipa (2), Sanxian (3), Zhongruan (7), Liuqin (8), Guzheng (9), Yangqin (10)
- **Wind -- bamboo**: Dizi (4)
- **Wind -- reed (metal/gourd)**: Suona (5), Sheng (11)

### Bayin (Eight-Sound) Classification
The 11 instruments map to traditional Chinese bayin categories:
- **Silk (si)**: Erhu, Pipa, Sanxian, Zhuiqin, Zhongruan, Liuqin, Guzheng, Yangqin (8 instruments)
- **Bamboo (zhu)**: Dizi (1 instrument)
- **Gourd (pao)**: Sheng (1 instrument)
- **Metal (jin)**: Suona (partial -- metal bell; also classified as reed) (1 instrument)
- **Missing bayin categories**: Stone (shi), Earth/clay (tu), Skin (ge), Wood (mu) -- no percussion or clay instruments

### Label Characteristics
- Single label per track (instrument identity)
- No multi-label or hierarchical labels
- No playing technique annotations
- No pitch, onset, or temporal segmentation annotations
- No metadata on musical pieces, composers, or performers

## Schema Mapping

## Gap Assessment
### Strengths
- Clean, uniform audio format (44,100 Hz, stereo, 16-bit PCM) -- no preprocessing needed
- Complete and balanced: exactly 5 tracks per instrument, no missing files
- Covers both string and wind instrument families
- MIT license enables unrestricted use
- Single-instrument recordings provide clean ground truth for instrument recognition

### Limitations
- **Very small scale**: only 55 files, 84.7 minutes total -- insufficient for training deep learning models alone
- **No structured metadata**: all labels encoded in filenames only, no CSV/JSON annotation files
- **No temporal annotations**: no onset detection, segment boundaries, or playing technique labels
- **Single-instrument only**: no ensemble, duet, or polyphonic content
- **Imbalanced duration**: Sheng has 903s total vs Suona with only 236s (3.8x difference)
- **No performer/piece metadata**: track provenance is unknown beyond instrument identity
- **Missing instrument families**: no percussion (drums, gongs, cymbals), no bowed strings beyond Erhu/Zhuiqin, no Guqin
- **Stereo but undocumented**: stereo field usage not specified (true stereo vs dual-mono unknown)
- **Actual size is ~855 MB uncompressed**, larger than the documented ~530 MB

### Relevance to Aquarius
- Useful as a small evaluation/test set for instrument recognition tasks
- Complements larger datasets (CCMusic, GZ-IsoTech) with additional instrument coverage
- Zhuiqin is rarely found in other datasets -- unique coverage
- Taxonomy provides a partial mapping to Chinese instrument classification systems
