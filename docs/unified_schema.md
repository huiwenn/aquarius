# Unified Schema for Aquarius

The superset of all metadata fields discovered across all collected datasets. Each row in the unified master table represents one **item** — the granularity varies by dataset (full song, segment, note, or entire collection). The `granularity` field tracks this.

## Identification

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `unified_id` | string | `<dataset>__<original_id>` | Generated |
| `dataset` | string | Source dataset name (lowercase_with_underscores) | All |
| `original_id` | string | ID within original dataset | POP909 (song_id), PMEmo (musicId), M4Singer (item_name), CTIS (label code), etc. |
| `granularity` | enum | `song` \| `segment` \| `note` \| `clip` \| `collection` | Derived |

## Content Metadata

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `title` | string (UTF-8) | Song/piece title (Chinese preferred) | POP909, PMEmo, Anthology, Guqin, MGD, M4Singer |
| `title_en` | string | English translation of title (if available) | — |
| `subtitle` | string | Sub-title or alternate title | MGD (Sub-Title) |
| `artist` | string | Performer/artist name | POP909, PMEmo, Guqin (演奏者) |
| `composer` | string | Composer/songwriter | — (gap in most datasets) |
| `arranger` | string | Arranger/transcriber | Guqin (打谱/记谱者) |
| `album` | string | Album name | PMEmo |
| `singer_id` | string | Singer identifier | M4Singer |
| `voice_type` | string | Vocal register (Soprano/Alto/Tenor/Bass) | M4Singer |
| `role_type` | string | Beijing Opera role type (dan/laosheng/jing/laodan/xiaosheng) | Jingju datasets |

## Temporal

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `period` | string | Historical period or era | — (largely missing, inferred from genre) |
| `dynasty` | string | Chinese dynasty (if applicable) | Guqin (琴曲来源 implies historical era) |
| `year` | int | Year of recording/composition | — (gap) |
| `score_source` | string | Historical score collection name | Guqin (琴谱来源, 琴曲来源) |

## Regional / Cultural

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `province` | string | Chinese province (31 standardized names) | MGD, Anthology, Kaggle |
| `region` | string | Broader region (North/South/Northeast/etc.) | MGD, Kaggle |
| `country` | string | Country of origin | GTSinger (multi-national) |
| `ethnic_group` | string | Ethnic group (Han, Uyghur, Mongolian, etc.) | MGD (implied by province/genre) |
| `location` | string | Specific location within province | MGD (Location) |

## Genre / Form

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `genre` | string | Primary genre | MGD (Genre), Kaggle (style_label), PMEmo (genre) |
| `sub_genre` | string | Sub-genre or form | — (gap for most) |
| `folk_song_type` | string | Folk song type (shan'ge/haozi/xiaodiao/wu'ge/yu'ge/tian'ge) | MGD (Genre 9 categories) |
| `shengqiang` | string | Beijing Opera melodic mode (xipi/erhuang) | Jingju Arias |
| `theme` | string | Thematic category | Kaggle (theme_label: Love/Epic/Folk tale/Celebration) |
| `arrangement_role` | string | Musical role in arrangement | POP909 (MELODY/BRIDGE/PIANO) |

## Instrumentation

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `instrument` | string | Primary instrument name (Chinese or English) | CTIS (cname), ChMusic, GZ_IsoTech, Guzheng_Tech99, Kaggle |
| `instrument_code` | string | Standardized instrument code | CTIS (label codes: C/D/L/T prefixes) |
| `instrument_pinyin` | string | Pinyin romanization | CTIS (pinyin) |
| `bayin_family` | string | Traditional bayin classification (silk/bamboo/metal/stone/earth/leather/gourd/wood) | Derived from instrument |
| `ensemble_type` | string | Solo/ensemble/orchestra | — (inferred) |
| `instrument_count` | int | Number of instruments | CTIS (219), ChMusic (11), Kaggle (3) |

