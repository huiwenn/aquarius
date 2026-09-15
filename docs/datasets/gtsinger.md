# GTSinger

## Source
- URL: https://huggingface.co/datasets/GTSinger/GTSinger
- Paper: NeurIPS 2024 Spotlight paper (arXiv:2409.13832)
- License: Custom (requires acceptance of terms on HuggingFace)
- Access method: HuggingFace (`GTSinger/GTSinger`)
- Status: downloaded (Chinese subset only)

## Paper & Description Insights
GTSinger is a large global, multi-technique, high-quality singing corpus with realistic music scores, designed for all singing tasks. Accepted as NeurIPS 2024 Spotlight. Full dataset ~54.2 GB across 9 languages.

Covers nine languages: Chinese, English, French, German, Italian, Japanese, Korean, Russian, Spanish. Five singing technique categories annotated: Breathy, Glissando, Mixed Voice and Falsetto, Pharyngeal, Vibrato. Each technique directory contains three parallel groups per song: the technique-specific group, a control group (normal singing), and a paired speech group.

Notable for multi-language and multi-technique coverage -- bridges Chinese singing with global context. From Zhejiang University.

## Content & Taxonomy Analysis
- Time period: Contemporary (C-pop repertoire)
- Region: Multi-national (9 languages); Chinese subset has 2 singers
- Genre/form: Singing voice (various techniques) + paired speech
- Instrumentation: Vocal only (2 Chinese singers: ZH-Alto-1, ZH-Tenor-1)
- Musical system: Various (multi-language songs)
- Language: Chinese, English, French, German, Italian, Japanese, Korean, Russian, Spanish
- Modalities: Audio (WAV), phoneme/word alignment (JSON + Praat TextGrid), music scores (MusicXML)
- Labels: singing technique (5 categories x 3 groups each: technique, control, paired speech), language, word-level and phoneme-level timing
- Notable: Multi-language, multi-technique; 54.2 GB full / ~10.7 GB Chinese subset

## Download Log
- Date: 2026-09-15
- Script: `src/downloaders/gtsinger_download.py`
- Method: `huggingface_hub.snapshot_download()` with `allow_patterns=["Chinese/*", "processed/Chinese/*", "README.md", "dataset_license.md"]`
- Downloaded: Chinese subset only (~10.7 GB)
- Skipped (non-Chinese, ~43.5 GB): English/, French/, German/, Italian/, Japanese/, Korean/, Russian/, Spanish/, processed/All/, processed/{English,French,German,Italian,Japanese,Korean,Russian,Spanish}/
- Output: `data/raw/gtsinger/`

### What was downloaded
- `Chinese/ZH-Alto-1/` -- female alto singer, 5 technique directories
- `Chinese/ZH-Tenor-1/` -- male tenor singer, 5 technique directories
- `processed/Chinese/metadata.json` (~39.5 MB) -- segment-level metadata
- `processed/Chinese/phone_set.json` -- phoneme inventory
- `processed/Chinese/spker_set.json` -- speaker set
- `README.md`, `dataset_license.md`

## Inspection Results

### Dataset Structure
```
Chinese/
  ZH-Alto-1/                    # Female alto singer
  ZH-Tenor-1/                   # Male tenor singer
    Breathy/                    # 20 songs per singer
    Glissando/                  # 20 songs per singer
    Mixed_Voice_and_Falsetto/   # 20 songs per singer
    Pharyngeal/                 # 20 songs per singer
    Vibrato/                    # 20 songs per singer
      <song_name>/              # Chinese song title (e.g. "成都", "江南")
        <Technique>_Group/      # Technique-specific recording
        Control_Group/          # Normal singing (same song)
        Paired_Speech_Group/    # Spoken version (same lyrics)
          XXXX.wav              # Audio segment
          XXXX.json             # Phoneme/word alignment
          XXXX.TextGrid         # Praat TextGrid (9 tiers)
          XXXX.musicxml         # Music score
```

### File Counts (expected from HF repo scan)
- Total files: ~37,703 (Chinese raw) + 3 (processed metadata)
- .wav files: ~10,188
- .json files: ~10,188
- .TextGrid files: ~10,188
- .musicxml files: ~7,139

### Audio Properties
- Format: WAV, mono, 24-bit PCM
- Sample rate: 48,000 Hz (uniform across all files)
- Segment duration range: 1.74s -- 13.63s
- Mean segment duration: ~6.55s (median ~6.74s)
- Estimated total duration: ~18.5 hours (10,188 segments x 6.55s avg)

