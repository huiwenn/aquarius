# China Colour Regions interactive map

An audio-free, browser-based map of provincial-level recording locations in the Colour Regions collection. Province borders come from Tianditu national-standard vector geometry, distributed in GeoJSON format by [GeoJSON.cn](https://geojson.cn/data/atlas/tiandi). The map uses [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) to render and interact with the provincial polygons.

## Run locally

From the repository root, regenerate the summary bundle and serve the folder over HTTP:

```powershell
& 'C:\Users\ruilu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' web/china-map/build_data.py
cd web/china-map
python -m http.server 8000
```

Open `http://localhost:8000`. The page loads MapLibre GL JS and its fonts from public CDNs. The boundary GeoJSON is included locally, so no basemap tile service is required.

## Data policy

- The fill counts recordings whose `metadata/recordings.csv` province exactly maps to a province-level geometry.
- Cross-province, non-standard, blank, and otherwise ambiguous province labels are not allocated to a polygon. The page reports the number excluded from the province layer.
- The collection's cultural-region classification is separate; the selected province profile shows a count breakdown by cultural region.
- The page links out to the recording's source URL. It does not download, embed, or redistribute audio.
- Boundary line features are excluded; the 34 provincial-level administrative units are rendered.

The source geometry is derived from public Tianditu/GeoJSON.cn vectors and simplified for web display. For research requiring legally authoritative boundaries or survey-grade precision, cite and obtain the relevant official dataset directly from the National Geomatics Center of China. See [China's public map-data portal](https://www.webmap.cn/main.do?method=index1).
# Colour Regions (色彩区): an open corpus of Chinese folk song

Colour Regions groups 1,692 linked recordings of Chinese folk song into the 15 colour regions (色彩区) of Chinese folk-song scholarship. Each recording comes with curation metadata, song labels (class, genre, composer, period), note transcriptions (MIDI, MusicXML) and pitch tracks (F0). The audio is not redistributed: the release is links plus derived data.

The dataset paper targets the TISMIR special collection *Open Music Data for Music Processing Research* (deadline 2026-12-01).

## Where everything is

| What | Where | Who can see it |
|---|---|---|
| **Code**, docs, curation metadata | This GitHub repo: [huiwenn/aquarius](https://github.com/huiwenn/aquarius) | repo collaborators |
| **Dataset** (tables, MIDI, MusicXML, F0) | Hugging Face: [sophiaphia/colour-regions](https://huggingface.co/datasets/sophiaphia/colour-regions) | private until release |
| **Paper** (LaTeX) | Overleaf: [project 6ac1a10e…](https://www.overleaf.com/project/6ac1a10eeafb4aa693a8d7b6), synced to GitHub [huiwenn/color-regions-paper-](https://github.com/huiwenn/color-regions-paper-) | invited collaborators |
| **Audio and working data** (`data/`) | The team drive. Never on GitHub, Hugging Face or any public location | team only |

## Code (this repo)

| Path | Contents |
|---|---|
| `src/secaiqu/` | Search, download, audit and speech screen |
| `src/transcription/` | Separation, F0, transcription models, ensemble, primary selection, index; `run_round.sh` processes a collection round |
| `src/colour_regions/` | Release build, provenance, privacy, song labels, Anthology overlap, metadata export, Hugging Face build, paper numbers |
| `src/regionclf/` | The example study: region classification |
| `src/annotation/` | Excerpt selection and the offline notator page for the human notation study |
| `metadata/` | The release tables, git-tracked (links and metadata, **no audio**); `metadata/README.md` explains every column |
| `docs/` | Running logs per topic. **`docs/worklog.md` is the handoff log: read its newest section first** |
| `.claude/skills/` | Project skills for Claude Code |

**Getting started.**
1. Read `CLAUDE.md` (project rules) and the newest entry in `docs/worklog.md`.
2. Get `data/` from the team drive and put it at `data/` in your clone (it is gitignored).
3. To add recordings, label songs, fix a label or rebuild the release, follow the `colour-regions-curation` skill (`.claude/skills/colour-regions-curation/SKILL.md`). Claude Code loads it automatically in this repo.

**Collaborating on code.**
- Work on a branch and open a pull request. `master` holds the released state.
- Before you commit, rebuild and run the checks:
  ```
  python src/colour_regions/build_release.py
  python src/colour_regions/export_metadata.py
  python src/colour_regions/consolidate.py
  python .claude/skills/colour-regions-curation/scripts/check_release.py   # must print OK
  ```
- Never commit audio, anything under `data/`, credentials or browser cookies.
- Never edit the generated tables (`metadata/*.csv`, `data/colour_regions/*.csv`) by hand. Each change goes into its source file (see the skill, `references/files.md`), followed by a rebuild.
- Add a dated entry to `docs/worklog.md` for every working session.

## Data (Hugging Face)

The dataset is the private repo `sophiaphia/colour-regions`. The card (`README.md` there) describes the contents, the method, the columns, how to get and verify the audio, and the limitations.

**Access.** A private dataset under a personal account is visible only to that account. To give teammates access, move it to a Hugging Face organization and add them as members:
```
hf repos move sophiaphia/colour-regions <org>/colour-regions --type dataset
```
After a move, update the repo id here, in `CLAUDE.md` and in `src/colour_regions/build_hf.py`.

**Reading the data.**
```
hf auth login
hf download sophiaphia/colour-regions --repo-type dataset --local-dir colour-regions
```
or with Python: `datasets.load_dataset("sophiaphia/colour-regions", "recordings")` (other configs: `song_labels`, `anthology_overlap`, `scores`, `score_matches`, `fingerprints`, `link_status`).

**Updating the data.** The Hugging Face repo is a build output. Don't edit files on the website.
1. Change the source files in this repo and rebuild (see above). The card text lives in `docs/hf_dataset_card.md`.
2. Build the release folder: `python src/colour_regions/build_hf.py` (writes `data/hf_release/`).
3. Upload. Use a pull request when the change needs review:
   ```
   hf upload sophiaphia/colour-regions data/hf_release . --type dataset --commit-message "…" [--create-pr]
   ```
4. Commit the matching code and `metadata/` to GitHub, so the two stay in step.

Licence: CC BY-NC-SA 4.0. Personal names appear only for national heritage bearers; `src/colour_regions/privacy.py` redacts all other singer names. `check_release.py` fails if one leaks.

## Paper (Overleaf, synced with GitHub)

- **Overleaf:** https://www.overleaf.com/project/6ac1a10eeafb4aa693a8d7b6, for writing, comments and track changes.
- **GitHub:** [huiwenn/color-regions-paper-](https://github.com/huiwenn/color-regions-paper-), the same project through Overleaf's GitHub sync, for local builds and generated files.
- **Local clone:** next to this repo, as `../color-regions-paper`:
  ```
  cd ..  &&  git clone git@github.com:huiwenn/color-regions-paper-.git color-regions-paper
  ```
  The scripts here write into that folder (override with `AQ_PAPER=/path/to/paper`). The older folder `../colour_regions_paper/` is a stale pre-sync copy; don't use it.

**Joining.** The owner invites you by email on Overleaf (Share → "Can edit" to write, "Can review" to comment and suggest). For local work you also need access to the GitHub repo.

**How the sync works.** Overleaf's GitHub sync is not automatic: someone presses the buttons in Overleaf (Menu → GitHub).
1. **Before local work:** in Overleaf, *Push Overleaf changes to GitHub*. Then run `git pull` in `../color-regions-paper`.
2. **Local work** (generated numbers, tables, figures, bulk edits): commit and push to GitHub.
3. **After pushing:** in Overleaf, *Pull GitHub changes into Overleaf*. Overleaf merges; resolve any conflict there.

Keep text edits on Overleaf where you can, so collaborators see them live. Use the local clone for what scripts produce.

**Writing together.**
- Use **Track changes** for edits to someone else's section, and **Comments** for questions. Resolve comments when done.
- One person per section at a time. Say which section you are working on.
- Style: about 80% of the way to ASD-STE100, with short sentences, active voice and consistent terms (see `CLAUDE.md`). English region names after the 色彩区 introduction.
- **Word limit:** 8,000 words including references. `bash build.sh` in the paper folder compiles locally and reports the count.
- **Citations:** each one goes in `refs/` with a `verification` field saying how it was checked against a primary source.
- **Claims:** draw no conclusions about transcription friction, notation or cultural interaction from automatic data (`docs/thesis_evidence_plan.md`).

**Numbers, tables and figures are generated, never typed.**
- `python src/colour_regions/paper_numbers.py` writes `generated/numbers.tex` (macros such as `\NRecTotal`), `generated/table_*.tex` and `generated/supp_*.tex`.
- `python notebooks/04_colour_regions_corpus.py` writes `figures/cr_*`.
- `build.sh` reruns `paper_numbers.py` on every build.
- Commit the generated files and push, then pull them into Overleaf. Never edit a generated file on Overleaf: the next run overwrites it.
- Don't commit LaTeX build output. If `main.pdf` or other tracked build files changed after a local build, restore them with `git restore main.pdf main.ent main.maf main.mtc main.mtc0` before you commit.

## Contacts and status

Project owner: Sophia Sun. Current status, open decisions and next steps are in the newest section of `docs/worklog.md`.
