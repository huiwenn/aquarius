# Work log / handoff — 色彩区 folk-song audio dataset, transcription, region classification

Last updated 2026-10-01 18:10 PT. Written for picking the work up in a new session or account.

## Where the full history lives
- **Session transcript** (the session that did all the 色彩区 audio work, 2026-09-28 → 2026-10-01):
  - `data/session_logs/2026-10-01_b53a1eb7-…/transcript_readable.md` — the readable version: user messages, Claude's replies, one line per tool call.
  - `transcript.jsonl` — the raw transcript.
  - `subagents/` — every subagent's transcript.
  - `data/` is gitignored, so copy this folder manually if you move machines.
- **Docs, each a running log of its topic:**

| Doc | Content |
|---|---|
| `docs/transcription.md` | v1 collection (YouTube, bot-wall handling), transcription model research and benchmark, pipeline, critic, in-domain audit (§1–7) |
| `docs/region_classification.md` | Part I: representation exploration (§0–11). Part II: reviewer-style ablations, stats, transfer, resynthesis, confounds, clustering, nested CV, song dating, strict protocol and official numbers (§12–22) |
| `docs/critiques.md` | Improvement directions, reviewer critiques, collection-v2 probe log |
| `docs/collection_v2.md` | **Current work.** v2 collection strategy, rules, schema, round 1 and 2 logs |
| `.claude/skills/regional-folk-audio-dataset/` | Repeatable skill: research → search → download → transcribe → audit |

## Status at handoff

### Done
- **v1 data:** 600 recordings, 40 per region across 15 regions, downloaded and transcribed. Index: `data/regions_transcription/dataset_index.csv` (primary transcription: GAME 3-run ensemble + post-processing).
- **Region classification:** official numbers use the strict channel+song protocol (`region_classification.md` §22).
  - T15 dual-view macro-F1 0.246; T5 0.443.
  - Anthology A5 0.62.
- **Song dating:** `data/regions_curated/song_dates/all_songs.csv` (18% of songs dated).
- **Collection v2 strategy:** `docs/collection_v2.md`. Curation rounds 1 and 2 were done by subagents.
  - The audited pool has 698 candidates in `data/regions_v2/candidates_clean/` (raw lists in `candidates/`).
  - Every region has 33–50 candidates and 18–40 channels.
  - No v1 channels are used, and no channel has more than 4 items per region.

### Download status (2026-10-02)
- v2 download is **complete**: 697 of 698 audited candidates are in `data/regions_v2/audio/`, with `data/regions_v2/manifest.csv` listing them. Only BV1hM4y1V7sd (西南高原) is missing.
- Per region: 赣 33, 西南高原 46, all others 45–50. `python src/secaiqu/v2/audit.py --manifest` gives the per-region rule table.
- Before downloading anything else: `pgrep -fl "v2/download.py"`. Never run two downloaders at once (shared IP; YouTube bot wall). The downloader is idempotent; `--retry-failed --player-client default` fixed YouTube 403s.

### Session 2026-10-02
- **Symlinks are now relative.** The repo was moved mid-run and every absolute staging symlink broke, which crashed separation. `transcribe_regions.py` and `select_primary.py` now write relative links. All 1,328 existing links under `data/` were converted, so the repo can move safely.
- **v2 separation is running** (`--steps sep`, log `data/regions_v2/logs/sep.log`, about 6 h). Rerunning it skips finished stems.
- **Speech screen:** `src/secaiqu/v2/speech_screen.py` (AudioSet-AST, 10 s windows, full mix). Output: `data/regions_v2/speech_screen/`, with v1 as the calibration reference in `data/regions_transcription/speech_screen/`. Log: `data/regions_v2/logs/speech_screen.log`.
  - A pitch-plateau heuristic was tried first and rejected: it flags recitative singing (太和清音, 木鱼歌, 童谣, 打鼓歌) as speech.

