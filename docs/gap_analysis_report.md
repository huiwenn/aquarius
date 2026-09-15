# Gap Analysis Report

## Summary

- **Total items**: 45,872
- **Total datasets**: 15
- **Datasets**: ace_opencpop, anthology_chinese_folk_songs, ccom_huqin, chmusic, ctis, erhu_playing_technique, gtsinger, guqin_dataset, gz_isotech, jingju_singing_audio, m4singer, mgd, pmemo, pop909, traditional_chinese_folk_music_kaggle

## Modality Coverage

| Modality | Present | Missing | Coverage |
|----------|---------|---------|----------|
| audio | 2,103 | 43,769 | 4.6% |
| midi | 10,292 | 35,580 | 22.4% |
| musicxml | 8,843 | 37,029 | 19.3% |
| lyrics | 3,287 | 42,585 | 7.2% |

## Modality × Dataset Matrix

| dataset                               |   has_audio |   has_midi |   has_musicxml |   has_lyrics |   has_score |   has_jianpu |   has_metadata_only |   total_items |
|:--------------------------------------|------------:|-----------:|---------------:|-------------:|------------:|-------------:|--------------------:|--------------:|
| ace_opencpop                          |          30 |         30 |              0 |           30 |           0 |            0 |                   0 |            30 |
| anthology_chinese_folk_songs          |           0 |       8654 |           8654 |         2497 |           0 |            0 |                   0 |          8654 |
| ccom_huqin                            |         159 |          0 |             57 |            0 |          57 |            0 |                   0 |           159 |
| chmusic                               |          55 |          0 |              0 |            0 |           0 |            0 |                   0 |            55 |
| ctis                                  |         219 |          0 |              0 |            0 |           0 |            0 |                   0 |           219 |
| erhu_playing_technique                |          11 |          0 |              0 |            0 |           0 |            0 |                   0 |            11 |
| gtsinger                              |          61 |          0 |             61 |           61 |          61 |            0 |                   0 |            61 |
| guqin_dataset                         |           0 |          0 |             71 |            0 |           0 |            0 |                   0 |            71 |
| gz_isotech                            |           8 |          0 |              0 |            0 |           0 |            0 |                   0 |             8 |
| jingju_singing_audio                  |          67 |          0 |              0 |            0 |           0 |            0 |                   0 |            67 |
| m4singer                              |         699 |        699 |              0 |          699 |           0 |            0 |                   0 |           699 |
| mgd                                   |           0 |          0 |              0 |            0 |           0 |            0 |               31761 |         31761 |
| pmemo                                 |         794 |          0 |              0 |            0 |           0 |            0 |                   0 |           794 |
| pop909                                |           0 |        909 |              0 |            0 |           0 |            0 |                   0 |           909 |
| traditional_chinese_folk_music_kaggle |           0 |          0 |              0 |            0 |           0 |            0 |                2374 |          2374 |

## Critical Metadata Gaps

| Field | Present | Missing | Coverage | Datasets |
|-------|---------|---------|----------|----------|
| title | 43,001 | 2,871 | 93.7% | anthology_chinese_folk_songs, ccom_huqin, gtsinger, guqin_dataset, m4singer (+3) |
| artist | 1,798 | 44,074 | 3.9% | ccom_huqin, guqin_dataset, pmemo, pop909 |
| genre | 45,872 | 0 | 100.0% | ace_opencpop, anthology_chinese_folk_songs, ccom_huqin, chmusic, ctis (+10) |
| instrument | 2,678 | 43,194 | 5.8% | ccom_huqin, chmusic, erhu_playing_technique, guqin_dataset, gz_isotech (+1) |
| key | 2,374 | 43,498 | 5.2% | traditional_chinese_folk_music_kaggle |
| province | 42,845 | 3,027 | 93.4% | anthology_chinese_folk_songs, ccom_huqin, mgd, traditional_chinese_folk_music_kaggle |
| language | 42,975 | 2,897 | 93.7% | ace_opencpop, anthology_chinese_folk_songs, gtsinger, jingju_singing_audio, m4singer (+3) |
| tempo_bpm | 2,374 | 43,498 | 5.2% | traditional_chinese_folk_music_kaggle |

## Priority Gap-Filling Actions

### 1. key/mode
- **Impact**: high
- **Current coverage**: 5.2%
- **Method**: computational inference from MIDI/audio pitch content
- **Confidence**: medium

### 2. Chinese pentatonic mode
- **Impact**: critical
- **Current coverage**: 0%
- **Method**: pitch-class analysis of MIDI/MusicXML content
- **Confidence**: medium
- **Note**: No dataset provides ground-truth mode labels

### 3. temporal/year
- **Impact**: medium
- **Current coverage**: 0%
- **Method**: artist lookup, genre-era mapping, publication dates
- **Confidence**: low

## Key Observations

1. **Metadata-only dominance**: ~75% of items are metadata-only (MGD catalog), skewing coverage stats. Audio coverage among audio-bearing datasets is much higher.

2. **Chinese mode labels**: Zero datasets provide ground-truth pentatonic mode (gong/shang/jue/zhi/yu). This is the single most important gap for a Chinese music database.

3. **Temporal metadata absent**: No dataset provides year/era. Must be inferred from artist, genre, and publication context.

4. **Composer attribution rare**: Only Guqin dataset has arranger/transcriber info. Most datasets track performer but not creator.

5. **Geographic coverage biased**: Folk music well-covered (31 provinces via MGD, 10 via Anthology). Other genres lack regional labels entirely.

6. **Emotion labels Western-only**: PMEmo has emotion annotations but on Western pop music. No Chinese-music emotion dataset exists.