### Song Repertoire
- 5 techniques x 20 songs per technique per singer = 100 song-technique pairs per singer
- 2 singers = 200 song-technique pairs total
- Song titles are Chinese C-pop songs (e.g. "成都" Chengdu, "江南" Jiangnan, "说谎" Lying, "知足" Contentment)
- Each song recorded in 3 groups (technique, control, paired speech) with 7--24 segments per group (avg ~12)

### Annotation Structure

#### JSON (per segment)
Array of word-level entries, each with:
- `word`: Chinese character or special token (`<SP>` = silence pause, `<AP>` = aspiration pause)
- `start_time`, `end_time`: word-level timing (seconds)
- `ph`: list of phonemes (pinyin initials/finals)
- `ph_start`, `ph_end`: per-phoneme timing (seconds)
- Phoneme inventory: 53 regular pinyin phonemes + 2 special tokens (`<SP>`, `<AP>`) = 55 total

#### TextGrid (9 tiers)
1. `word` -- word-level alignment (Chinese characters + `<SP>`/`<AP>`)
2. `phone` -- phoneme-level alignment (pinyin)
3. `mix` -- mixed voice annotation
4. `falsetto` -- falsetto annotation
5. `breathy` -- breathy voice annotation
6. `pharyngeal` -- pharyngeal voice annotation
7. `vibrato` -- vibrato annotation
8. `glissando` -- glissando annotation
9. `global` -- global technique label

#### MusicXML
- Standard MusicXML 3.0 format
- Contains melodic score with key, time signature, note pitches and durations
- Encoded with HwMusicxml software (encoding date 2024-05-07)

### Processed Metadata (processed/Chinese/)
- `metadata.json` (~39.5 MB): segment-level metadata for all Chinese segments, includes wav paths (need to update to local absolute paths)
- `phone_set.json`: phoneme set definition
- `spker_set.json`: speaker set (ZH-Alto-1, ZH-Tenor-1)

## Schema Mapping
| GTSinger field | Aquarius concept | Notes |
|---|---|---|
| Singer ID (ZH-Alto-1, ZH-Tenor-1) | performer_id | 2 anonymous Chinese singers |
| Voice type (Alto, Tenor) | voice_type | From singer ID prefix |
| Song name (Chinese) | work_title | C-pop songs in Chinese characters |
| Technique directory | technique_label | 5 categories: Breathy, Glissando, Mixed_Voice_and_Falsetto, Pharyngeal, Vibrato |
| Group type | recording_condition | 3 groups: technique, control, paired_speech |
| WAV audio | audio | Mono, 24-bit, 48 kHz |
| JSON word entries | word_alignment | Word-level timestamps |
| JSON ph entries | phoneme_alignment | Phoneme-level timestamps with pinyin |
| TextGrid tiers 1-2 | word_phoneme_alignment | Praat format word + phoneme tiers |
| TextGrid tiers 3-9 | technique_annotation | Per-frame technique labels across 7 tiers |
| MusicXML | musical_score | Melodic score with pitch, rhythm, key |
| processed/metadata.json | segment_metadata | Pre-processed segment-level metadata |

## Gap Assessment
- **24-bit audio**: Unusual bit depth (most datasets use 16-bit). May need conversion for compatibility with some processing pipelines.
- **Chinese-only subset**: We download only 2 of ~20+ singers. Cross-language analysis would require the full dataset (~54 GB).
- **Song overlap across techniques**: The same 20 songs appear across all 5 techniques per singer, enabling paired technique comparison but limiting song diversity.
- **No explicit tempo/BPM**: MusicXML contains note durations but no explicit tempo marking; tempo must be derived.
- **No pitch (f0) contours**: Raw audio only; f0 extraction needed for pitch analysis.
- **Two singers only**: Chinese subset has only 1 alto + 1 tenor. Limited singer diversity for voice-type studies.
- **Anonymous singers**: No demographic or vocal training information.
- **Metadata path update needed**: `processed/Chinese/metadata.json` contains relative wav paths that must be updated to local absolute paths before use.
- **Strong for Aquarius**: Rich technique-annotated singing voice data with paired speech, word/phoneme alignment, and music scores. Unique multi-technique design enables systematic study of singing techniques in Chinese. The 9-tier TextGrid provides frame-level technique annotations rarely found in other datasets.
