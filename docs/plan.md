# Aquarius: Unified Chinese Music Dataset — Execution Plan

## Project Goal

Build a **complete, gap-filled unified database** of Chinese music datasets for a TISMIR Dataset Article (deadline: 2026-12-01). The deliverable is a single dataset where every entry has all columns populated — either from source data or via imputation/generation.

**Scope**: All Chinese music — traditional through contemporary. See `docs/chinese_music_taxonomy_reference.md` for the musicological lens.

---

## How to Run This Loop

### First Iteration Bootstrap

If `docs/worklog.md` does not exist, this is a fresh start:
1. Create `docs/datasets/` directory and `docs/worklog.md`.
2. Read `AquariusDatasets.md` to understand the starting dataset list.
3. Begin Phase 1.

Python environment: use the `py312` conda environment (`conda activate py312`). Install packages as needed with `pip install`. No venv or requirements.txt to maintain.

### On Every Iteration

1. **Orient**: Read `docs/worklog.md`. Scan `docs/datasets/` to see what sections are filled. Check `data/raw/` for downloads. Determine current phase.
2. **Do one unit of work** from the current phase (see below).
3. **Check ending condition**. If met, log the phase as complete — next iteration starts Phase N+1.
4. **Log**: Append to `docs/worklog.md` using format: `## [YYYY-MM-DD] Phase N: what was done`. Include: datasets touched, results, decisions, what's next.
5. **Commit** all changed code and docs in one commit. Mention phase and datasets in the message.

### Units of Work

Each iteration does exactly one of these, then yields:
- A batch of 3–5 dataset registry entries (Phase 1)
- Dispatch + verify one batch of 2–3 download subagents (Phase 2)
- Dispatch + verify one batch of 2–3 inspection subagents (Phase 3)
- Phase 4 unification (main-agent work, one iteration)
- Phase 5 gap-filling plan (main-agent work, one iteration)

### Ending Conditions

| Phase | Done when | Next |
|-------|-----------|------|
| 1 | Every dataset has a `docs/datasets/<name>.md` with Source, Paper Insights, and preliminary Taxonomy Analysis | → Phase 2 |
| 2 | Every `ready` dataset attempted; every doc has Download Log filled | → Phase 3 |
| 3 | Every downloaded dataset has Inspection Results, Taxonomy Analysis (ground truth), and Gap Assessment; `docs/unified_schema.md` exists | → Phase 4 |
| 4 | `data/unified/master_table.parquet` + `gap_report.json` exist; every doc has Schema Mapping; `docs/gap_analysis_report.md` written; figures in `data/figures/` | → Phase 5 |
| 5 | `docs/gap_filling_plan.md` written | → **Stop** |
| **Stop** | All phases complete. Gap-filling *execution* is a separate human-approved phase. | — |

---

## Per-Dataset Documentation

`docs/datasets/<dataset_name>.md` is the **single source of truth** per dataset. Created in Phase 1, expanded through Phase 4. Every agent that touches a dataset **must update its doc**.

Template:

```markdown
# <Dataset Name>

## Source
- URL: ...
- Paper: ... (with citation)
- License: ...
- Access method: ...
- Status: ready / gated / dead / unclear

## Paper & Description Insights
What musicological question the dataset addresses. Design decisions.
Known limitations. Relationship to other datasets. Key quotes.

## Content & Taxonomy Analysis
Mapped to docs/chinese_music_taxonomy_reference.md:
- Time period / dynasty, region / ethnicity, genre / form
- Instrumentation, musical system, language
Note what is explicitly labeled vs. inferred.
(Phase 1: from paper. Phase 3: update with ground truth.)

## Download Log
- [date] Method tried — result
- Final status, file counts, total size, file type breakdown

## Inspection Results
- Verified file counts and types
- Every metadata column: name, type, example values, missing count
- Entry count and what each entry represents
- Data quality issues, surprises vs. paper claims

## Schema Mapping
Field mapping table (original name → unified schema name).
Which fields present, missing, need transformation.

## Gap Assessment
Missing modalities (generation feasibility), missing metadata
(imputation feasibility), priority ranking.
```

---

## Phase 1: Dataset Registry

**Owner**: Main agent

Build the catalog by creating `docs/datasets/<name>.md` for every Chinese music dataset.

1. Start from `AquariusDatasets.md`. For each entry, WebFetch the homepage/paper/GitHub.
2. Fill in Source, Paper & Description Insights, and preliminary Taxonomy Analysis.
3. Search for additional datasets: "Chinese music dataset MIR", "中国音乐数据集", snowball from citations, check HuggingFace/Kaggle/Zenodo/GitHub.
4. For parent/child datasets (e.g., CSMTD containing GZ_IsoTech): create docs for both, note relationship, mark child as "download via parent."
5. For dead links: search Wayback Machine, GitHub forks. For gated datasets: still create the doc with status `gated`.

---

## Phase 2: Download

**Owner**: Subagents dispatched by main agent

Download every `ready` dataset into `data/raw/<dataset_name>/`.

**Dispatch**: Group datasets by complexity (simple: git clone, CLI tools; complex: scraping, Chinese-language sites). Batch 2–3 subagents at a time. Give each: the dataset doc content + target directory.

**Subagent instructions** (read `docs/datasets/[name].md` and paste its full content into the prompt):

> Download dataset [NAME] into `data/raw/[NAME]/`. The dataset doc below has all known context.
>
> 1. Get the data — git clone, kaggle/huggingface CLI, write a scraper, navigate the website, handle zip extraction. The access method in the doc is a hint, not gospel.
> 2. Preserve original structure. Don't modify data.
> 3. Save download scripts to `src/downloaders/[name]_download.py`.
> 4. Update `docs/datasets/[name].md` Download Log: what you tried, results, final file counts/sizes/types.
> 5. If blocked (credentials, CAPTCHA, dead link): document the blocker and stop. Don't retry more than twice.
> 6. **Do not commit.** The main agent commits after verification.
>
> [paste full content of docs/datasets/[name].md here]

