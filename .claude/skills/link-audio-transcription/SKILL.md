---
name: link-audio-transcription
description: Robust, verifiable pipeline for downloading audio from web links (YouTube, Bilibili, archive/Europeana MP3s) and transcribing singing to MIDI/MusicXML and F0 at scale, then releasing it as a link-based dataset (links + derived data, no audio). Covers yt-dlp pacing and bot walls, Bilibili cookies and undecodable m4a files, link-availability checks, Chromaprint fingerprints for verifying re-downloads, decode fallbacks, vocal separation, crash-safe multi-model transcription runs (GAME/ROSVOT/YourMT3+, run ensembles, offset trim), speech screening pitfalls, and the bookkeeping that keeps long GPU jobs from silently corrupting outputs. Use this skill whenever the user wants to bulk-download music or speech audio from video platforms or archives, check or re-verify a list of media links, transcribe recordings (singing, folk, field recordings) to notes or pitch tracks, run or resume a long separation/transcription job, or publish a dataset of links with derived annotations — even if they only mention one step, such as "grab these Bilibili videos", "are these links still alive", or "transcribe this folder".
---

# Link audio → verified downloads → transcription → link-based release

This skill condenses a working pipeline that took ~1,300 folk-song recordings from YouTube, Bilibili and an
archive to separated vocals, F0 tracks and note transcriptions over several days on one Apple-silicon laptop.
Most of its value is in the failure modes: several bugs produced plausible-looking wrong outputs, not crashes.

Companion skill: `regional-folk-audio-dataset` covers curation and search (what to collect), transcription model
benchmarking in depth, and auditing transcriptions without ground truth. This skill covers the mechanics around it:
getting files reliably, processing them without silent corruption, and releasing them responsibly.

## The five stages

| Stage | Goal | Read |
|---|---|---|
| 1. Links in | Every ID comes from a logged search or a source list, never from memory | below |
| 2. Download | Native audio, paced per platform, idempotent, manifest rebuilt from disk | `references/platforms.md` |
| 3. Decode and preprocess | Every file decodable; separation; speech handled honestly | `references/processing.md` |
| 4. Transcribe at scale | Crash-safe runs where "missing" never means "empty" | `references/processing.md`, `references/failure_modes.md` |
| 5. Verify and release | Link status, fingerprints, relative paths, privacy, no audio | `references/release.md` |

Read `references/failure_modes.md` before launching any long job. Each entry there cost hours in the worked example.

## Core principles (and why)

1. **Links come from searches you logged, not from a model's memory.** Language models write plausible but
   nonexistent video IDs; in the worked example, none of 60 recalled links for two regions existed. Store every
   query and all its results (JSONL) so each item traces to a search hit.
2. **One download process per IP.** Parallel downloaders trigger IP-level bans that cookies do not lift. Interleave
   platforms in one process so slow YouTube pacing overlaps fast Bilibili work.
3. **Keep native audio and decode with ffmpeg.** Do not transcode at download time. Some Bilibili m4a files cannot be
   decoded by libsndfile or macOS Core Audio ("Format not recognised", `MacError 1650549857`) but ffmpeg reads
   them. Every consumer that loads audio needs an ffmpeg fallback (`scripts/decode.py`).
4. **"No output file" is not "no notes".** A crashed or interrupted model leaves files missing; a fallback rule that
   treats a missing file as "nothing found" silently replaces good transcriptions. Record which inputs a model
   *processed* successfully (a `_processed.txt` per output folder) and decide fallbacks only for processed inputs.
   Judge from the raw model output, not a post-processed copy that may not exist yet.
5. **Rebuild state from disk, and make every step idempotent.** Manifests, indexes and selections are recomputed from
   files on disk, never from in-memory status after an interruption. Every step skips existing outputs, so a rerun
   resumes.
6. **Sanity-check stage counts and fallback rates after every stage.** Plausible-looking bugs show up as anomalous
   rates: 33 of 46 recordings in one region sent to an "instrumental" fallback, or 48 of 48 in another. Use
   `scripts/stage_report.py` and compare against expectations (in a vocal corpus, instrumental fallbacks should be a
   few percent at most).
7. **Release links and derived data, not audio, and make re-downloads verifiable.** Store duration and a Chromaprint
   fingerprint per item, check link availability at each release, and keep repo paths relative so the project can move.

## Stage 1: links in

- Candidate record: platform, id, url, title, channel and **channel id** (display names collide: deleted Bilibili
  accounts all show "账号已注销"), duration, the search query, and curation fields.
