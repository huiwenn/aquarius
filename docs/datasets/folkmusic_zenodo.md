# FolkMusic / China Traditional Music Instrument Dataset

## Source
- URL: https://zenodo.org/records/8012071
- Paper: Associated with instrument recognition research
- License: CC Attribution 4.0 International
- Access method: Zenodo direct download (FolkMusic.zip, 5.6 GB)
- Status: downloaded + inspected

## Paper & Description Insights
A Chinese traditional music dataset for training instrument recognition models. Contains MP3 audio clips (3-second duration each, single instrument per clip) recorded in dual-channel at 44,100 Hz. Total compressed size 5.6 GB.

Covers 15 traditional Chinese instruments: Ba, Flute (Dizi), Dongxiao, Erhu, Guqin, Guzheng, Hulusi, Liuqin, Pipa, Sanxian, Sheng, Suona, Yangqin, Zhongruan, and Falling Qin (落琴).

Compared to ChMusic (11 instruments, 55 full tracks), this dataset has more instruments (15) and uses short 3-second clips for classification. Compared to CTIS (219 instrument types), this is smaller but more focused on common traditional instruments.

## Content & Taxonomy Analysis
- Time period: Traditional Chinese music
- Region: Han Chinese traditions
- Genre/form: Instrument recognition clips (isolated)
- Instrumentation: 15 instruments — Erhu, Pipa, Guqin, Guzheng, Dizi, Dongxiao, Hulusi, Liuqin, Sanxian, Sheng, Suona, Yangqin, Zhongruan, Ba, Falling Qin
- Musical system: Traditional Chinese
- Modalities: Audio (MP3, 44,100 Hz, 3s clips)
- Labels: instrument identity (15 classes)

## Download Log
- Date: 2026-09-15
- Method: Zenodo direct download (FolkMusic.zip, 5.6 GB)
- Extracted to: `data/raw/folkmusic_zenodo/`
- Result: 11,966 MP3 clips across 15 instrument directories (one corrupt file in ba/ reported during extraction)

## Inspection Results

### Directory Structure
```
data/raw/folkmusic_zenodo/
├── FolkMusic.zip          # Original archive (5.6 GB)
├── ba/                    # 647 clips
├── dizi/                  # 1,450 clips
├── dongxiao/              # 1,033 clips
├── erhu/                  # 193 clips
├── guqin/                 # 1,070 clips
├── guzheng/               # 1,275 clips
├── hulusi/                # 1,036 clips
├── liuqin/                # 122 clips
├── pipa/                  # 1,405 clips
├── sanxian/               # 85 clips
├── sheng/                 # 1,294 clips
├── suona/                 # 1,170 clips
├── yangqin/               # 883 clips
├── zhongruan/             # 162 clips
└── zhuiqin/               # 141 clips
```

### Audio Properties
| Property | Value |
|----------|-------|
| Total clips | 11,966 |
| Format | MP3 |
| Sample rate | 44,100 Hz |
| Channels | 2 (stereo) |
| Duration per clip | 3.00 seconds (uniform) |
| Total duration | ~35,898 seconds (~10 hours) |
| Total size (extracted) | ~5.4 GB |

### Per-Instrument Summary
| Instrument | Chinese | Clips | Bayin family |
|------------|---------|-------|-------------|
| Ba | 巴乌 | 647 | bamboo |
| Dizi | 笛子 | 1,450 | bamboo |
| Dongxiao | 洞箫 | 1,033 | bamboo |
| Erhu | 二胡 | 193 | silk |
| Guqin | 古琴 | 1,070 | silk |
| Guzheng | 古筝 | 1,275 | silk |
| Hulusi | 葫芦丝 | 1,036 | gourd |
| Liuqin | 柳琴 | 122 | silk |
| Pipa | 琵琶 | 1,405 | silk |
| Sanxian | 三弦 | 85 | silk |
| Sheng | 笙 | 1,294 | gourd |
| Suona | 唢呐 | 1,170 | metal |
| Yangqin | 扬琴 | 883 | silk |
| Zhongruan | 中阮 | 162 | silk |
| Zhuiqin | 坠琴 | 141 | silk |

### Notes
- Filename convention: `audio_{number}.mp3` — numbers are not sequential within or across directories
- The directory name "zhuiqin" corresponds to 落琴 (Falling Qin) per paper, but is more likely 坠琴 (Zhuiqin), consistent with ChMusic
- Class imbalance: Dizi has 17× more clips than Sanxian (1,450 vs 85)

## Schema Mapping

| FolkMusic field | Unified schema field | Notes |
|---|---|---|
| Directory name (e.g. "dizi") | `instrument` | Capitalized English name |
| Directory name | `instrument_pinyin` | Chinese name via lookup |
| Directory name | `bayin_family` | bamboo/silk/gourd/metal via lookup |
| Filename (e.g. "audio_412") | `original_id` | Stem without extension |
| (dataset-level) | `has_audio` = true | MP3, 44100 Hz, stereo, 3s |
| (dataset-level) | `genre` = "traditional instrumental" | |
| (dataset-level) | `granularity` = "clip" | 3-second clips |

## Gap Assessment

### Strengths
- Large scale: 11,966 clips, ~10 hours of audio
- 15 instrument classes covering major traditional Chinese instrument families
- Uniform format: all clips are 3s, 44100 Hz, stereo — no preprocessing needed
- CC-BY-4.0 license — freely redistributable
- Complements ChMusic (full tracks, 11 instruments) and CTIS (219 instrument types)

### Limitations
- **No metadata beyond instrument**: no piece title, performer, key, tempo
- **Short clips only**: 3-second segments, no full performances
- **MP3 compression**: lossy format, not ideal for fine-grained audio analysis
- **Class imbalance**: 17× ratio between largest and smallest classes
- **No technique labels**: unlike GZ_IsoTech or ErhuPT
- **No temporal annotations**: no onset, pitch, or beat data
- **Possible naming issue**: "zhuiqin" directory — confirm whether this is 坠琴 or 落琴
