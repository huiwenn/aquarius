# Scaling to more regions, genres, countries and sources

## Orchestration pattern that worked

- **The coordinator** (main agent) owns decisions, the research log, the benchmark and verification. It writes
  shared utilities *before* dispatching agents, so agents don't each reinvent them: the search helper, the
  evaluator and the melody-alignment module.
- **Parallel agents** for independent work:
  - curation: one agent per 5 classes; 3 agents did 15 regions in ~12–17 min each
  - model setup: one agent per model family, each with its own env, runner script under
    `src/transcription/models/<model>/`, benchmark run and a report covering leakage and timing
  - the documentation skill
- **What to put in every agent prompt:**
  - exact paths
  - which env and conda to use (arch!)
  - what not to touch (don't edit the research log; the coordinator merges)
  - output schema
  - keep all code in the repo
  - report format: numbers, pitfalls, commands
- **Verify agent output yourself.** Check leakage claims, rerun scores and audit `git status`, especially when a
  safety check was unavailable during an agent's run.
- **Don't trust agent-shared scratchpads.** Two agents overwrote the same `build.py`.

## Idempotency everywhere

- Every stage skips outputs that exist: separation, GAME (patched), ROSVOT, YourMT3+, MusicXML, F0.
- Manifests are rebuilt from disk (`--manifest-only`), never from in-memory state.
- Staging uses symlinks, tolerating `FileExistsError` (concurrent stagers).
- Delete known-bad partial outputs before rerunning: empty MIDIs, killed runs' files, stray fallback outputs.

## Long-running loops

- `follow_downloads.sh`:
  - while the downloader lives: rebuild the manifest → `run_all.sh` → sleep 15 min
  - then a final pass + index
  - it detects the downloader with `pgrep -f "download_curated.py --min-sleep"`, so launch retries with the same
    flag if they should be followed
- Use `nohup` for anything over ~10 min so it outlives the orchestrator's tool calls. Monitor with cheap counters
  (`grep -c '] ok' log`, `find … -name '*.mid' | wc -l`) rather than tailing huge logs.
- Don't leave `until grep …` waiters on runs you've killed. They never finish and block completion checks.

## What to parameterize for a new corpus

| Knob | Worked example | Change for … |
|---|---|---|
| Taxonomy files | `data/regions/<region>.json` (15) | other countries' regional styles, genres, ethnic groups |
| Target / over-curation | 30 / 40 | keep the ~1.33× buffer |
| Query language & vocabulary | Chinese genre terms (信天游, 花儿, 号子 …) | local-language genre names, famous tradition-bearers, archive channels |
| Exclusion list | composed folk-style songs, 广场舞, 粤剧 … | the local equivalents (pop arrangements, tourist shows) |
| Duration window | 60–720 s | a longer max for epic/long forms, with segmenting |
| Source | YouTube (ytsearch) | archives, Bilibili (needs WBI signing), Zenodo datasets |
| Transcriber | GAME zh + htdemucs | re-benchmark with a control set in or near the target language |
| Score references for audit | Anthology (10 provinces) | any regional score corpus; map its volumes to your classes |

## Budget

For 600 recordings on one M1 Pro:
- curation: ~15 min with 3 agents
- downloading: ~14 h throttled
- transcription: finished in parallel with the downloads
- model selection (6 models, 4 agents): ~1.5 h

Downloading dominates, so start it as early as possible and pipeline everything behind it.