### Session 2026-10-02 (cont.) — paper and release
- **Paper:** TISMIR dataset article "Colour Regions" in `../colour_regions_paper/`.
  - `build.sh` regenerates numbers and tables from data, compiles, and reports words (limit 8,000 including references).
  - Scope, licence and hosting decisions are in memory (`project_paper_scope.md`): Colour Regions corpus plus the Anthology, merged v1+v2 pool, CC BY-NC-SA, Hugging Face + GitHub.
- **Release tables:** `src/colour_regions/build_release.py` writes `data/colour_regions/recordings.csv` and `scores.csv`.
  - The `core` flag excludes label errors, arrangements, composed songs and talk-heavy items.
  - Each recording gets channel-grouped folds and geocoding (`geocode.py` with gazetteer `data/geo/`).
  - Numbers for the paper: `paper_numbers.py`.
- **v1 re-curation:** `data/regions_curated/v1_provenance.csv` holds tiers, singers, dating and flags.
  - Review decisions are in `v1_label_review.csv` and `v1_content_review.csv`. The user still needs to confirm them.
- **Speech screen result:** AST "speech" also fires on unaccompanied folk singing. Core therefore uses a two-signal rule: speech ≥ 0.3 plus documentary metadata (24 items).
- **Pipeline bugs fixed:**
  - `separate.py` falls back to ffmpeg for m4a files that Core Audio can't decode.
  - `run_game.py` retries on MPS out-of-memory and writes `_processed.txt`.
  - `select_primary.py` / `instrumental_fallback` no longer read a crashed GAME run as "instrumental".
  - The 33 wrong YourMT3 outputs for 北方草原 were deleted.
- **Running:** v2 separation (`logs/sep2.log`) and `src/transcription/run_v2.sh` (GAME/ROSVOT passes → ensemble → select → index; log `logs/run_v2.log`).
  - Afterwards: `python src/regionclf/corpus.py --sources trans_merged`, then `src/regionclf/rev_merged.py` for the example study.
- **EDA:** `notebooks/04_colour_regions_corpus.py`, plus Part 2 of `notebooks/eda_writeup.md`.

### Session 2026-10-02 (cont. 2) — thesis, review, human checks
- **Thesis:** the author gave the paper thesis (`../colour_regions_paper/THESIS.md`): friction between the music, jianpu/Anthology notation and Western-trained AMT as a fingerprint of regional character; expert notator disagreement as the envelope; shared vs distinctive features as traces of contact.
- **Evidence rule:** no conclusions on friction, notation or interaction from automatic data. The plan, decided criteria and order of work are in `docs/thesis_evidence_plan.md`.
- **Exploratory probes, Round 1 automatic data:** aggregate friction and scale-degree intonation were both at chance under the strict protocol. They are logged in the plan as exploratory only.
- **Review 1:** `../colour_regions_paper/reviews/review_01.md`. Most data and text fixes are applied.
- **Release data fixes:**
  - Tiers are now A1/A2/B/C. A1 = singer on the national heritage list (`check_inheritors.py`): 34 of 143 tier-A recordings.
  - Singer pseudonyms (`singer_id`); names are released only for A1, and names are redacted from evidence text.
  - Folds are grouped by channel ∪ singer (`group_id`).
  - Generic genre titles get a per-item `song_key`.
  - `score_matches.csv`: 188 recordings match a score title, 61 of them in the same province.
  - Link check: 1,297/1,297 links alive on 2026-10-02 (`link_check.py`).
  - Fingerprints: compressed and raw (`fingerprints.py`).
  - Release downloader with verification: `download_release.py`.
- **Human tasks:**
  - Gold-set rating, by the author: https://claude.ai/artifact/2d22Duf8owkvFQFx4xvYUU
  - Optional label spot-check page (answers in its db collection `spotcheck`): https://claude.ai/artifact/LQgfcNr9y8sdnYY4huHzgL
  - Outsourced notation, 3 notators × ~20 excerpts: guideline `docs/annotation_guideline.md`, selection `src/annotation/select_excerpts.py`. Run the selection only after v2 F0 exists, then freeze it and log the sha256 in the plan. Package: `src/annotation/build_package.py`.
