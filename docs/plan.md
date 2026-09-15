# Aquarius: Unified Chinese Music Dataset — Execution Plan

## Project Goal

Build a **complete, gap-filled unified database** of Chinese music datasets for a TISMIR Dataset Article (deadline: 2026-12-01). The deliverable is a single dataset where every entry has all columns populated — either from source data or via imputation/generation. The paper documents the taxonomy, curation process, gap analysis, and gap-filling methodology.

**Scope**: All Chinese music — traditional through contemporary (folk, opera, instrumental, C-pop, Mandopop, rock, guofeng, etc.).

See `docs/chinese_music_taxonomy_reference.md` for the musicological lens guiding categorization.

---

## Worklog Discipline

Every step of this project must be documented as it happens — not reconstructed after the fact. The worklog serves three purposes: (1) the paper's methodology section draws directly from it, (2) a new agent session can read the logs and pick up where the last left off, (3) the human collaborator can review decisions and reasoning asynchronously.

### Per-Dataset Documentation

Every dataset gets its own markdown file at `docs/datasets/<dataset_name>.md`. This is the **single source of truth** for everything learned about that dataset — there is no separate registry summary or profile document. It is created during Phase 1 and expanded during Phases 2–4 as work progresses. Structure:

```markdown
# <Dataset Name>

## Source
- URL: ...
- Paper: ... (with citation)
- License: ...
- Access method: ...
- Status: ready / gated / dead / unclear

## Paper & Description Insights
What the paper/README says this dataset is for. Key findings from reading
the publication. What musicological questions it was designed to address.
Design choices the authors made and why. Known limitations they acknowledge.
Relevant quotes from the paper.

## Content & Taxonomy Analysis
What kind of music is actually in this dataset, analyzed through our
taxonomy lens (see docs/chinese_music_taxonomy_reference.md):
- Time period / dynasty coverage
- Regional / ethnic representation
- Genre / form breakdown
- Instrumentation
- Musical system (pentatonic modes, tuning, etc.)
- Language (for vocal music)
Note what is explicitly labeled vs. what we inferred.
(Phase 1: fill from paper. Phase 3: update with ground truth from inspection.)

## Download Log
Chronological log of download attempts:
- [date] Attempted method X — result
- [date] Wrote scraper at src/downloaders/... — result
- Final status: success / partial / failed
- Files downloaded: N, total size: X MB
- File types: {".wav": 100, ".mid": 20, ".csv": 3}
(If blocked by access controls, document what's needed and move on.)

## Inspection Results
What we found when we actually looked at the data:
- File counts and types (verified, not just reported)
- Metadata fields discovered (list every column with types and examples)
- Number of entries, what each entry represents (song, segment, note, etc.)
- Data quality issues (encoding problems, missing values, inconsistencies)
- Surprises — anything that contradicts the paper's description

## Schema Mapping
How this dataset's fields map to the unified schema.
Which fields are present, which are missing, which need transformation.
Field name mapping table (original → unified).

## Gap Assessment
What's missing from this dataset and how hard it would be to fill:
- Missing modalities and generation feasibility
- Missing metadata and imputation feasibility
- Priority ranking for gap-filling
```

Not every section needs to be filled at once — they accumulate across phases. But every agent that touches a dataset **must update its doc**. No silent work.

### Main Worklog

The main agent maintains `docs/worklog.md` — a chronological log of high-level decisions, batch dispatches, verification results, and phase transitions. Format:

```markdown
## [YYYY-MM-DD] Phase X: Brief description
What was done, what was decided, what's next.
- Dispatched subagents for: dataset_a, dataset_b, dataset_c
- Results: dataset_a succeeded, dataset_b failed (reason), dataset_c partial
- Decided to defer dataset_b to next session because...
- Committed: [commit hash or description]
```

Keep it concise but complete. A new session should be able to read `docs/worklog.md` and understand the full project history.

---

## Phase 1: Dataset Registry & Metadata Catalog

**Owner**: Main agent

**Goal**: Build a catalog of every known Chinese music dataset before downloading anything. The per-dataset docs (`docs/datasets/<name>.md`) are the catalog — there is no separate registry file.

### Instructions