**Verification**: Check file counts on disk vs. doc, spot-check a few files, update status. Commit downloaders and docs.

---

## Phase 3: Inspect & Schema Discovery

**Owner**: Subagents dispatched by main agent

Profile every downloaded dataset. The superset of all discovered features becomes the unified schema.

**Dispatch**: One subagent per dataset, batches of 2–3. Give each: dataset path + dataset doc content.

**Subagent instructions** (read `docs/datasets/[name].md` and paste its full content into the prompt):

> Inspect dataset [NAME] at `data/raw/[NAME]/`. The dataset doc below has context from the paper.
>
> 1. Walk the directory tree. Map the structure.
> 2. Count and characterize every file type: audio (count, duration samples, sample rate), MIDI (track counts, instruments), scores, metadata files, lyrics, images.
> 3. For every metadata/CSV/JSON: extract all columns, types, example values, row counts, what each row represents, missing value counts.
> 4. Identify taxonomic labels present: genre, instruments, composer, period, region, ethnicity, mood, key/mode, tempo, language.
> 5. Note encoding issues (GB2312/GBK vs UTF-8), custom formats, annotation conventions.
> 6. Write inspection script at `src/inspectors/[name]_inspect.py`.
> 7. Update `docs/datasets/[name].md`: fill Inspection Results, expand Taxonomy Analysis with ground truth, fill Gap Assessment.
> 8. **Do not commit.** The main agent commits after verification.
>
> [paste full content of docs/datasets/[name].md here]

**Verification**: Read all dataset docs. Build the unified schema (union of all discovered fields + taxonomy reference fields). Save as `docs/unified_schema.md`. Commit.

---

## Phase 4: Unify & Gap Analysis

**Owner**: Main agent

1. Write `src/unify.py`: read raw data, map fields to unified schema, normalize encoding/language, assign IDs (`<dataset>__<original_id>`), output `data/unified/master_table.parquet` + `.csv` sample. Track provenance per cell: `source` / `inferred` / `missing`.
2. Write `src/gap_analysis.py`: produce gap report (`data/unified/gap_report.json`), modality gap matrix, metadata gap matrix, priority list. Save readable version as `docs/gap_analysis_report.md`.
3. Generate figures in `data/figures/`: dataset×modality heatmap, dataset×metadata heatmap, temporal/genre/modality distributions.
4. Update every dataset doc: fill Schema Mapping, finalize Gap Assessment.

**Guidelines**: Use parquet for working data. Handle mixed granularity (song vs. segment vs. note) carefully. Map synonymous fields to canonical names (keep mapping in each doc's Schema Mapping). Preserve Chinese text as UTF-8, add translations as extra columns.

---

## Phase 5: Gap Filling (Plan Only)

**Owner**: Main agent writes `docs/gap_filling_plan.md`; execution is a separate human-approved phase.

Analyze the gap report and cover:
1. **Modality generation**: MIDI→audio (synthesis tools, Chinese instrument soundfonts), audio→MIDI (transcription models, accuracy expectations), audio/MIDI→score (MusicXML, jianpu handling), quality thresholds
2. **Metadata imputation**: composer (filename parsing, DB cross-reference, LLM lookup), period (genre/style inference), region/ethnicity (genre labels, instrument use, lyrics language), instrumentation (audio recognition, MIDI programs), genre (classifiers, catalogs), key/mode (Chinese pentatonic-aware detection), tempo
3. **Confidence tracking**: every imputed value gets a score + method tag
4. **Validation**: sample-based human review, cross-validation, consistency checks
5. **Prioritization**: highest-impact, highest-confidence fills first

---

## General Guidelines

### Pacing
- **Max 2–3 subagents in parallel.** Batch, verify, then dispatch next.
- **Simple datasets first** to validate the workflow cheaply.
- **Main agent handles small tasks inline** — don't spawn a subagent for a quick git clone.
- **Fail fast**: two retries max, then log and move on.
- **Background execution** for large downloads — don't block.

### Data Rules
- **50 GB cap per dataset.** Prioritize: metadata (full) → MIDI/score → audio (sample). Document what was skipped.
- **Deduplicate aggressively.** Parent contains child → download parent only. Document every skip in the parent doc and worklog.
- **Chinese encodings**: try UTF-8 first, fall back to GBK/GB2312/Big5. Preserve original text.
- **Escalate to human** when blocked by credentials, CAPTCHAs, or paid access. Document and move on.

### Project Structure
```
docs/
├── plan.md                             # This file
├── worklog.md                          # Chronological project log
├── chinese_music_taxonomy_reference.md
├── unified_schema.md                   # Phase 3: superset schema
├── gap_analysis_report.md              # Phase 4
├── gap_filling_plan.md                 # Phase 5
└── datasets/                           # One doc per dataset (single source of truth)

src/
├── downloaders/                        # Per-dataset download scripts
├── inspectors/                         # Per-dataset inspection scripts
├── unify.py                            # Phase 4
└── gap_analysis.py                     # Phase 4

data/                                   # Gitignored
├── raw/<dataset_name>/                 # Phase 2
├── unified/                            # Phase 4
│   ├── master_table.parquet
│   ├── master_table_sample.csv
│   ├── gap_report.json
│   └── coverage_matrix.csv
└── figures/                            # Paper visualizations
```

### Python
- Use `py312` conda environment. Install packages as needed with `pip install`. All code in `src/`.

### Git
- Commit code and docs after every unit of work. Data is gitignored.
- Commit messages: mention phase and dataset(s).