- **Paper:** restructured around the thesis.
  - Friction and interaction sections give the design only, with \authq placeholders.
  - The supplement has the datasheet, rules, mapping and review tables.

### Session 2026-10-02 (cont. 3): reviews, research report, study design
- **Review 02** (`../colour_regions_paper/reviews/review_02.md`): design-level critique.
  - Applied: definitions, the calibrated envelope, signal = inter > intra + debrief, the decision table (supplement S6), the contact-test redesign, a dataset-first title, and the overclaim rewrites.
- **Research report:** saved as `docs/research_report_secaiqu_measurable.md`.
  - Paper additions: §2 "Notation, transcription and the note" (Seeger, List, Stanyek, Holzapfel et al., Ozaki et al., Chiba et al., 沈洽 音腔, 董维松 润腔), the circularity caveat in §8.1, a third primary hypothesis (润腔 type → machine error category), and contact guardrails.
  - New references were checked on Crossref or Zenodo; 沈洽 and 董维松 only through search summaries (noted in the bib `verification` field).
- **Author decisions:**
  - About 45 excerpts, the same 3 notators, 3 blind repeats + 1 calibration excerpt.
  - Internal freeze (dated commit + sha256), with no OSF registration.
  - Title: dataset-first.
- **Annotation guideline** v1.1-draft rewritten; `docs/jianpu_examples.txt` created.
- **Selection script** redesigned: metadata-only eligibility, the dominant channel excluded, strata, by-ear windows, repeats and orders.
  - **Blocker:** free rhythm must be coded by ear first (`data/annotation/free_rhythm_candidates.csv`, 112 items). Metadata marks free rhythm almost only in the Northwest.
  - Not yet run, by design.
- **Paper:** 7,571 words (limit 8,000), with pending results left as `[result pending]`.
- **Citation agent hit the session usage limit;** citations were verified directly instead.

### Session 2026-10-03: Round 2 transcribed, merged results in
- **Round 2 transcription finished** (07:21): 695/697 transcribed, 38.7 h. 678 GAME 3-run ensemble, 11 ROSVOT, 8 YourMT3+. Index: `data/regions_v2/transcription/dataset_index.csv`.
- **Bugs fixed:**
  - `instrumental_fallback` now judges by the raw GAME output (47 wrong Hakka fallbacks removed).
  - `build_dataset_index` handles a relative `AQ_TRANS`.
  - `corpus.build_merged` keeps the core subset only and uses channel ∪ singer groups.
- **Merged core results** (`data/regionclf/review_merged.csv`; channel ∪ singer folds, song-disjoint, 3 seeds):
  - T15: dual-view 0.292 [0.277, 0.306], n-gram 0.265, theory 0.225; Δ dual−ngram +0.027, p = 0.0002.
  - T5: dual-view 0.460.
  - Tier A/B accuracy = tier C accuracy (0.31).
  - Accuracy: minority regions 0.54, Han regions 0.23.
- **Frozen Round 1 → Round 2 test:** T15 dual-view 0.252 (n-gram 0.232, theory 0.196); T5 about 0.31 for all models.
  - The all-items, channel-only run is kept as `review_merged_allitems_channelonly.csv` (not official).
- **Merged quality checks** (`data/transcription/audit/*_merged.csv`):
  - Score reference: 87 recordings, 0.53 vs 0.45.
  - Cross-performance: 164 pairs, 0.44 vs 0.26.
- **Paper:** §7, §8.1, abstract and conclusion updated; 7,736 words.
  - Remaining `[result pending]` items all need human work: label spot-check, gold set, friction study, contact test.
- **Figures:** regenerated by `src/colour_regions/after_v2.sh`.