1. Start from `AquariusDatasets.md` which lists known datasets and URLs.
2. For each entry, use WebFetch and WebSearch to visit the dataset's homepage, paper, or GitHub repo.
3. **Create `docs/datasets/<dataset_name>.md`** and fill in:
   - **Source** section: name, URLs, paper citation, access method, license, status
   - **Paper & Description Insights**: read the associated paper or website thoroughly — don't just skim. Extract what musicological question the dataset was built to answer, design decisions, known limitations, and how it relates to other datasets.
   - **Content & Taxonomy Analysis** (preliminary): what the paper claims about the content, mapped to our taxonomy. Actual verification comes in Phase 3.
4. Search for additional Chinese music datasets not in `AquariusDatasets.md`:
   - "Chinese music dataset MIR"
   - "Chinese traditional music corpus"
   - "中国音乐数据集" (Chinese-language searches)
   - "Chinese music audio MIDI dataset"
   - Check papers that cite the datasets we already know (snowball search)
   - Check HuggingFace, Kaggle, Zenodo, and GitHub for Chinese music datasets
5. **Handle parent/child datasets**: When a parent dataset (e.g., CSMTD) contains sub-datasets that also appear independently (e.g., GZ_IsoTech), create docs for both but note the relationship in each. Mark the child's doc with a note: "Contained within [parent] — will download via parent, not standalone." This keeps the landscape complete while avoiding duplicate downloads.
6. Commit all `docs/datasets/*.md` files and update `docs/worklog.md`.

### Guidelines

- Be thorough. A dataset paper's value scales with coverage. Missing a major dataset is worse than including a minor one.
- If a dataset URL is dead, search for mirrors or archived versions (Wayback Machine, alternative GitHub forks). Update status accordingly.
- When a paper describes a dataset but doesn't provide a download link, still create its doc with status `gated` or `unclear` — we want to document the landscape even if we can't get everything.

---

## Phase 2: Download & Ingest

**Owner**: Subagents (one per dataset or small batch)

**Goal**: Download every accessible dataset into `data/raw/<dataset_name>/`.

### How to Dispatch Subagents

The main agent should:
1. Read through `docs/datasets/` to find all datasets with status `ready`.
2. Group by access method complexity:
   - **Simple**: Direct HTTP download, git clone, pip/kaggle/huggingface CLI — these can be batched.
   - **Complex**: Requires scraping, navigating a website, filling out forms, handling CAPTCHAs, dealing with Chinese-language UIs, or writing custom download scripts.
3. Spawn subagents in batches of 2–3 (see Pacing). Give each subagent:
   - The dataset name and the content of its `docs/datasets/<name>.md` (so it has all context)
   - The target directory: `data/raw/<dataset_name>/`

### Subagent Instructions (include in each subagent prompt)

You are downloading a Chinese music dataset. Your job:

1. **Figure out how to get the data.** The access method in the dataset doc is a starting hint, not gospel. You may need to:
   - Clone a git repo
   - Use `kaggle datasets download` or `huggingface-cli download`
   - Write a Python script using requests/BeautifulSoup/selenium to scrape download links
   - Navigate a Chinese-language website (read the HTML, follow links, find the actual download)
   - Download from Google Drive, Baidu Pan, or other cloud storage
   - Handle zip/tar extraction
2. **Download into `data/raw/<dataset_name>/`.** Preserve the original directory structure.
3. **Don't modify the data.** Download as-is. No renaming, no reformatting.
4. **If you can't download it**, document why in the dataset doc and move on. Don't silently fail.
5. All download scripts you write go in `src/downloaders/`. Name them by dataset. Keep them — they're part of the reproducibility story for the paper.
6. **Update `docs/datasets/<dataset_name>.md`** — fill in the **Download Log** section with a chronological record of what you tried, what worked, what failed, file counts, total size, and file type breakdown.

### Main Agent Verification

After subagents complete:
1. Verify file counts on disk match what the dataset doc reports (`find data/raw/<name> -type f | wc -l`).
2. Spot-check a few files from each dataset (can you open an audio file? does the CSV parse?).
3. Update dataset doc status if needed (e.g., `ready` → `partial` if some files failed).
4. Flag datasets that failed and decide whether to retry with a different approach or mark as inaccessible.
5. Commit any new code in `src/downloaders/` and updated docs.

---

## Phase 3: Inspect & Schema Discovery

**Owner**: Subagents (one per dataset)