## Musical Properties

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `key` | string | Musical key (Western notation: C, D, E, etc.) | POP909 (key_audio.txt), MGD (Keys), Kaggle (pitch_key) |
| `key_transpose` | string | Key transposition position | MGD (Key_Transpose_Position) |
| `mode` | string | Chinese pentatonic mode (gong/shang/jue/zhi/yu) or Western (major/minor) | — (gap: needs inference) |
| `tempo_bpm` | float | Tempo in BPM | POP909 (MIDI tempo), Kaggle (tempo_bpm), MGD |
| `time_signature` | string | Time signature (e.g., "4/4", "3/4") | POP909 (num_beats_per_measure), MGD (Regular_TS), Guqin |
| `tuning` | string | Instrument tuning system | Guqin (定弦: 13 distinct tunings) |
| `pitch_range_low` | int | Lowest MIDI note | Anthology (38), Guzheng_Tech99 (38), M4Singer (35) |
| `pitch_range_high` | int | Highest MIDI note | Anthology (91), Guzheng_Tech99 (86), M4Singer (78) |
| `duration_seconds` | float | Duration in seconds | All audio datasets |

## Language

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `language` | string | Primary language | M4Singer (Mandarin), GTSinger (5 languages) |
| `lyrics_text` | string | Lyrics text (Chinese characters) | M4Singer (txt), Anthology (per-note) |
| `lyrics_format` | string | Lyrics format (LRC/TextGrid/per-note/plain) | PMEmo (LRC), M4Singer (TextGrid), Anthology (MusicXML) |
| `phonemes` | list[string] | Phoneme sequence (pinyin) | M4Singer (phs), Jingju Phoneme |

## Modalities Available (boolean flags)

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `has_audio` | bool | Audio files available | ChMusic, CTIS, GZ_IsoTech, Guzheng_Tech99, PMEmo, M4Singer, Jingju, FolkMusic |
| `has_midi` | bool | MIDI files available | POP909, Anthology, Guqin, M4Singer, Guzheng_Tech99 |
| `has_musicxml` | bool | MusicXML files available | Anthology, Guqin |
| `has_jianpu` | bool | Jianpu notation available | Anthology (source scanned images in anonymized subset) |
| `has_lyrics` | bool | Lyrics available | Anthology (partial), PMEmo, M4Singer |
| `has_score` | bool | Musical score annotations | GTSinger, M4Singer |
| `has_metadata_only` | bool | Only pre-computed features or metadata, no raw data | Kaggle |

## Audio Properties

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `audio_format` | string | File format (WAV/MP3/FLAC) | All audio datasets |
| `sample_rate` | int | Sample rate in Hz | ChMusic (44100), CTIS (44100/48000), M4Singer (44100/48000/96000) |
| `channels` | int | Number of audio channels | ChMusic (2), M4Singer (1), CTIS (1-2) |
| `bit_depth` | int | Audio bit depth | ChMusic (16), M4Singer (16) |

## Annotations

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `chord_labels` | string | Chord annotation format | POP909 (Harte notation, 930 labels) |
| `beat_annotations` | bool | Beat/downbeat timing available | POP909 (beat_audio.txt, beat_midi.txt) |
| `emotion_valence` | float | Valence score (0–1) | PMEmo (static + dynamic) |
| `emotion_arousal` | float | Arousal score (0–1) | PMEmo (static + dynamic) |
| `eda_signals` | bool | EDA physiological signals | PMEmo |
| `playing_technique` | string | Instrument playing technique label | GZ_IsoTech (8 classes), Guzheng_Tech99 (7 classes), ErhuPT |
| `singing_technique` | string | Singing technique label | GTSinger (5 groups) |
| `onset_time` | float | Note onset time (seconds) | Guzheng_Tech99, Jingju |
| `offset_time` | float | Note offset time (seconds) | Guzheng_Tech99 |
| `note_pitch` | int | MIDI note number | Guzheng_Tech99, M4Singer (notes) |
| `note_duration` | float | Note duration (seconds) | M4Singer (notes_dur) |
| `phoneme_duration` | float | Phoneme duration (seconds) | M4Singer (ph_dur) |
| `slur_flag` | int | Slur indicator (0/1) | M4Singer (is_slur) |
| `boundary_line` | bool | Line-level boundary annotation | Jingju Singing Audio |
| `boundary_syllable` | bool | Syllable-level boundary annotation | Jingju Singing Audio |
| `boundary_phoneme` | bool | Phoneme-level boundary annotation | Jingju Singing Audio, Jingju Phoneme |
| `pitch_contour` | bool | Continuous pitch contour data | Jingju Pitch Contour |
| `aria_segmentation` | bool | Aria-level segmentation | Jingju Arias |
| `metrical_pattern` | string | Jingju metrical pattern (banshi) | Jingju Lyrics |
| `overtone_marker` | bool | Guqin overtone (泛音) markers | Guqin |
| `mfcc_features` | list[float] | Pre-computed MFCC features | Kaggle (13 MFCCs × mean/std), PMEmo (OpenSMILE) |

