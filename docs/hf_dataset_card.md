---
license: cc-by-nc-sa-4.0
language:
  - zh
pretty_name: "Colour Regions: Chinese folk song by colour region (色彩区)"
size_categories:
  - 1K<n<10K
task_categories:
  - audio-classification
tags:
  - music
  - folk-music
  - ethnomusicology
  - chinese-music
  - music-transcription
  - midi
  - musicxml
  - f0
configs:
  - config_name: recordings
    default: true
    data_files: data/recordings.parquet
  - config_name: song_labels
    data_files: data/song_labels.parquet
  - config_name: anthology_overlap
    data_files: data/anthology_overlap.parquet
  - config_name: scores
    data_files: data/scores.parquet
  - config_name: score_matches
    data_files: data/score_matches.parquet
  - config_name: fingerprints
    data_files: data/fingerprints.parquet
  - config_name: link_status
    data_files: data/link_status.parquet
---

# Colour Regions

Colour Regions is an open corpus of Chinese folk song for geographic and ethnomusicological research. It groups {N_REC} recordings ({HOURS} h) into the 15 colour regions (色彩区) of Chinese folk-song scholarship: 11 Han regions and 4 minority song areas.

**This dataset contains no audio.** Each recording is a link to its source ({N_YT} YouTube, {N_BILI} Bilibili and {N_EU} Europeana/CREM items). The dataset gives the curation metadata and the data derived from the audio: note transcriptions (MIDI and MusicXML) and pitch tracks (F0).

> Status: pre-release, private. Authors, citation and the accompanying paper (TISMIR, special collection "Open Music Data for Music Processing Research") will be added.

## What is in it

| Path | Content |
|---|---|
| `data/recordings.parquet` | One row per recording: link, region, place, ethnic group, song, genre, performance type, provenance, song labels, quality flags, and paths to the derived files. |
| `data/song_labels.parquet` | One row per song ({N_SONGS} songs): song class, genre, composer, lyricist, arranger, period of composition, with the evidence, sources and confidence of each label. |
| `data/anthology_overlap.parquet` | Songs of this corpus that are also printed in the *Anthology of Chinese Folk Songs* (《中国民间歌曲集成》, OMR edition), {N_OVERLAP} songs matched. |
| `data/scores.parquet`, `data/score_matches.parquet` | Anthology and Essen scores mapped to the same regions (statistics only), and title matches between recordings and scores. |
| `data/fingerprints.parquet` | Chromaprint fingerprints of the first 120 s, to check that a re-downloaded file is the same recording. |
| `data/link_status.parquet` | The latest check of whether each link still works. |
| `midi/primary/` | The primary transcription of each recording (vocal melody; for instrumental items, the main melody). |
| `midi/game/`, `midi/rosvot/` | Alternative transcriptions by single models, for comparison. |
| `musicxml/primary/` | The primary transcription as notation. The metre is nominal: free-rhythm songs (散板, 长调) get a beat grid they do not have. Use the MIDI for timing. |
| `f0/rmvpe/`, `f0/pesto/` | F0 of the separated voice, 10 ms hop, in Hz (0 = unvoiced). PESTO files also hold a confidence. |

All paths in `recordings.parquet` are relative to the dataset root, for example `midi/primary/Northwest_Plateau/<id>.mid`.

## How the data was made

1. **Collection.** Three rounds of curated web search:
   - Round 1: 600 YouTube recordings, 40 per region.
   - Round 2: 697 recordings from new channels, mainly Bilibili, with a channel cap and provenance rules.
   - Round 3: 358 recordings from the *Musical Map of China* series (中国音乐地图), whose descriptions name the singers and places.
   Every link comes from a logged search; none was written from memory.
2. **Region labels and provenance.** Each recording has a provenance tier:
   - `A1`: national heritage bearer;
   - `A2`: named singer with a stated county;
   - `B`: field or locality-attested recording;
   - `C`: region from title or genre only.