**Goal**: Profile every downloaded dataset to discover what fields, modalities, and metadata exist. The superset of all discovered features becomes the unified schema.

### How to Dispatch Subagents

Spawn one subagent per downloaded dataset (in batches of 2–3). Give each:
- The dataset path: `data/raw/<dataset_name>/`
- The content of its `docs/datasets/<name>.md` (for context from the paper)

### Subagent Instructions (include in each subagent prompt)

You are profiling a Chinese music dataset. Your job is to understand everything about its structure and content.

1. **Walk the directory tree.** Map out the folder structure. Understand the organization.
2. **Identify all file types** and count them. For each type:
   - Audio files (wav, mp3, flac, ogg): count, total duration if feasible (use `librosa` or `soundfile` to sample a few), sample rates, bit depths
   - MIDI files: count, sample a few to check track counts, instruments used
   - Score files (musicxml, mei, pdf, jianpu images): count, format details
   - Metadata files (csv, json, tsv, xlsx, txt): read them thoroughly — these are gold
   - Lyrics files: count, format, language
   - Image files (spectrograms, covers, notation images): count, purpose
3. **For every metadata/CSV/JSON file**, extract:
   - All column names / field names
   - Data types and example values for each field
   - Number of rows/entries
   - What entity each row represents (a song? a performance? a segment? a note?)
   - Missing value counts per column
4. **Identify the taxonomic features present** — does this dataset tag its items with:
   - Genre/form? Instruments? Composer/performer? Time period/dynasty?
   - Region/province? Ethnic group? Mood/emotion? Key/mode/scale?
   - Tempo/rhythm? Language (for vocal music)? Any other labels?
5. **Note anything unusual or dataset-specific**: custom file formats, annotation conventions, encoding issues (Chinese character encodings — watch for GB2312/GBK vs UTF-8), README contents.
6. **Write a Python inspection script** at `src/inspectors/<dataset_name>_inspect.py` that can reproduce the profile. Keep it — it's part of reproducibility.
7. **Update `docs/datasets/<dataset_name>.md`**:
   - Fill in **Inspection Results** with what you found — file counts, metadata fields with types and examples, data quality issues, surprises vs. paper claims.
   - Expand **Content & Taxonomy Analysis** with ground-truth observations: what time periods, regions, genres, instruments are actually represented? What's labeled vs. unlabeled? Does the data match what the paper claimed?
   - Fill in **Gap Assessment** — what modalities and metadata are missing?

### Main Agent Verification