### Next steps
1. ~~Finish the download.~~ Done (697/698).
2. **Screen for speech.** Curators flagged items that may contain narration in each item's `note` (非遗 promos, news, documentaries). Screen them with the critic's stem-dominance / vocal-activity check (`src/transcription/critic/stem_dominance.py`) and drop items that are mostly speech.
3. **Transcribe v2** with the same pipeline as v1, from a native arm64 shell:
   ```bash
   export AQ_MANIFEST=data/regions_v2/manifest.csv AQ_TRANS=data/regions_v2/transcription
   ~/miniforge3/envs/sep/bin/python src/transcription/transcribe_regions.py --models game,rosvot
   bash src/transcription/ensemble_dataset.sh
   python src/transcription/select_primary.py && python src/transcription/build_dataset_index.py
   ```
   The `AQ_*` env vars were added 2026-10-01. Without them, everything defaults to the v1 paths.
4. **Evaluate once.** v2 is a frozen external test set.
   - Train on v1 (+ scores) exactly as in `region_classification.md` §22 and predict v2.
   - Report overall, for the tier A+B subset, and for minority vs Han regions.
   - Add a v2 corpus builder in `src/regionclf/corpus.py`. The records need `source` starting with "trans".
5. **Open decisions:**
   - Allow up to 6 items per channel for **institutional archive** channels? 赣鄱声像档案馆 has 3 more good 赣 field items; see `collection_v2.md` round-2 log.
   - 赣 has 33 candidates; platform search is exhausted. Other sources: the 赣鄱声像档案馆 website, 语保 recordings.
