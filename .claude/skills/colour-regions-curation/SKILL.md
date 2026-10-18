---
name: colour-regions-curation
description: How to add to and maintain the Colour Regions (色彩区) folk-song corpus in this repo — adding new recordings (a new collection round), researching and labelling songs (composer, lyricist, arranger, period of composition, song class such as folk / court / work song, genre), fixing a label or a region, excluding a recording, and rebuilding and publishing the release (metadata/ on GitHub, the Hugging Face dataset). Explains every column and its allowed values, and which file is the source of truth for each kind of change. Use this whenever someone wants to add songs or rows, label or research songs, change any value in recordings.csv / song_labels.csv / metadata/, ask what a column means or what values it takes, or rebuild or upload the dataset — even if they only say "add these videos", "who wrote this song", "this song is in the wrong region" or "what does provenance_tier mean".
---

# Colour Regions: adding and labelling data

This repo builds a link-based corpus of Chinese folk song. Each recording is a link (YouTube, Bilibili, Europeana) plus curation metadata, song labels and derived data (MIDI/MusicXML transcriptions, F0). **The audio is never committed or shared.** Read `CLAUDE.md` for the project rules. This skill covers the day-to-day workflows.

## The two ideas to understand first

**1. Recordings vs songs.** A *recording* is one video, keyed by `item_id`. A *song* is a tune within a region, keyed by (`region`, `song_key`) and identified by a stable `song_id`. One song can have several recordings. Song labels (class, genre, composer, period) live at the song level and are copied to every recording of that song.

**2. Never edit generated tables.** `data/colour_regions/recordings.csv`, `song_labels.csv`, `metadata/*.csv` and `data/hf_release/` are **rebuilt by scripts**, so hand edits are overwritten. Every change goes into a *source-of-truth* file, followed by a rebuild. `references/files.md` maps each kind of change to its file. Quick map:

| You want to … | Edit | Then run |
|---|---|---|
| Add recordings | a new round: `data/regions_v<N>/candidates_clean/<region>.json` | download → `run_round.sh N` → label new songs |
| Label new songs / fix a song label | `data/colour_regions/song_labels/labels_<Region>.csv` (new rows) or `adjudication.csv` (corrections) | `song_labels_check.py` |
| Move a recording to another region | `data/regions_curated/region_overrides.csv` | rebuild |
| Exclude a recording from core | its manifest `dating_flag` / `note`, or the review CSVs | rebuild |
| Accept/reject an Anthology match | `data/colour_regions/anthology_overlap_manual.csv` | `anthology_overlap.py --verdicts-only` |

Rebuild = the four commands under "Rebuild and check" below.

## Workflow A: add recordings (a new collection round)

New recordings always go into a **new round** folder, `data/regions_v<N>/` (N = next number). The scripts discover rounds automatically (`src/colour_regions/rounds.py`), so no code changes are needed.

1. **Find candidates by logged search only.** Never type a video ID from memory: earlier LLM-written link lists were partly fabricated.
   ```
   AQ_COLLECTION=data/regions_v4 python src/secaiqu/v2/search.py --region 湘 --platform bili -n 15 "桑植民歌 原生态"
   ```
   Every query and hit is appended to `data/regions_v4/logs/search_<platform>.jsonl`.
2. **Curate** a ranked list per region in `data/regions_v4/candidates_clean/<region>.json`. The format and the item rules (duration, one song per video, provenance tiers, channel cap) are in `references/files.md` §Candidate list. Keep the builder script in the repo (`src/<round>/build_*.py`), not in a scratch folder.
3. **Download, slowly, one downloader at a time** (check with `pgrep -fl download`). Pacing is built in: 45–90 s per YouTube item, 8–20 s per Bilibili item.
   ```
   AQ_COLLECTION=data/regions_v4 python src/secaiqu/v2/download.py
   ```
   The downloader uses your Firefox cookies. Fast runs trigger a YouTube bot wall that lasts hours.
