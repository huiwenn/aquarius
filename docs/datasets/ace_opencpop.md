# ACE-OpenCpop / ACE-KiSing

## Source
- URL: https://www.isca-archive.org/interspeech_2024/shi24_interspeech.pdf
- Paper: "Singing Voice Data Scaling-up: An Introduction to ACE-Opencpop and ACE-KiSing" (Interspeech 2024) — https://arxiv.org/abs/2401.17619
- License: CC-BY-NC-4.0
- Access method: ESPnet-Muskits; HuggingFace (https://huggingface.co/datasets/espnet/ace-opencpop-segments)
- Status: downloaded + inspected
- Derived from: Opencpop (see `opencpop.md`) and KiSing (see `kising.md`)

## Paper & Description Insights
ACE-Opencpop and ACE-KiSing are data-augmented extensions of Opencpop and KiSing, created using an existing SVS synthesizer for data augmentation with detailed manual tuning. ACE-Opencpop has vocal characteristics and styles from 30 singers, presented at song level with segmentation aligning to original Opencpop configuration.

ACE-KiSing extends KiSing with eight additional songs by Kiki Zhang, including four English songs (making it bilingual). Both serve as benchmarks for SVS and enhance performance on other datasets as supplementary training data.

Available via ESPnet-Muskits with pre-trained models and training recipes.

## Content & Taxonomy Analysis
- Time period: Contemporary
- Region: Mainland China
- Genre/form: C-pop / Mandopop (synthesized augmentation of real recordings)
- Instrumentation: Vocal only (30 singer voices in ACE-Opencpop; augmented)
- Musical system: Western diatonic
- Language: Mandarin Chinese (+ English in ACE-KiSing)
- Modalities: Audio (singing), music scores, segmentation annotations
- Labels: singer identity, segmentation, music score alignment
- Note: Synthetic augmentation — not all recordings are from real singers

## Download Log
- 2026-09-15: Downloaded via `load_dataset("espnet/ace-opencpop-segments")` + `save_to_disk()`
- HF repo: `espnet/ace-opencpop-segments`
- On-disk size: 43 GB at `data/raw/ace_opencpop/`
- Note: Download encountered HTTP 429 rate limiting (4 retries with 165-194s waits) but completed successfully (89 parquet data files)

## Inspection Results
- **Total segments**: 105,960 (train: 100,510, validation: 50, test: 5,400)
- **14 columns**: audio, segment_id, transcription, singer, label, tempo, note_midi, note_phns, note_lyrics, note_start_times, note_end_times, phn, phn_start_time, phn_end_time
- **Singers**: 30 (integer IDs 1-30)
- **Tempo**: range 40-128 BPM, mean 74.6 BPM
- **Audio**: stored as Audio feature (sampling_rate=None, decoded on access)
- **Annotations per segment**:
  - `transcription`: space-separated phoneme sequence (Mandarin initials/finals + SP/AP markers)
  - `label`: full phoneme alignment with start/end timestamps (e.g., "0.000 0.032 g 0.032 0.253 an ...")
  - `note_midi`: list of MIDI pitch values per note (0.0 = silence/rest)
  - `note_phns`: phoneme groupings per note (initial_final format, e.g., "g_an", "sh_ou")
  - `note_lyrics`: same as note_phns (pinyin syllable per note)
  - `note_start_times` / `note_end_times`: note-level timing in seconds
  - `phn`: individual phoneme sequence (list of strings)
  - `phn_start_time` / `phn_end_time`: phoneme-level timing in seconds
- **Special tokens**: SP (short pause), AP (aspiration pause/breath)
- **Phoneme system**: Mandarin pinyin initials and finals (b, p, m, f, d, t, n, l, g, k, h, j, q, x, zh, ch, sh, r, z, c, s, y, w + vowels/finals: a, o, e, i, u, v, ai, ei, ao, ou, an, en, ang, eng, ong, ian, iao, ie, iu, uan, uang, ue/ve, un, in, ing, etc.)
- **Unique label patterns**: 3,352 distinct phoneme alignment sequences

## Schema Mapping

| ACE-OpenCpop field | Unified schema field | Notes |
|---|---|---|
| Singer index (0-29) | `original_id` | "singer_{id}" |
| Singer index | `singer_id` | String of singer index |
| (dataset-level) | `has_audio` = true | WAV segments |
| (dataset-level) | `has_midi` = true | Note-level alignment |
| (dataset-level) | `has_lyrics` = true | Phoneme-aligned lyrics |
| (dataset-level) | `genre` = "C-pop" | Mandarin pop singing |
| (dataset-level) | `language` = "Mandarin" | |
| (dataset-level) | `granularity` = "collection" | One entry per singer (30 singers) |

## Gap Assessment
