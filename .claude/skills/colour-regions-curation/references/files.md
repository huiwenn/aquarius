# Source-of-truth files and formats

Everything under `data/` is gitignored. Get it from the team drive, never from a public location: the audio is third-party.

## Map: which file holds which decision

| Decision | File | Format |
|---|---|---|
| Which recordings exist (round ≥ 2) | `data/regions_v<N>/candidates_clean/<region>.json`, then `manifest.csv` (built by the downloader) | below |
| Round-1 recordings and their re-curation | `data/regions_audio/manifest.csv`, `data/regions_curated/v1_provenance.csv` | |
| Round-1 label and content reviews | `data/regions_curated/v1_label_review.csv` (`label_status` exclude/minor), `v1_content_review.csv` (exclude) | |
| Heritage-bearer check (tier A1) | `data/regions_curated/ihchina_items.csv` (`src/colour_regions/check_inheritors.py`) | |
| Region moves | `data/regions_curated/region_overrides.csv` | `item_id,region,reason` |
| Musical Map of China fields and region rules | `src/colour_regions/rhymoi.py` (`ETHNIC_REGION`, `PRECEDENT`) | code |
| Song labels | `data/colour_regions/song_labels/labels_<Region>.csv` | protocol columns |
| Song-label corrections | `data/colour_regions/song_labels/adjudication.csv` | `song_id,field,value,decision,reason`; `decision` = `override` (set field = value) or `accept` (review row resolved, no change) |
| Song ids | `data/colour_regions/song_labels/song_ids.csv` | appended by `song_table.py` only |
| Anthology match verdicts | `data/colour_regions/anthology_overlap_manual.csv` | `song_id,anthology_item_id,verdict,reason` (`match` / `uncertain` / `reject`) |
| Region definitions | `src/colour_regions/regions.py` | ask the owner before changing |
| Dataset card | `docs/hf_dataset_card.md` | `{N_REC}`-style placeholders are filled by `build_hf.py` |

## Candidate list (one JSON per region and round)

`data/regions_v<N>/candidates_clean/<region>.json`:

```json
{"region": "湘", "candidates": [
  {"platform": "bili", "id": "BV1…", "url": "https://www.bilibili.com/video/BV1…", "title": "…", "channel": "…",
   "channel_id": 123, "duration_s": 245, "song_name": "马桑树儿搭灯台", "province": "湖南", "county_or_area": "桑植",
   "ethnic_group": "汉", "genre": "山歌", "performance_type": "原生态", "singer": "…", "singer_inheritor": "",
   "provenance_tier": "A", "provenance_evidence": "title: 桑植民歌传承人 …; description: …",
   "dating_flag": "traditional", "source_query": "桑植民歌 原生态", "note": "", "curator": "your name"}
]}
```

Notes on the fields:
- `platform`: `bili`, `yt` or `europeana`.
- `region` and the file name: the Chinese region name.
- The order of `candidates` is the rank.
- `provenance_tier`: `A`, `B` or `C`. A1 and A2 are decided by the build.

## Item rules (from `docs/collection_v2.md`)

- **Length and content:** 40 s to 10 min; one song per video (no compilations); a solo or lead voice clearly audible; at most 3 instrumental items per region.
- **Place:** the singing is inside the region; label border cases by the singer's locality.
- **Repetition:** at most 2 recordings of one song per region; at most 4 recordings per channel per region (institutional archives excepted, with the owner's OK).
- **Mix:** at least 70% 原生态 / field / tradition-bearer and at most 30% 民族唱法; no choirs, pop or EDM arrangements, karaoke or tutorials.
- **Composed songs:** set `dating_flag: composed` and give the composer in `note`. When unsure, use `check`.
- **Provenance:** at least 50% of a region's new items should be tier A or B.
- **IDs:** every ID comes from a logged search hit.

## Where things are on disk (per round N ≥ 2)

```
data/regions_v<N>/
  candidates_clean/<region>.json   your curated list
  logs/search_<platform>.jsonl     every search (audit trail)
  audio/<region>/<id>.<ext>        downloads (never shared)
  manifest.csv                     downloader output (status ok / failed)
  speech_screen/                   speech screen
  transcription/                   vocals, accomp, midi/<model>/, musicxml/<model>/, f0_rmvpe, f0_pesto, dataset_index.csv
```