4. **Process:** run speech screen, separation, transcription, F0, index and release tables in one command, from an arm64 shell. GPU jobs must not start from the x86 `py312`.
   ```
   nohup arch -arm64 /bin/bash src/transcription/run_round.sh 4 > /dev/null 2>&1 &
   grep "^== " data/regions_v4/logs/run_round.log      # progress; grep -c Traceback for errors
   ```
5. **Label the new songs** (Workflow B), then rebuild and check.

Adding a few items to an *existing* round is possible (append to its candidate JSON, rerun the downloader and `run_round.sh`). Prefer a new round, so each round's collection rules stay documented.

## Workflow B: research and label songs

1. `python src/colour_regions/song_table.py` adds the new songs to `data/colour_regions/song_labels/input_<Region>.csv` with the evidence we already hold: curator fields, video titles, Anthology title matches, composer lines from source descriptions. It assigns each new song a permanent `song_id` (registry `song_ids.csv`).
2. For each input row without a label, add one row to `labels_<Region>.csv` with the protocol columns. **Read `references/song_research.md` before you start**: it covers how to search, which sources count, the decision rules (folk songs have no composer; a collection year doesn't date a traditional song; …) and the vocabulary.
3. `python src/colour_regions/song_labels_check.py` validates the vocabulary and cross-checks against the blind round-1 dating, the Anthology and the curator flags. Every flagged row lands in `song_labels/review.csv`, and you resolve it in `adjudication.csv`.
4. Rebuild. The labels then appear on every recording of the song.

The golden rule: **never invent a name or a year.** A name or year needs a source you actually read. Your own knowledge alone may set the class, genre and period at `low` confidence, and `sources` must then say `knowledge`.

## Workflow C: corrections

- **Wrong song label:** add a row `song_id,field,value,override,<reason with source>` to `song_labels/adjudication.csv`. Never edit the labeller's row in place: the adjudication file is the audit trail.
- **Wrong region:** add `item_id,region,reason` to `data/regions_curated/region_overrides.csv`. The original stays in `region_curator`. Files stay in the curator's folder; the scripts handle that.
- **Bad recording** (not folk, a choir, speech, a wrong song): for round ≥ 2, set `dating_flag` to `composed` or add a note in the round's manifest. For round 1, use `data/regions_curated/v1_label_review.csv` / `v1_content_review.csv`. The `core` / `subset` columns follow on rebuild.
- **Removal request** (rights holder or performer): drop the item from its round's manifest and the release, and record it in the worklog.

## Rebuild and check

```
python src/colour_regions/build_release.py      # data/colour_regions/*.csv
python src/colour_regions/export_metadata.py    # metadata/ (GitHub release)
python src/colour_regions/consolidate.py        # data/colour_regions/corpus/ (symlink view)
python .claude/skills/colour-regions-curation/scripts/check_release.py   # must print OK
```
Use the x86 `py312` env for these: `/usr/local/Caskroom/miniforge/base/envs/py312/bin/python`.

`check_release.py` checks vocabularies, period-versus-year consistency, the "no composer on folk songs" rule, song-id integrity, that `metadata/` is up to date, and that **no private singer names** reach the release. Fix every ERROR before committing.

## Publishing

- **GitHub** (code + `metadata/`): commit only when the project owner asks. Never commit audio, `data/`, or `data/session_logs/`.
- **Hugging Face** (`sophiaphia/colour-regions`, private): `python src/colour_regions/build_hf.py`, then `hf upload sophiaphia/colour-regions data/hf_release . --type dataset`. The card comes from `docs/hf_dataset_card.md`, so edit it there.
- Add a dated entry to `docs/worklog.md` describing what changed.

## Column reference

Every column, its values and where it comes from: `references/columns.md`. For the meaning of a single column, read only that file.

## Guardrails (why they exist)

- **Privacy:** names are released only for national heritage bearers (tier A1). Everyone else gets a pseudonymous `singer_id`. Evidence text is redacted automatically by `src/colour_regions/privacy.py`, so put singer names only in the `singer` fields, where the redaction can find them.
- **Evidence rule:** don't write conclusions about transcription "friction", notation or cultural contact from automatic data. Those wait for the human notation study.
- **Methodology:** ask the project owner before changing a rule (tiers, core definition, vocabularies, region assignment).
