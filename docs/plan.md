# Aquarius: Unified Chinese Music Dataset — Execution Plan

## Project Goal

Build a **complete, gap-filled unified database** of Chinese music datasets for a TISMIR Dataset Article (deadline: 2026-12-01). The deliverable is a single dataset where every entry has all columns populated — either from source data or via imputation/generation. The paper documents the taxonomy, curation process, gap analysis, and gap-filling methodology.

**Scope**: All Chinese music — traditional through contemporary (folk, opera, instrumental, C-pop, Mandopop, rock, guofeng, etc.).

See `docs/chinese_music_taxonomy_reference.md` for the musicological lens guiding categorization.

---

## Phase 1: Dataset Registry & Metadata Catalog

**Owner**: Main agent

**Goal**: Build a structured registry of every known Chinese music dataset before downloading anything. This is the map before the territory.

### Instructions

1. Start from `AquariusDatasets.md` which lists known datasets and URLs.
2. For each entry, use WebFetch and WebSearch to visit the dataset's homepage, paper, or GitHub repo. Extract:
   - **Name**: Official dataset name
   - **Source URL(s)**: Where to access/download it
   - **Paper**: Associated publication (if any)
   - **Access method**: How to get the data (direct download link, git clone, Kaggle API, HuggingFace, gated access requiring a form, manual email request, scraping needed, etc.)
   - **Known modalities**: What data representations are included (audio formats, MIDI, MusicXML, jianpu, lyrics, metadata CSVs, etc.)
   - **Reported size**: Number of items, total file size if stated
   - **License**: Stated license or access terms
   - **Content description**: What kind of music is in it (genre, instruments, era, region — whatever the source says)
   - **Status**: `ready` (can download now), `gated` (need to request access), `dead` (link broken), `unclear`
3. Search for additional Chinese music datasets not in `AquariusDatasets.md`. Search queries to try:
   - "Chinese music dataset MIR"
   - "Chinese traditional music corpus"
   - "中国音乐数据集" (Chinese-language searches)
   - "Chinese music audio MIDI dataset"
   - Check papers that cite the datasets we already know (snowball search)
   - Check HuggingFace, Kaggle, Zenodo, and GitHub for Chinese music datasets
4. Save the registry as `data/dataset_registry.json` — a list of objects, one per dataset. Also save a human-readable summary as `docs/dataset_registry_summary.md`.
5. Commit `docs/dataset_registry_summary.md` (the JSON is in data/ which is gitignored).

### Guidelines

- Be thorough. A dataset paper's value scales with coverage. Missing a major dataset is worse than including a minor one.
- If a dataset URL is dead, search for mirrors or archived versions (Wayback Machine, alternative GitHub forks).
- Some datasets are subsets of larger ones (e.g., CSMTD contains multiple sub-databases). Record both the parent and children as separate entries if they can be used independently.
- When a paper describes a dataset but doesn't provide a download link, still record it with status `gated` or `unclear` — we want to document the landscape even if we can't get everything.

---

## Phase 2: Download & Ingest

**Owner**: Subagents (one per dataset or small batch)

**Goal**: Download every accessible dataset into `data/raw/<dataset_name>/`.

### How to Dispatch Subagents

The main agent should:
1. Read the registry from Phase 1.
2. Group datasets by access method complexity:
   - **Simple**: Direct HTTP download, git clone, pip/kaggle/huggingface CLI — these can be batched.
   - **Complex**: Requires scraping, navigating a website, filling out forms, handling CAPTCHAs, dealing with Chinese-language UIs, or writing custom download scripts.
3. Spawn subagents in parallel where possible. Give each subagent:
   - The dataset name and all known URLs
   - The access method from the registry
   - The target directory: `data/raw/<dataset_name>/`
   - Instructions to save a download manifest at `data/raw/<dataset_name>/_manifest.json` documenting what was downloaded, file counts, total size, any errors.

### Subagent Instructions (include in each subagent prompt)

You are downloading a Chinese music dataset. Your job:

1. **Figure out how to get the data.** The access method in the registry is a starting hint, not gospel. You may need to:
   - Clone a git repo
   - Use `kaggle datasets download` or `huggingface-cli download`
   - Write a Python script using requests/BeautifulSoup/selenium to scrape download links
   - Navigate a Chinese-language website (read the HTML, follow links, find the actual download)
   - Download from Google Drive, Baidu Pan, or other cloud storage
   - Handle zip/tar extraction
2. **Download into `data/raw/<dataset_name>/`.** Preserve the original directory structure.
3. **Don't modify the data.** Download as-is. No renaming, no reformatting.
4. **Write `data/raw/<dataset_name>/_manifest.json`** with:
   ```json
   {
     "dataset_name": "...",
     "download_date": "YYYY-MM-DD",
     "source_urls": ["..."],
     "method": "description of how you downloaded it",
     "files_downloaded": 123,
     "total_size_bytes": 456789,
     "file_types": {".wav": 100, ".mid": 20, ".csv": 3},
     "errors": ["any issues encountered"],
     "notes": "anything relevant"
   }
   ```
5. **If you can't download it**, still write the manifest with `"files_downloaded": 0` and explain why in `errors`. Don't silently fail.
6. All download scripts you write go in `src/downloaders/`. Name them by dataset. Keep them — they're part of the reproducibility story for the paper.

### Main Agent Verification

After subagents complete:
1. Check every `_manifest.json`. Verify file counts match what's actually on disk (`find data/raw/<name> -type f | wc -l`).
2. Spot-check a few files from each dataset (can you open an audio file? does the CSV parse?).
3. Update the registry with actual download status and corrected metadata.
4. Flag datasets that failed and decide whether to retry with a different approach or mark as inaccessible.
5. Commit any new code in `src/downloaders/` and updated docs.