6. **Pending from earlier:**
   - Rate the listening gold set (https://claude.ai/artifact/2d22Duf8owkvFQFx4xvYUU).
   - F0 ornamentation (润腔) view for dual-view.
   - Tune-family analysis (茉莉花, 孟姜女, …) — see `critiques.md` §1.

### Session 2026-10-04: Musical Map of China, feature flags, notator page

**Author decisions (2026-10-04):**
- The Musical Map of China channel (中国音乐地图 / 瑞鸣音乐 Rhymoi, YouTube `UCN19zbpNCX9lrbKreffuSAQ`) is a good source and is **no longer capped**. Its items go into the **main pool**, marked in a new semantic-flags column.
- **Tier by stated area:** a named singer plus one stated county → A2; province or prefecture only → C; heritage bearers → A1 as usual. This replaces the 2026-10-02 decision "Rhymoi items stay tier C".
- **Notator page:** an offline `index.html` inside each private package, not a hosted artifact (the audio is third-party).

**Done:**
- `src/colour_regions/rhymoi.py` parses the series descriptions (体裁, 民族, 地区, 演唱, instruments) into `data/rhymoi/rhymoi_items.csv`. It adds a rule-based region with `needs_review`, an area level, a tier and the flags.
  - On the 181 Round 1 items, the rules agree with the curators' regions 100% where no review is flagged. Disagreements are Anhui south (curators: Jiangsu–Zhejiang Plain) and Hunan Miao/Tujia (curators: Xiang); both are flagged for review.
- `build_release.py`:
  - adds the column **`feature_flags`** (`series:musical_map_of_china; accompanied|unaccompanied; instrument:<x>; multiple_singers; song_and_dance`);
  - fills singers and genre from the descriptions;
  - upgrades 52 Rhymoi items from C to A2 (`provenance_tier_curator` keeps C);
  - **`singer_id` is now a hash of the normalised name** (`S` + 8 hex characters). The old sequential `S0001` ids shifted whenever a singer was added. This changes every `singer_id`, `group_id` and `fold` in `metadata/` (not yet committed).
  - The column is named `feature_flags`, not `flags`, because `DataFrame.flags` is a pandas attribute.
- `export_metadata.py` and `metadata/README.md` include `feature_flags`; the release, metadata and corpus view are rebuilt.
- **Channel catalogue:** `data/rhymoi/channel_flat.json` and `channel_titles.csv` list 1,599 videos.
  - About 667 have song-like titles; 168 of those are already in the corpus.
  - About 590 are instrumental or opera by title.
- **Metadata fetch running:** `src/colour_regions/rhymoi_fetch.py` fetches 833 videos (song-like titles first), paced at 45–90 s, no cookies, no audio, so about 15 h. Log: `data/rhymoi/fetch.out`. It is resumable: rerun the same command. Some videos are "not available" and are skipped on rerun.
- **Notator page:** `src/annotation/portal_template.html` plus `build_package.py`, which now builds one folder per notator: `index.html`, `audio/E##_{mix,voice,guide}.wav`, the guideline and the jianpu examples.
  - The page has: consent; the background form; the excerpt list in the notator's order; a player with the excerpt window, loop and speed; a session timer with a 2 h cap; the notes form (the 4 required headings); a format check for `_jianpu.txt` and `_performance.csv` (links, grace overlap, steady spans, confidence, metre per bar); the debrief (load `debrief_N#.json`, code P/C/G/S); and export or restore as JSON plus per-excerpt `_notes.txt`.
  - Test with `python src/annotation/build_package.py --demo`, which builds `data/annotation_package_demo/` from 3 arbitrary core items. That folder is for testing only.

**Next:**
1. When the fetch ends, run `python src/colour_regions/rhymoi.py`, then review the eligible new items:
   - the `needs_review` regions (border provinces, minorities inside Han provinces);
   - sung vs instrumental;
   - composed songs.
2. Ask the author before downloading the audio of new items (paced, about 500 items), then transcribe them as Round 3 and add a `round3()` to `build_release.py`.
3. **Open question for the author:** `select_excerpts.py` excludes the "dominant Round 1 commercial channel" (Rhymoi) from the notation study. Keep that, or allow Rhymoi items now that the channel is valued?
4. Write the Chinese translation of the guideline body; the page UI is already bilingual.

### Session 2026-10-09: Round 3 candidates for Northern Steppe, Xinjiang and Tibetan (Olivia)

**Input:** 44 YouTube links from a curator's own search (Olivia), for Inner Mongolia, Xinjiang and Tibet. Every link was checked as live before the run.

**Done:**
- 14 of the 44 links are already in the release (Round 1). They were not added again.
- The 30 new links are in `metadata/pending/round3_candidates.csv`: 12 Northern Steppe, 10 Xinjiang, 8 Tibetan.
  - They are **not in `recordings.csv`** yet. `build_release.py` does not read the file, so the release numbers do not change.
  - The author decided to keep all 30 and mark them with flags instead of dropping them. New flags: `instrumental` (7 items), `documentary` (5), `compilation` (2), `filmed_in_mongolia` (2), `tv_performance` (1), `needs_review` (8).
- `src/secaiqu/round3/download_pending.py` downloaded all 30 audio files to `data/round3/audio/<region_code>/` (30/30 ok, 187 min, 188 MB). It used the same settings as `v2/download.py`: native audio, U(45, 90) s pacing, one process. It used **no browser cookies**. It wrote `data/round3/manifest.csv` and filled title, channel, channel_key, upload_date and duration_s in the pending list.
- **Not done: transcription.** The Mac used for this run has no separation or transcription environments (no `~/miniforge3/envs`) and little free disk space. Every item has `transcription_status: pending`.

**Rule conflicts to review (from `collection_v2.md` item rules):**
- Longer than 10 min: `eCulAKP9cPI` (38 min, compilation), `oS4CBOiLlHA` (13 min, compilation), `3NcQtIS0s1M` (10.7 min), `hV8EJOvvPvY` and `Sh73S0piXyA` (10.0 min each).
- Instrumental items: Northern Steppe has 4, Xinjiang has 1, Tibetan has 2, plus items flagged `needs_review` that may be instrumental. The rule allows at most 3 per region.
- `hV8EJOvvPvY` and `Sh73S0piXyA` were filmed in Mongolia (the country), which is outside the region's area.

**Next:**
1. On a Mac with the GPU environments, copy or re-download the audio (`python src/secaiqu/round3/download_pending.py` is resumable), then run the transcription pipeline (GAME ens3 + pp) on `data/round3/audio/`.
2. Review the `needs_review` items and the rule conflicts above. Then decide which items go into the release as Round 3, and add a `round3()` to `build_release.py`.

## Environment notes (this Mac)
- **Python envs:**
  - Analysis python: `/usr/local/Caskroom/miniforge/base/envs/py312/bin/python` — x86 under Rosetta, no MPS.
  - GPU/ML envs: arm64 under `~/miniforge3/envs/` (sep, game, some, ymt3, basicpitch, vocalparse, node, regionclf, regionseq, regionimg). `rosvot` is arm64 under the Caskroom conda.
  - Launch GPU pipelines from an arm64 python; child processes inherit the architecture.
- **Downloads:**
  - yt-dlp uses Firefox cookies.
  - The JS runtime is node at `~/miniforge3/envs/node/bin/node` (system node is broken).
  - Bilibili search: `src/secaiqu/v2/search.py --platform bili` uses the web API with homepage cookies. yt-dlp's `bilisearch` returns HTTP 412.
- **ihchina inheritor lookup:**
  - `curl -A "Mozilla/5.0" "https://www.ihchina.cn/art/representative.html?keywords=<name>"` returns JSON.
  - Slow; it sometimes times out.
  - Baidu Baike is captcha-blocked.
- **Budget:** WebSearch was exhausted in this session (200 calls). Five parallel Opus curation subagents used up a whole session's usage limit in about 20 minutes. Give subagents query budgets and have them write results incrementally.

## Uncommitted work
Nothing from this session's later work is committed. That includes `src/regionclf/`, `src/secaiqu/v2/`, `src/transcription/`, and the docs above. Run `git status`, then commit when ready.

---

# Earlier log (Phase 1–2, dataset registry and integration)


## [2026-09-15] Phase 1: Dataset Registry — Complete

Cataloged 38 datasets across 38 docs in `docs/datasets/`.

**CCMusic ecosystem (12 datasets):** CCMusic (umbrella), CSMTD (parent), GZ_IsoTech, GuZheng Midi-Wav, Chinese National Pentatonic Mode, PMEmo, Guzheng_Tech99, XFID, CTIS, ErhuPT, CCOM-HuQin, Guqin Dataset

**Singing voice (7):** Opencpop, M4Singer, KiSing, GTSinger, MADVSD (gated — PII), ACE-OpenCpop/ACE-KiSing, SongSong/OpenSongSong

**Beijing Opera / Jingju (7):** Singing Audio + Boundary, Phoneme Annotation, Annotated Arias, Pitch Contour, BOPP, Music Corpus/Dunya (gated), Lyrics

**Folk music (5):** Anthology of Chinese Folk Songs, Anonymized Subset, MGD, Chinese Folk Songs Symbolic, FolkMusic/Zenodo

**Pop / general (4):** POP909, ChMusic, Chinese Songs MIDI, Traditional Chinese Folk Music (Kaggle)

**Opera — other (1):** CODS (Cantonese Opera)

**Other (2):** Chinese Music Archive (gated — website), Chinese Chorales

**Status summary:** 30 ready, 5 gated/unclear (MADVSD, Jingju Music Corpus, Chinese Music Archive, CODS, SongSong), 3 unclear (KiSing, Chinese Chorales, Kaggle folk)

**Discovery:** Searched "Chinese music dataset MIR", "中国音乐数据集", HuggingFace/Zenodo/GitHub, citation snowballing. All AquariusDatasets.md entries cataloged. Broad searches returning only already-cataloged datasets. Discovery complete.

**Next:** Phase 2 — download all `ready` datasets.