3. **Transcription.**
   - htdemucs separates the voice from the accompaniment.
   - GAME transcribes the voice: three runs, combined by note-level voting, with a 50 ms offset trim. ROSVOT is used where GAME misses sung material, and YourMT3+ on the full mix for instrumental items.
   - RMVPE and PESTO compute F0 on the separated voice.
4. **Song labels.** Research agents labelled each song from sources, following a written protocol. The labels were cross-validated against an earlier blind dating (94% agreement on the song class) and against the Anthology, and then checked by an independent verifier. A second, independent review covered every song. The column `song_label_check` says what that review found: `verified` (checked against a source), `reviewed` (consistent with all the evidence, no source read), `corrected` (changed after review) or `disputed` (an open question).

## Main columns of `recordings`

| Column | Meaning |
|---|---|
| `item_id`, `platform`, `url` | Source identifier and link |
| `region`, `region_en`, `region_type` | Colour region (Chinese, English), Han or minority |
| `region_curator` | The curator's region, where a later decision moved the recording |
| `province`, `county_or_area`, `lon`, `lat`, `geo_level` | Stated place and its location |
| `ethnic_group`, `song_name`, `song_key`, `genre`, `performance_type` | As stated by the source and the curators |
| `singer`, `singer_id` | Names are given only for national heritage bearers; `singer_id` is a pseudonymous ID |
| `provenance_tier`, `provenance_evidence` | Strength of the region attestation, and the evidence |
| `feature_flags` | List of semantic features, e.g. `series:musical_map_of_china`, `accompanied`, `instrument:马头琴`, `multiple_singers` |
| `song_class`, `song_genre`, `composer`, `composition_period`, … | Song labels (see `song_labels` for the evidence) |
| `subset` | `core` (default analysis subset, {N_CORE}), `folk_style_composed` (songs composed in a folk idiom, {N_FSC}), `excluded` (label errors, arrangements, composed songs, speech) |
| `group_id` | Connected component of "same channel" ∪ "same singer". Keep a group on one side of any train/test split. |
| `transcription_model`, `n_notes`, `vocal_db`, `game_rosvot_agreement` | Transcription quality indicators |
| `midi_*`, `musicxml_primary`, `f0_*` | Paths to the derived files |

## Getting the audio

The audio is third-party and is not redistributed. Download each recording from its `url` under the platform's terms (for example with `yt-dlp`), then check it against `fingerprints` (duration within ±2 s, Chromaprint bit error rate ≤ 0.25). Some links will stop working over time: see `link_status`. The derived data stays usable without the audio.

## Evaluation

Recordings from one channel or one singer share recording conditions and voice. A model can learn those instead of the region. Use `group_id` to keep each group on one side of a split, and keep songs (`song_key`) disjoint. The *Musical Map of China* series (flag `series:musical_map_of_china`, 539 recordings) forms most of the largest group; it spans all 15 regions, so its channel is not a shortcut to the region label, but report results with and without it.

## Limitations

- **Labels:** most song labels are low confidence: anonymous traditional songs labelled from the genre and the title. Region labels of tier `C` items rest on the title or genre only.
- **Balance:** regions are unequal in size (73–202 recordings). The *Musical Map of China* series adds many minority-region items from one studio production.
- **Transcriptions:** they are automatic. On held-out benchmarks GAME reaches about 0.59 COnP, and in-domain checks show clear agreement with Anthology scores of the same song, but individual notes are often wrong, especially in heterophonic, ornamented or free-rhythm singing.
- **Platform bias:** the sources are online videos, which over-represent staged and broadcast performances.

## Licence and removal

The metadata and derived data are released under **CC BY-NC-SA 4.0**. Data derived from the Anthology of Chinese Folk Songs OMR edition (CC BY-NC-SA 4.0) keeps that licence. Video titles are third-party text, kept as published. Personal names appear only for national heritage bearers, a public role.

To ask for an item to be removed, open a discussion on this page.