---

## Phase 3: Inspect & Schema Discovery

**Owner**: Subagents (one per dataset)

**Goal**: Profile every downloaded dataset to discover what fields, modalities, and metadata exist. The superset of all discovered features becomes the unified schema.

### How to Dispatch Subagents

Spawn one subagent per downloaded dataset. Give each:
- The dataset path: `data/raw/<dataset_name>/`
- The registry entry for that dataset (for context)
- Target output: `data/profiles/<dataset_name>_profile.json`

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
   - Genre/form?
   - Instruments?
   - Composer/performer?
   - Time period/dynasty?
   - Region/province?
   - Ethnic group?
   - Mood/emotion?
   - Key/mode/scale?
   - Tempo/rhythm?
   - Language (for vocal music)?
   - Any other labels?
5. **Note anything unusual or dataset-specific**: custom file formats, annotation conventions, encoding issues (Chinese character encodings — watch for GB2312/GBK vs UTF-8), README contents.
6. **Write a Python inspection script** at `src/inspectors/<dataset_name>_inspect.py` that produces the profile. Keep it — it's part of reproducibility.
7. **Save the profile** to `data/profiles/<dataset_name>_profile.json`:
   ```json
   {
     "dataset_name": "...",
     "inspection_date": "YYYY-MM-DD",
     "total_files": 123,
     "total_size_bytes": 456789,
     "file_type_counts": {".wav": 100, ".mid": 20},
     "entry_count": 100,
     "entry_unit": "song",
     "modalities_present": ["audio_wav", "midi", "metadata_csv"],
     "modalities_missing": ["score", "lyrics"],
     "metadata_fields": {
       "source_file": "songs.csv",
       "columns": {
         "title": {"type": "string", "example": "茉莉花", "missing": 0},
         "genre": {"type": "string", "example": "folk", "unique_values": ["folk", "opera", "pop"], "missing": 2}
       }
     },
     "taxonomic_coverage": {
       "genre": true,
       "instrument": true,
       "composer": false,
       "time_period": false,
       "region": true,
       "ethnic_group": false,
       "mood": false,
       "key_mode": true,
       "tempo": false
     },
     "encoding_notes": "UTF-8, no issues",
     "other_notes": "..."
   }
   ```

### Main Agent Verification

After inspection subagents complete:
1. Read all profiles from `data/profiles/`.
2. **Build the unified schema**: take the union of all `metadata_fields` across all datasets. Every field that appears in any dataset becomes a column. Add standard fields that the taxonomy reference suggests even if no dataset has them yet — these are the gaps to fill.
3. Save the unified schema as `data/unified_schema.json` and a readable version as `docs/unified_schema.md`.
4. Produce a **coverage matrix**: datasets (rows) × schema fields (columns), with cells showing present/partial/missing. Save as `data/coverage_matrix.csv` and a visualization.
5. Commit inspection scripts and schema docs.

---

## Phase 4: Unify & Gap Analysis

**Owner**: Main agent

**Goal**: Merge all datasets into one master table using the unified schema, and produce a detailed gap report.

### Instructions

1. Write `src/unify.py` — a script that:
   - Reads every dataset's raw data and its profile
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
   - Dataset × modality heatmap
   - Dataset × metadata coverage heatmap
   - Temporal distribution of entries across datasets
   - Genre distribution
   - Modality distribution (pie/bar)
6. Commit all code and docs.

### Guidelines

- The master table will likely have thousands of rows and dozens of columns. Use parquet for the working format (efficient, typed), CSV only for human inspection of samples.
- Don't force every dataset into identical granularity. Some datasets have one row per song, others per phrase or per note. Record the granularity level and handle aggregation carefully.
- When field names differ but mean the same thing (e.g., "artist" vs "performer" vs "演奏者"), map them to one canonical name. Keep a mapping table for reproducibility.
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

### Data Organization
```
data/
├── dataset_registry.json          # Phase 1 output
├── raw/                           # Phase 2 output
│   ├── <dataset_name>/
│   │   ├── _manifest.json
│   │   └── ... (original files)
├── profiles/                      # Phase 3 output
│   ├── <dataset_name>_profile.json
├── unified/                       # Phase 4 output
│   ├── master_table.parquet
│   ├── master_table_sample.csv
│   ├── gap_report.json
│   └── coverage_matrix.csv
└── figures/                       # Visualizations
```

### Git Discipline
- Commit code and docs frequently. Data is gitignored.
- Commit messages should say what phase/dataset the work covers.
- Don't commit large data files, audio, or binary blobs.

### Error Handling
- Network failures, encoding errors, and malformed data are expected. Handle gracefully.
- Always log what went wrong. Never silently skip a dataset.
- If a download or inspection fails, record the failure and move on — don't block the whole pipeline.

### Chinese Language Handling
- Expect GB2312, GBK, Big5, and UTF-8 encodings. Try UTF-8 first, fall back to others.
- Preserve original Chinese text. Add translations/romanizations as extra fields.
- Some READMEs and metadata will be in Chinese only — read and process them.

### Subagent Best Practices
- Give each subagent a clear, self-contained prompt with all context it needs.
- Include the dataset's registry entry in the prompt so it doesn't have to re-discover basic info.
- Set realistic timeouts — some downloads are large.
- Subagents should write their results to well-defined file paths so the main agent can find them.
- Run subagents in parallel where there are no dependencies between datasets.
