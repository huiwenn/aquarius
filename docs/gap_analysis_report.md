# Gap Analysis Report

## Summary

- **Total items**: 60,032
- **Total datasets**: 23
- **Datasets**: ace_opencpop, anthology_chinese_folk_songs, ccom_huqin, chinese_chorales, chmusic, cnpm, ctis, erhu_playing_technique, folkmusic_zenodo, gtsinger, guqin_dataset, guzheng_tech99, gz_isotech, jingju_arias, jingju_lyrics, jingju_phoneme_annotation, jingju_pitch_contour, jingju_singing_audio, m4singer, mgd, pmemo, pop909, traditional_chinese_folk_music_kaggle

## Modality Coverage

| Modality | Present | Missing | Coverage |
|----------|---------|---------|----------|
| audio | 14,623 | 45,409 | 24.4% |
| midi | 10,292 | 49,740 | 17.1% |
| musicxml | 9,082 | 50,950 | 15.1% |
| lyrics | 4,983 | 55,049 | 8.3% |

## Modality × Dataset Matrix

| dataset                               |   has_audio |   has_midi |   has_musicxml |   has_lyrics |   has_score |   has_jianpu |   has_metadata_only |   total_items |
|:--------------------------------------|------------:|-----------:|---------------:|-------------:|------------:|-------------:|--------------------:|--------------:|
| ace_opencpop                          |          30 |         30 |              0 |           30 |           0 |            0 |                   0 |            30 |
| anthology_chinese_folk_songs          |           0 |       8654 |           8654 |         2497 |           0 |            0 |                   0 |          8654 |
| ccom_huqin                            |         159 |          0 |             57 |            0 |          57 |            0 |                   0 |           159 |
| chinese_chorales                      |           0 |          0 |              9 |            0 |           0 |            0 |                   0 |             9 |
| chmusic                               |          55 |          0 |              0 |            0 |           0 |            0 |                   0 |            55 |
| cnpm                                  |         287 |          0 |              0 |            0 |           0 |            0 |                   0 |           287 |
| ctis                                  |         219 |          0 |              0 |            0 |           0 |            0 |                   0 |           219 |
| erhu_playing_technique                |          11 |          0 |              0 |            0 |           0 |            0 |                   0 |            11 |
| folkmusic_zenodo                      |       11966 |          0 |              0 |            0 |           0 |            0 |                   0 |         11966 |
| gtsinger                              |         229 |          0 |            229 |          229 |         229 |            0 |                   0 |           229 |
| guqin_dataset                         |           0 |          0 |             71 |            0 |           0 |            0 |                   0 |            71 |
| guzheng_tech99                        |          99 |          0 |              0 |            0 |           0 |            0 |                   0 |            99 |
| gz_isotech                            |           8 |          0 |              0 |            0 |           0 |            0 |                   0 |             8 |
| jingju_arias                          |           0 |          0 |              0 |           34 |           0 |            0 |                   0 |            34 |
| jingju_lyrics                         |           0 |          0 |              0 |         1429 |           0 |            0 |                   0 |          1429 |
| jingju_phoneme_annotation             |           0 |          0 |              0 |           65 |           0 |            0 |                   0 |            65 |
| jingju_pitch_contour                  |           0 |          0 |             62 |            0 |           0 |            0 |                   0 |           103 |
| jingju_singing_audio                  |          67 |          0 |              0 |            0 |           0 |            0 |                   0 |            67 |
| m4singer                              |         699 |        699 |              0 |          699 |           0 |            0 |                   0 |           699 |
| mgd                                   |           0 |          0 |              0 |            0 |           0 |            0 |               31761 |         31761 |
| pmemo                                 |         794 |          0 |              0 |            0 |           0 |            0 |                   0 |           794 |
| pop909                                |           0 |        909 |              0 |            0 |           0 |            0 |                   0 |           909 |
| traditional_chinese_folk_music_kaggle |           0 |          0 |              0 |            0 |           0 |            0 |                2374 |          2374 |

## Critical Metadata Gaps

| Field | Present | Missing | Coverage | Datasets |
|-------|---------|---------|----------|----------|
| title | 44,660 | 15,372 | 74.4% | anthology_chinese_folk_songs, ccom_huqin, gtsinger, guqin_dataset, jingju_lyrics (+5) |
| artist | 1,798 | 58,234 | 3.0% | ccom_huqin, guqin_dataset, pmemo, pop909 |
| genre | 60,032 | 0 | 100.0% | ace_opencpop, anthology_chinese_folk_songs, ccom_huqin, chinese_chorales, chmusic (+18) |
| instrument | 14,743 | 45,289 | 24.6% | ccom_huqin, chmusic, erhu_playing_technique, folkmusic_zenodo, guqin_dataset (+3) |
| key | 2,661 | 57,371 | 4.4% | cnpm, traditional_chinese_folk_music_kaggle |
| province | 42,845 | 17,187 | 71.4% | anthology_chinese_folk_songs, ccom_huqin, mgd, traditional_chinese_folk_music_kaggle |
| language | 45,070 | 14,962 | 75.1% | ace_opencpop, anthology_chinese_folk_songs, chinese_chorales, cnpm, gtsinger (+9) |
| tempo_bpm | 2,374 | 57,658 | 4.0% | traditional_chinese_folk_music_kaggle |

## Priority Gap-Filling Actions

### 1. key/mode
- **Impact**: high
- **Current coverage**: 4.4%
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
