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

| Dataset | Items in master table | Granularity | Modalities | Key unique labels |
|---------|----------------------|-------------|------------|-------------------|
| POP909 | 909 | song | MIDI, annotations | chord (930), key (24), beat, arrangement role |
| ChMusic | 55 | song | audio | instrument (11) |
| Guqin | 71 | song | MusicXML | tuning (13), score source (6), historical source (38) |
| Anthology | 8,654 | song | MIDI, MusicXML | province (10), lyrics (2,497 songs) |
| PMEmo | 794 | song | audio, features | emotion (V/A), EDA, lyrics (LRC), comments |
| M4Singer | 699 | song (aggregated) | audio, MIDI, TextGrid | singer (20), voice type (4), phonemes (58) |
| CTIS | 219 | clip | audio, spectrogram | instrument class (219), Chinese name, pinyin |
| GZ_IsoTech | 8 | clip | audio, spectrogram | technique (8 classes) |
| MGD | 31,761 | song | metadata (Excel) | province (31), genre (9), key |
| Kaggle Folk Music | 2,374 | song | features (CSV) | region (4), instrument (3), style (3), theme (4) |
| Jingju Singing Audio | 67 | song/aria | audio, TextGrid | role type (2), boundaries (line/syllable/phoneme) |
| CCOM-HuQin | 159 | song + clip | audio, MusicXML, CSV | instrument (10 huqin), technique (13), region, composer, year |
| CNPM | 287 | clip | audio, mel | pentatonic mode (5 modes × 12 tonics × 6 scale systems) |
| ErhuPT | 11 | clip | audio, mel | playing technique (11 classes) |
| ACE-OpenCpop | 30 | collection | audio, MIDI, lyrics | singer (30), phoneme alignment, note alignment |
| GTSinger | 229 | song | audio, MusicXML, TextGrid, JSON | singer (2), technique (8 groups), phoneme/word alignment |
| Jingju Phoneme | — | segment | audio, annotations | phoneme labels, role type (not in master table yet) |
| Jingju Pitch Contour | — | segment | pitch data | pitch contour (not in master table yet) |
| Jingju Arias | — | aria | TextGrid | role type (5), shengqiang (2) (not in master table yet) |
| Jingju Lyrics | — | document | text | metrical patterns (not in master table yet) |
| Anonymized Anthology | — | song | MIDI, MusicXML, JPG | subset of Anthology (not separate in master table) |
| Guzheng_Tech99 | — | note | audio, features | technique (7) (not in master table yet) |
| FolkMusic/Zenodo | — | clip | audio | instrument (15) (not in master table yet) |

## Notes

1. **Master table**: 46,327 items across 16 datasets in `data/unified/master_table.parquet`. Three granularity levels: song (45,670), clip (627), collection (30). Additional datasets (Jingju sub-datasets, Guzheng_Tech99, FolkMusic/Zenodo) are downloaded but not yet in the master table — loaders can be added to `src/unify.py`.

2. **Chinese mode**: CNPM provides 287 ground-truth pentatonic mode labels covering all 5 modes (宫/商/角/徵/羽) × 12 tonics × 6 scale system variants (五声/六声+变宫/六声+清角/七声清乐/七声雅乐/七声燕乐). This is the only dataset with explicit mode labels and can serve as training data for mode classifiers.

3. **Temporal gap**: CCOM-HuQin provides year metadata for 57 excerpts (1917–2017). No other dataset provides explicit year/era except implicitly through artist (POP909) or historical source references (Guqin).

4. **Composer coverage**: CCOM-HuQin provides composer names for 57 excerpts. Guqin has arranger/transcriber info. Most datasets lack songwriter attribution.

5. **Technique annotations**: Well-covered across multiple instruments — Guzheng (GZ_IsoTech 8 classes, Guzheng_Tech99 7 classes), Erhu (ErhuPT 11 classes), HuQin family (CCOM-HuQin 13 classes), singing (GTSinger 8 groups, M4Singer). Other instruments lack technique labels.

6. **Geographic coverage**: MGD covers 31 provinces. Anthology covers 10 provinces. CCOM-HuQin adds region for 57 excerpts (Guangdong, Shanxi, Shandong, Henan, etc.). XFID (Xinjiang folk instruments) remains gated.

7. **Emotion labels**: Only PMEmo has emotion annotations, and its content is predominantly Western music. No Chinese-music emotion dataset exists.

8. **Licensing and redistribution**: Not all datasets can be redistributed as part of a public Aquarius release. CCMusic ecosystem datasets (CTIS, GZ_IsoTech, CNPM, ErhuPT, GuzhengTech99) carry an institutional restriction: "This database can only be used by the applicant and members of the applicant's department or research institution." M4Singer and GTSinger also prohibit redistribution. Aquarius distributes unified metadata and tooling; users must obtain restricted-license data independently. See `docs/license_audit.md` for full details.