- Allow single-video URLs only. Playlist and channel URLs download everything.
- Bilibili search: use the web search API with homepage cookies (`references/platforms.md`). yt-dlp's `bilisearch`
  returns HTTP 412.
- YouTube search: `yt-dlp "ytsearchN:<query>"` with flat extraction works even while downloads are walled.

## Stage 2: download

Settings that worked (details and the evidence in `references/platforms.md`):

| Platform | How | Pace |
|---|---|---|
| YouTube | yt-dlp, `bestaudio/best`, Firefox cookies, Node JS runtime, `noplaylist`, `writeinfojson` | 45–90 s between items; 1 h cooldown on "Sign in to confirm you're not a bot" |
| Bilibili | yt-dlp, `bestaudio/best` (m4a), Firefox cookies | 8–20 s |
| Archive MP3 (e.g. Europeana/CREM) | direct HTTP GET of the media URL | 3–8 s |

- **Retries:** most failures are transient. A plain retry with the default player client
  (`--retry-failed --player-client default`) recovered all YouTube 403s. Do not retry with the `tv` client: it causes
  "The page needs to be reloaded". Truncated Bilibili streams can fail three times in a row; record them as failed.
- **Manifest:** write `manifest.csv` from disk after every run (`status`, `error`, `audio_path`, actual duration).

## Stage 3: decode and preprocess

- **Decoding:** use `scripts/decode.py` (`load_audio(path, sr)` via ffmpeg) anywhere audio is read. Separation tools
  that read files themselves need a fallback: on a decode error, convert to WAV with ffmpeg and retry
  (`references/processing.md` has the patch).
- **Vocal separation:** htdemucs matched BS-RoFormer for downstream transcription at a fraction of the time. Sum the
  non-vocal stems as accompaniment.
- **F0:** RMVPE (on CPU in the ROSVOT env) plus PESTO with confidence; keep both. Agreement between them is much lower
  on field recordings than on studio benchmarks. That is mostly soft singing, not bleed.
- **Speech screening:** an AudioSet classifier (AST) detects real speech, but it also scores unaccompanied
  traditional singing (elderly singers, work chants, children's songs) as speech. A pitch-stability heuristic fails
  the same way on recitative genres. Do not drop items on one signal. Require speech share ≥ 0.3 **and** metadata
  that marks documentary, news or interview content, and release the window scores.

## Stage 4: transcribe at scale

- **Model choice:** pick on a benchmark subset annotated independently of every model's training data, and report
  onset bias. The companion skill has the full comparison. In the worked example, GAME (medium, seg 0.1) won on
  vocadito; ROSVOT looked best only on data it was trained on.
- **Improvements that held up:** a 50 ms offset trim for GAME (chosen by cross-validation), and a 3-run majority-vote
  ensemble, because GAME's decoder is stochastic (single runs agree on only ~84% of notes).
- **Running it:** use an orchestrator script (`scripts/pipeline_template.sh`) launched with nohup from a native arm64
  Python. It runs CPU work (ROSVOT, RMVPE) in parallel with GPU work, repeats passes over finished regions while
  separation continues, and only then ensembles, selects the primary transcription and builds the index.
- **GPU memory:** concurrent MPS jobs (separation + transcription + a classifier) caused GAME out-of-memory crashes
  mid-folder. The runner should retry the missing outputs with batch size 1, and record processed inputs.
- **Do not edit a running bash script** except below the line bash is currently executing; bash reads scripts
  incrementally.

## Stage 5: verify and release

- `scripts/link_check.py`: tests every link (YouTube oEmbed; Bilibili via yt-dlp metadata extraction, because the
  web API needs signed requests; HEAD for archives) and appends dated results.
- `scripts/fingerprints.py`: Chromaprint (`fpcalc`) compressed and raw fingerprints of the first 120 s.
  `scripts/verify_download.py` compares a user's copy by duration (±2 s) and bit error rate (≤ 0.25).
- Paths: write relative symlinks and repo-relative paths in indexes. An absolute-path staging folder broke when the
  repo was moved mid-run.
- Privacy and licensing: release names only for people with a public role, give others pseudonymous IDs, redact
  names from free-text evidence, keep source titles as published, and state the licence of derived data. Details:
  `references/release.md`.

## Before you hand results over

Run `scripts/stage_report.py` (counts per stage, fallback rates per group, missing outputs) and read it. Report
failures and anomalies explicitly, with counts. Several bugs in the worked example were found only this way.