After inspection subagents complete:
1. Read all `docs/datasets/*.md` files — specifically the Inspection Results and Gap Assessment sections.
2. **Build the unified schema**: collect every metadata field discovered across all datasets. Every field that appears in any dataset becomes a column. Add standard fields from the taxonomy reference even if no dataset has them yet — these are the gaps to fill.
3. Save the unified schema as `docs/unified_schema.md`. (If Phase 4 code needs a machine-readable version, generate `data/unified_schema.json` from the schema doc at that point — don't maintain two sources.)
4. Commit inspection scripts and schema docs.

---

## Phase 4: Unify & Gap Analysis

**Owner**: Main agent

**Goal**: Merge all datasets into one master table using the unified schema, and produce a detailed gap report.

### Instructions

1. Write `src/unify.py` — a script that:
   - Reads every dataset's raw data (using the inspection scripts or their logic for parsing)
   - Maps each dataset's fields to the unified schema (field name normalization, value standardization)
   - Handles encoding normalization (all text to UTF-8)
   - Handles language normalization (Chinese field names → English, or keep both)
   - Assigns each entry a unique ID: `<dataset_name>__<original_id>`
   - Outputs `data/unified/master_table.parquet` (and `.csv` for inspection)
2. For each cell in the master table, track provenance:
   - `source`: the value came directly from the dataset
   - `inferred`: derived from other fields or filename patterns
   - `missing`: not available, needs imputation or generation
3. Write `src/gap_analysis.py` — produces:
   - **Gap report** (`data/unified/gap_report.json`): for each dataset, what percentage of each column is filled
   - **Modality gap matrix**: which datasets have audio but no MIDI, MIDI but no audio, etc.
   - **Metadata gap matrix**: which datasets lack composer, period, region, etc.
   - **Priority list**: which gaps are most impactful to fill (e.g., a dataset of 1000 songs missing only composer info is higher priority than one of 10 songs missing everything)
4. Save human-readable gap analysis as `docs/gap_analysis_report.md`.
5. Generate visualization figures in `data/figures/` for the paper:
   - Dataset x modality heatmap
   - Dataset x metadata coverage heatmap
   - Temporal distribution of entries across datasets
   - Genre distribution
   - Modality distribution (pie/bar)
6. **Update every `docs/datasets/<dataset_name>.md`** — fill in the **Schema Mapping** section documenting how each dataset's fields map to the unified schema, and finalize the **Gap Assessment** with specific gap-filling priority.
7. Update `docs/worklog.md` with Phase 4 decisions and results.
8. Commit all code and docs.

### Guidelines

- The master table will likely have thousands of rows and dozens of columns. Use parquet for the working format (efficient, typed), CSV only for human inspection of samples.
- Don't force every dataset into identical granularity. Some datasets have one row per song, others per phrase or per note. Record the granularity level and handle aggregation carefully.
- When field names differ but mean the same thing (e.g., "artist" vs "performer" vs "演奏者"), map them to one canonical name. Keep the mapping in each dataset's Schema Mapping section.
- Chinese characters in metadata should be preserved as-is (UTF-8). Add romanized/English translations as separate columns where useful.

---

## Phase 5: Gap Filling (Plan Only)

**Owner**: Main agent writes the plan; execution is a separate phase.

**Goal**: After Phase 4, write a detailed plan for filling every gap in the master table so the final database has no missing columns.

### What the Plan Should Cover

The main agent should analyze the gap report from Phase 4 and write `docs/gap_filling_plan.md` covering:

1. **Modality generation**:
   - MIDI → Audio: which synthesis tools to use, which soundfonts (especially for traditional Chinese instruments — erhu, guzheng, pipa, dizi soundfonts), quality validation
   - Audio → MIDI: which transcription models to use (basic-pitch, MT3, omnizart), expected accuracy for Chinese music (polyphonic traditional ensemble is very hard), fallback to melody-only transcription
   - Audio/MIDI → Score: which tools for MusicXML generation, how to handle jianpu notation
   - What quality threshold makes a generated modality worth including vs. marking as "generated, low confidence"

2. **Metadata imputation**:
   - **Composer/performer**: strategies for inference — filename parsing, cross-referencing with music databases, LLM-assisted lookup from song titles
   - **Time period/dynasty**: inference from genre, style analysis, associated metadata, publication dates of recordings
   - **Region/ethnic group**: inference from genre labels (e.g., Xinjiang folk → Uyghur/Xinjiang), instrument use, language of lyrics
   - **Instrumentation**: audio-based instrument recognition models, MIDI program numbers → instrument names, manual annotation for small datasets
   - **Genre/form**: classification models, cross-referencing with known catalogs, LLM-assisted from titles and metadata context
   - **Key/mode**: audio key detection, MIDI analysis, special handling for Chinese pentatonic modes (most Western key detectors assume 12-TET diatonic)
   - **Tempo**: audio tempo estimation, MIDI tempo extraction

3. **Confidence tracking**: every imputed or generated value gets a confidence score and method tag so users of the database know what's ground truth vs. inferred.

4. **Validation strategy**: how to spot-check imputed values — sample-based human review, cross-validation against known entries, consistency checks.

5. **Prioritization**: which gaps to fill first based on the gap analysis — highest-impact, highest-confidence fills first.

---

## General Guidelines for All Agents

### Python Environment
- Use a virtual environment in the project root (`.venv/`).
- Core dependencies: `pandas`, `numpy`, `librosa`, `mido` (MIDI), `music21` (score), `soundfile`, `requests`, `beautifulsoup4`, `tqdm`, `pyarrow` (parquet).
- Install additional packages as needed. Keep `requirements.txt` updated.
- All code goes in `src/`. Subdirectories: `src/downloaders/`, `src/inspectors/`, with other scripts at `src/` root level.

### Project Structure
```
docs/
├── plan.md                        # This file
├── worklog.md                     # Chronological project log
├── chinese_music_taxonomy_reference.md
├── unified_schema.md              # Phase 3 output — the superset schema
├── gap_analysis_report.md         # Phase 4 output
├── gap_filling_plan.md            # Phase 5 output
└── datasets/                      # Per-dataset documentation (single source of truth)
    ├── ccmusic.md
    ├── pop909.md
    ├── opencpop.md
    └── ... (one per dataset)

src/
├── downloaders/                   # Per-dataset download scripts
│   ├── ccmusic_download.py
│   └── ...
├── inspectors/                    # Per-dataset inspection scripts
│   ├── ccmusic_inspect.py
│   └── ...
├── unify.py                       # Phase 4
├── gap_analysis.py                # Phase 4
└── requirements.txt

data/                              # Gitignored — all data artifacts
├── raw/                           # Phase 2: downloaded datasets
│   └── <dataset_name>/
├── unified/                       # Phase 4: merged outputs
│   ├── master_table.parquet
│   ├── master_table_sample.csv
│   ├── gap_report.json
│   └── coverage_matrix.csv
└── figures/                       # Visualizations for the paper
```

Note: there is no `data/dataset_registry.json` or `data/profiles/` directory. The per-dataset docs in `docs/datasets/` are the registry and the profiles. Machine-readable data (like `gap_report.json`) is generated by scripts only when code needs to consume it — it is an output, not a maintained document.

### Git Discipline
- Commit code and docs frequently. Data is gitignored.
- Commit messages should say what phase/dataset the work covers.
- Don't commit large data files, audio, or binary blobs.

### Error Handling & Escalation
- Network failures, encoding errors, and malformed data are expected. Handle gracefully.
- Always log what went wrong. Never silently skip a dataset.
- If a download or inspection fails, record the failure in that dataset's doc and move on — don't block the whole pipeline.
- **When to escalate to the human**: If a dataset requires institutional credentials, paid access, or manual steps that an agent cannot perform (e.g., filling a form with a real identity, solving a CAPTCHA, emailing a researcher), document the blocker in `docs/datasets/<name>.md` under Download Log and move on. Don't burn tokens trying to work around access controls.

### Data Size Limits
- **50 GB cap per dataset.** If a dataset's total size exceeds 50 GB, download metadata files and a representative sample of media files (e.g., first N audio files, or one file per category/folder). Document what was sampled and what was skipped in the dataset's doc.
- For datasets near the limit, prioritize: metadata/CSVs first (always full), then MIDI/score (small), then audio (large). Audio is the modality we can regenerate from MIDI if needed.
- Record the full dataset size in the doc even if only a sample was downloaded, so the gap analysis knows the true scale.

### Deduplication
- **Deduplicate aggressively.** Some datasets are subsets of larger ones (e.g., CSMTD contains GZ_IsoTech, GuZheng MIDI-Wav, etc. as sub-databases). When a parent dataset contains a child, download only the parent.
- **Always document skipped sub-datasets** in both: (1) the parent's `docs/datasets/<parent>.md` noting which children it subsumes, and (2) `docs/worklog.md` with a clear entry like "Skipped standalone download of X because it is contained within Y."
- If a child dataset has additional annotations or modalities not in the parent, download only the extra parts and note the relationship.
- During Phase 4 unification, check for duplicate entries across datasets by matching on title, filename, or audio fingerprint where feasible.

### Chinese Language Handling
- Expect GB2312, GBK, Big5, and UTF-8 encodings. Try UTF-8 first, fall back to others.
- Preserve original Chinese text. Add translations/romanizations as extra fields.
- Some READMEs and metadata will be in Chinese only — read and process them.

### Pacing & Token Budget Awareness

This project runs on a Claude plan with finite daily/monthly token usage. Every subagent consumes tokens — spawning, context passing, tool calls, retries. The main agent must pace work to avoid burning through the budget before the pipeline completes.

**Rules:**
- **Max 2–3 subagents running in parallel at any time.** Do not fan out one subagent per dataset all at once. Work in small batches: dispatch 2–3, wait for them to finish, verify their output, then dispatch the next batch.
- **Batch by complexity.** Start each phase with the simplest datasets (direct git clone, small size, clean metadata) to validate the approach cheaply. Save complex/scraping-heavy datasets for later batches when the workflow is proven.
- **Prefer the main agent for small tasks.** If a dataset can be cloned and inspected in a few tool calls, do it inline rather than spawning a subagent. Subagents have overhead (prompt context, cold start). Reserve them for tasks that genuinely need isolation or parallelism — large downloads, complex scraping, or datasets that need custom code.
- **Checkpoint frequently.** After each batch of subagents completes, the main agent should commit code/docs and update the worklog. If the session ends mid-pipeline, the next session can pick up from the last checkpoint rather than re-doing work.
- **Fail fast, don't retry endlessly.** If a download or scrape fails twice, log it and move on. Burning tokens on retries for a flaky server is wasteful — flag it for a future session or manual intervention.
- **Phase 1 is cheap; Phase 2 is expensive.** The registry (Phase 1) is mostly WebFetch calls by the main agent — do it fully before starting any downloads. This avoids spawning subagents for datasets that turn out to be duplicates or inaccessible.
- **Monitor progress against the dataset count.** If there are ~15 datasets, plan for ~5 batches of 2–3 across Phases 2 and 3. If the registry grows to 30+, consider triaging: prioritize open-access, well-documented datasets first; defer gated/unclear ones.
- **Long-running downloads: use background execution.** For large datasets (multi-GB audio collections), kick off the download in background and move on to other work. Don't block the main agent waiting.

### Session Start: How to Resume

At the start of every session (or goal loop iteration), the main agent must orient itself before doing new work:

1. **Read `docs/worklog.md`** — understand what has been done and what was planned next.
2. **Scan `docs/datasets/`** — see which per-dataset docs exist and how complete each section is.
3. **Check `data/raw/`** — which datasets have been downloaded (look for non-empty directories).
4. **Determine current phase** — based on what exists, figure out where to pick up.
5. **Log the session start** in `docs/worklog.md` with what you found and what you plan to do.

### Ending Conditions

The goal loop should check these conditions at the end of each iteration:

**Phase 1 complete when:**
- Every known dataset has a `docs/datasets/<name>.md` with Source, Paper & Description Insights, and preliminary Content & Taxonomy Analysis filled
- Worklog documents the registry is complete and ready for download phase

**Phase 2 complete when:**
- Every dataset with status `ready` has been attempted
- Every `docs/datasets/<name>.md` has its Download Log section filled
- Worklog documents download results and any failures

**Phase 3 complete when:**
- Every successfully downloaded dataset has its Inspection Results, ground-truth Content & Taxonomy Analysis, and Gap Assessment sections filled in `docs/datasets/<name>.md`
- `docs/unified_schema.md` exists (the superset schema)
- Worklog documents inspection results

**Phase 4 complete when:**
- `data/unified/master_table.parquet` exists
- `data/unified/gap_report.json` exists
- `data/figures/` contains the coverage and distribution visualizations
- Every `docs/datasets/<name>.md` has its Schema Mapping section filled
- `docs/gap_analysis_report.md` is written
- Worklog documents unification results

**Phase 5 complete when:**
- `docs/gap_filling_plan.md` is written with concrete strategies for every identified gap
- Worklog documents the plan

**Full pipeline complete when:**
- All five phases are marked complete in the worklog
- The main agent writes a final summary in `docs/worklog.md` stating: all phases done, here's what we have, here's what's left for gap-filling execution

At this point the goal loop should **stop** — gap-filling execution (Phase 5's plan put into action) is a separate project phase that should be reviewed by the human before launching.

### What To Do in a Single Goal Loop Iteration

Each iteration should accomplish one meaningful unit of work and then yield. Don't try to run the entire pipeline in one iteration. Good units:

- Complete Phase 1 registry (if small enough) or a batch of 3–5 dataset registry entries
- Dispatch and verify one batch of 2–3 download subagents
- Dispatch and verify one batch of 2–3 inspection subagents
- Complete Phase 4 unification (this is main-agent work, reasonable as one iteration)
- Write Phase 5 plan

End each iteration by: updating `docs/worklog.md`, committing, and stating what the next iteration should do.

### Subagent Best Practices
- Give each subagent a clear, self-contained prompt with all context it needs.
- Include the content of the dataset's `docs/datasets/<name>.md` in the prompt so it has all context without re-discovering.
- Set realistic timeouts — some downloads are large.
- Subagents must write their results into the dataset's doc — this is how the main agent and future sessions find the work.
- Run subagents in parallel where there are no dependencies between datasets — but **never more than 2–3 at a time** (see Pacing above).
