# CLAUDE.md: Aquarius / Colour Regions

This repo builds **Colour Regions** (色彩区), an open corpus of Chinese folk song for geographic and ethnomusicological analysis. Its dataset paper targets the TISMIR special collection "Open Music Data for Music Processing Research" (deadline 2026-12-01).

- **Corpus:** 1,297 linked recordings over 15 colour regions, from two collection rounds.
- **Scores:** the Anthology of Chinese Folk Songs (8,654 OMR scores) and Essen scores, mapped to the same regions.
- **Derived data:** curation metadata, provenance tiers, F0 tracks and MIDI/MusicXML transcriptions.
- **Example study:** region classification.

The repo began as a unified table of 23 Chinese music datasets (`AquariusDatasets.md`, `docs/plan.md`, `src/downloaders/`, `src/inspectors/`, `src/unify.py`). That work is now related-work context only.

## Start here

1. Read `docs/worklog.md` first. It is the handoff log, with current status, the latest session and next steps; read its newest dated section. Add a dated entry at the end of every session.
2. Read the topic docs. Each one is a running log, so append to it rather than rewriting it.

| Doc | Topic |
|---|---|
| `docs/collection_v2.md` | Round 2 collection rules, schema and logs |
| `docs/transcription.md` | Round 1 collection, model benchmark, transcription pipeline, audit |
| `docs/region_classification.md` | Example study; official numbers are in §22 (strict protocol) |
| `docs/critiques.md` | Reviewer-style critiques; the status table is in §4 |
| `docs/thesis_evidence_plan.md` | What must be done before any claims on friction, notation or interaction |
| `docs/annotation_guideline.md` | Guideline for the human notation study (draft) |
| `docs/research_report_secaiqu_measurable.md` | Literature report on 色彩区 musicology |

- **Paper:** in `../colour_regions_paper/` (LaTeX, outside this repo). `build.sh` compiles it and reports the word count. The limit is 8,000 words including references.
  - `THESIS.md` holds the thesis; keep it as the user wrote it.
  - `reviews/` holds the reviewer passes.

## Layout

| Path | Contents |
|---|---|
| `src/secaiqu/` | Round 2 search, download, audit and speech screen (`v2/`) |
| `src/transcription/` | Separation, F0, GAME/ROSVOT/YourMT3+ runs, ensemble, primary selection, index |
| `src/colour_regions/` | Release build, provenance tiers, geocoding, fingerprints, link check, metadata export, consolidated view, paper numbers |
| `src/regionclf/` | Region-classification experiments (merged corpus: `corpus.py`, `rev_merged.py`) |
| `src/annotation/` | Excerpt selection and packages for the notation study |
| `notebooks/04_colour_regions_corpus.py` | EDA figures `figures/cr_*` |
| `metadata/` | Git-tracked release: links + metadata per region, **no audio** |
| `data/` | Everything large (gitignored). Round 1 in `regions_audio/` and `regions_transcription/`; Round 2 in `regions_v2/`; release tables in `colour_regions/`; symlink view in `colour_regions/corpus/` |
| `.claude/skills/` | Project skills (see below) |

## Rebuild order after any curation change

```
python src/colour_regions/build_release.py      # data/colour_regions/*.csv
python src/colour_regions/export_metadata.py    # metadata/ (git release)
python src/colour_regions/consolidate.py        # data/colour_regions/corpus/ symlink view
python src/colour_regions/paper_numbers.py      # LaTeX number macros and tables for the paper
```

## Environments (this Mac)

- The default conda (`/usr/local/Caskroom/miniforge`, env `py312`) is **x86_64 under Rosetta**, so it has no MPS. Use it for data and CSV work.
- GPU and ML jobs use the arm64 conda at `~/miniforge3` (envs `sep`, `game`, `ymt3`, …). Launch GPU pipelines from an arm64 Python: children of an x86 Python run as i386 and fall back to CPU without warning.
- The system `node` is broken. Use `~/miniforge3/envs/node/bin/node`.

## Rules

- **Audio is third-party.** Never commit or redistribute it, or put it in a shared location outside the team. The release is links plus derived data.
- **Licence:** CC BY-NC-SA 4.0 for everything. Hosting: Hugging Face for data, GitHub for code.
- **Privacy:**
  - Singer names appear only for national heritage bearers; everyone else gets a pseudonymous `singer_id`.
  - `data/session_logs/` holds private Claude transcripts. Never share or commit them.
- **Downloads:**
  - Run one downloader at a time (`pgrep -fl download` first).
  - Pacing: 45–90 s per YouTube item, 8–20 s per Bilibili item. Fast YouTube runs trigger an hours-long bot wall.
  - Ask before using the user's browser cookies or session.
- **Evidence rule:** draw no conclusions on transcription friction, notation or cultural interaction from automatic data. They wait for the human notation study (3 notators per excerpt). Automatic probes count as exploratory only.
- **Paper numbers:** generate every number in the paper from data with a script (`paper_numbers.py`). Don't type numbers by hand.
- **Citations:** verify every one against a primary source (DOI, publisher or catalogue), and record how it was verified in the bib `verification` field.
- **Writing style:** about 80% of the way to ASD-STE100. Use short sentences, one idea per sentence, active voice and consistent terms. Use English region names after the 色彩区 introduction.
- **Paths:** use relative symlinks, and repo-relative paths in every CSV. The repo has moved before.
- **Git:** commit or push only when the user asks.
- **Methodology:** when unsure about a methodology choice, ask the user rather than guess.

## Skills

Two project skills are in `.claude/skills/`, and Claude Code loads them automatically in this repo:

- `regional-folk-audio-dataset`: the end-to-end playbook. It covers research-driven curation by search, downloading, transcription with model selection, and auditing without ground truth. Use it to extend the corpus to new regions or genres.
- `link-audio-transcription`: the general pipeline for downloading from links and transcribing at scale. It covers platform pitfalls, crash-safe GPU runs, fingerprints, link checks and the link-based release. Read its `references/failure_modes.md` before any long run.
