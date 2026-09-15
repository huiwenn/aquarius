# Gap Analysis Report

## Summary

- **Total items**: 45,611
- **Total datasets**: 11
- **Datasets**: anthology_chinese_folk_songs, chmusic, ctis, guqin_dataset, gz_isotech, jingju_singing_audio, m4singer, mgd, pmemo, pop909, traditional_chinese_folk_music_kaggle

## Modality Coverage

| Modality | Present | Missing | Coverage |
|----------|---------|---------|----------|
| audio | 1,842 | 43,769 | 4.0% |
| midi | 10,262 | 35,349 | 22.5% |
| musicxml | 8,725 | 36,886 | 19.1% |
| lyrics | 3,196 | 42,415 | 7.0% |

## Modality × Dataset Matrix

| dataset                               |   has_audio |   has_midi |   has_musicxml |   has_lyrics |   has_score |   has_jianpu |   has_metadata_only |   total_items |
|:--------------------------------------|------------:|-----------:|---------------:|-------------:|------------:|-------------:|--------------------:|--------------:|
| anthology_chinese_folk_songs          |           0 |       8654 |           8654 |         2497 |           0 |            0 |                   0 |          8654 |
| chmusic                               |          55 |          0 |              0 |            0 |           0 |            0 |                   0 |            55 |
| ctis                                  |         219 |          0 |              0 |            0 |           0 |            0 |                   0 |           219 |
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
| title | 42,883 | 2,728 | 94.0% | anthology_chinese_folk_songs, guqin_dataset, m4singer, mgd, pmemo (+1) |
| artist | 1,741 | 43,870 | 3.8% | guqin_dataset, pmemo, pop909 |
| genre | 45,611 | 0 | 100.0% | anthology_chinese_folk_songs, chmusic, ctis, guqin_dataset, gz_isotech (+6) |
| instrument | 2,508 | 43,103 | 5.5% | chmusic, guqin_dataset, gz_isotech, traditional_chinese_folk_music_kaggle |
| key | 2,374 | 43,237 | 5.2% | traditional_chinese_folk_music_kaggle |
| province | 42,789 | 2,822 | 93.8% | anthology_chinese_folk_songs, mgd, traditional_chinese_folk_music_kaggle |
| language | 42,884 | 2,727 | 94.0% | anthology_chinese_folk_songs, jingju_singing_audio, m4singer, mgd, pmemo (+1) |
| tempo_bpm | 2,374 | 43,237 | 5.2% | traditional_chinese_folk_music_kaggle |

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