## Provenance

| Field | Type | Description | Source datasets |
|-------|------|-------------|----------------|
| `source_dataset` | string | Dataset name | All |
| `source_url` | string | Original dataset URL | All |
| `paper_citation` | string | Associated paper reference | Most |
| `license` | string | License type | All |
| `access_status` | string | `open` \| `gated` \| `restricted` \| `blocked` | All |
| `download_date` | string | Date downloaded (ISO 8601) | All |
| `cell_provenance` | enum | Per-field: `source` \| `inferred` \| `missing` | Generated in Phase 4 |

## Dataset Coverage Summary

| Dataset | Items | Granularity | Modalities | Key unique labels |
|---------|-------|-------------|------------|-------------------|
| POP909 | 909 | song | MIDI, annotations | chord (930), key (24), beat, arrangement role |
| ChMusic | 55 | song | audio | instrument (11) |
| Guqin | 71 | song | MusicXML | tuning (13), score source (6), historical source (38) |
| Anthology | 8,658 | song | MIDI, MusicXML | province (10), lyrics (2,497 songs) |
| Anonymized Anthology | 335 | song | MIDI, MusicXML, JPG | Jiangsu II subset, scanned jianpu images |
| PMEmo | 794 | song | audio, features | emotion (V/A), EDA, lyrics (LRC), comments |
| M4Singer | 20,896 | segment | audio, MIDI, TextGrid | singer (20), voice type (4), phonemes (58) |
| CTIS | 4,956 | clip | audio, spectrogram | instrument class (219), Chinese name, pinyin |
| GZ_IsoTech | 2,824 | clip | audio, spectrogram | technique (8 classes) |
| Guzheng_Tech99 | 15,838 | note | audio, features | technique (7), onset/offset, pitch |
| MGD | 31,761 | song | metadata (Excel) | province (31), genre (9), key |
| Jingju Singing Audio | ~120+ | song/aria | audio, TextGrid | role type, boundaries (line/syllable/phoneme) |
| Jingju Phoneme | varies | segment | audio, annotations | phoneme labels, role type |
| Jingju Pitch Contour | varies | segment | pitch data | pitch contour |
| Jingju Arias | 34 | aria | TextGrid | role type (5), shengqiang (2), tone-melody |
| Jingju Lyrics | varies | document | text | metrical patterns, linguistic features |
| Kaggle Folk Music | 2,374 | song | features (CSV) | region (4), instrument (3), style (3), theme (4) |
| FolkMusic/Zenodo | TBD | clip | audio | instrument (15) |
| GTSinger | TBD | segment | audio, score | language (5), technique (5) |
| CCOM-HuQin | TBD | segment | audio | instrument (huqin family) |
| ErhuPT | TBD | clip | audio | playing technique |
| CNPM | TBD | song | audio | pentatonic mode |
| ACE-OpenCpop | TBD | segment | audio | phoneme, note |

## Notes

1. **Mixed granularity**: POP909/Anthology/MGD are song-level; M4Singer is segment-level; Guzheng_Tech99 is note-level; CTIS/GZ_IsoTech are clip-level. The unified table handles this via the `granularity` field — different datasets contribute at different levels.

2. **Chinese mode gap**: Almost no dataset provides ground-truth Chinese pentatonic mode labels (gong/shang/jue/zhi/yu). MGD has `Keys` and `Key_Transpose_Position` which may encode mode info. CNPM is specifically about pentatonic modes but needs inspection. This is a critical gap for Phase 5.

3. **Temporal gap**: No dataset provides explicit year/era metadata except implicitly through artist (POP909) or historical source references (Guqin).

4. **Composer gap**: Only Guqin and POP909 have anything close to composer info (Guqin has performer/arranger; POP909 has artist). Most datasets lack songwriter attribution.

5. **Emotion labels**: Only PMEmo has emotion annotations, and its content is predominantly Western music. Chinese-music-specific emotion labels are absent.

6. **Singing/playing technique annotations**: Well-covered for Guzheng (GZ_IsoTech + Guzheng_Tech99), Erhu (ErhuPT), and singing (M4Singer, GTSinger). Other instruments lack technique labels.

7. **Geographic coverage**: MGD covers 31 provinces (most comprehensive). Anthology covers 10 provinces. Most other datasets don't specify region. Xinjiang coverage through XFID is gated.
