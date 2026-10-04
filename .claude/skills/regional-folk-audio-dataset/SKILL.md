---
name: regional-folk-audio-dataset
description: End-to-end playbook for building a curated, transcribed audio dataset of regional or genre music (folk songs, traditional music, ethnic/minority repertoires) from YouTube or similar web sources — research-driven curation via search, rate-limit-safe downloading, vocal separation, audio-to-MIDI/MusicXML transcription with model selection on an honest benchmark, and auditing transcription quality without ground truth. Use this skill whenever the user wants to collect N songs per region/style/ethnic group, download music audio in bulk from YouTube/Bilibili, transcribe singing or folk recordings to MIDI or sheet music, pick or benchmark a transcription model, audit/critique/correct existing transcriptions, or extend the Aquarius 色彩区 dataset to new regions, countries or genres — even if they only mention one of these stages.
---

# Regional folk audio dataset: research → search → download → transcribe → audit

This skill captures a process that was run end to end on the Aquarius project: 15 Chinese folk-song
regions (11 Han 色彩区 + 4 minority regions) × 40 recordings = 600 recordings, 32.6 h, every one
transcribed to MIDI + MusicXML. The research log is `docs/transcription.md`; all code lives in
`src/secaiqu/` (collection) and `src/transcription/` (transcription, critic, audit). Treat that project as the
worked example. The playbook is meant to transfer to other countries, genres, sources and transcription targets.

**Companion skill:** `link-audio-transcription` has the download mechanics for Bilibili and archives, the decode fallbacks, crash-safe transcription runs, the catalogue of failure modes (silent fallback bugs, MPS out-of-memory, path problems), link checks, fingerprints and link-based release. Read it before any long download or transcription run.

The five phases are sequential, but phases 3–5 overlap in practice: transcription follows downloads as
they land. Each phase has a reference file with the details, numbers and failure modes. Read the one for the
phase you're in, not all of them.

| Phase | Goal | Read |
|---|---|---|
| 0. Environment | Correct arch/GPU envs before anything heavy | `references/environment.md` |
| 1. Research & curation | A ranked, verified candidate list per region | `references/curation_and_search.md` |
| 2. Download | Audio + provenance, without getting the IP walled | `references/downloading.md` |
| 3. Transcription | Best model chosen on an honest benchmark, run at scale | `references/transcription.md` |
| 4. Audit & correct | Quality estimates in-domain, not just on the benchmark | `references/auditing.md` |
| 5. Scale out | More regions/genres/sources, parallel agents | `references/scaling.md` |

Exact commands for every script are in `scripts/commands.md`. `scripts/run_pipeline.sh` chains the stages with
sanity checks between them.

---

## Principles that held up (read these first)

1. **Never trust links from memory or a previous LLM pass.** Of the 453 links originally collected, ~86 were
   dead and none of the 60 湘/赣 IDs appeared in any search result, so they were most likely fabricated.
   Get candidate IDs *only* from live search (`yt-dlp "ytsearchN:<query>"`, metadata only), and log every query.
2. **Single videos only.** Playlist and channel URLs silently download whole collections: 92 files landed in one
   region, and only 1 was usable. Reject any URL that isn't `watch?v=` / `youtu.be/`.
3. **Download slowly.** Six parallel workers got the IP bot-walled after ~150 downloads, and a later burst of ~85
   triggered it again even with cookies. The wall lasted hours. One worker with 45–90 s randomized gaps ran
   ~400 downloads with no wall at all. Budget ~45 downloads/hour.
4. **Over-curate: 40 candidates for a target of 30.** Downloads fail, and some items turn out instrumental or
   off-topic. With 40 ranked candidates every region finished at 40/40 after the fallbacks.
5. **Choose models on a benchmark you have stress-tested for leakage and labelling convention.** On
   M4Singer/GTSinger, ROSVOT looked 3× better than everything else (COnP 0.72 vs 0.25). It had been trained on
   M4Singer and shares that lab's labelling convention (notes start at the consonant). On an independently
   annotated set (vocadito) it fell to 0.26 while GAME scored 0.59, against 0.72 human agreement. Always add a
   control set annotated by someone else, and report onset bias.
6. **The benchmark is not the dataset.** Studio pop vocals with synthetic mixes are nothing like field
   recordings of 长调, 花儿 or 侗族大歌. Use the benchmark to *choose* tools. Estimate *quality* in-domain with
   reference-free checks (phase 4) and a small human-audited gold set.
7. **Separate before transcribing vocals.** With accompaniment, GAME drops from 0.59 to 0.53 COnP. htdemucs
   separation restores it to 0.587 and runs 7–15× faster than BS-RoFormer (25 s vs 370 s for a 152 s song on an
   M1 Pro).
8. **Make every stage idempotent and resumable.** Skip existing outputs, rebuild manifests from disk, and allow
   stages to be killed and rerun. Long runs *will* be interrupted: bot walls, classifier outages, killed processes,
   architecture mistakes.
9. **Keep all code and a research log.** Every script used went into the repo, and every decision (with its numbers)
   went into the log. That is what makes the dataset reproducible for a paper.

---

## Phase 0 — Environment (15 min, saves hours)

On Apple Silicon, check the architecture of every Python env before installing torch. In the worked example
the default conda was x86_64 under Rosetta, so torch had **no MPS**. Worse, any arm64 process *launched from* that
x86 Python inherited i386 and silently fell back to CPU: separation took 278 s instead of 53 s for one song.
Create GPU envs in a native arm64 conda, and launch GPU pipelines from an arm64 Python. Per-model device quirks
(ROSVOT gives wrong output on MPS; YourMT3+ is faster on CPU) are in `references/environment.md`.

## Phase 1 — Research & curation

1. **Define the taxonomy** (regions, genres, ethnic groups) with a short description, representative songs and
   typical genres per class. The worked example used one JSON per region in `data/regions/`.
2. **Dispatch one curation agent per 3–5 classes.** Each agent runs search-only queries through
   `src/secaiqu/search_candidates.py`, which appends every query and hit to a shared `search_log.jsonl`. It then
   writes a ranked list of **40** single-video candidates per class to `data/regions_curated/<class>.json` with:
   rank, video_id, url, title, channel, duration, song_name, area, genre, performance_type, ethnic_group,
   source_query, already_downloaded, note.
3. **Curation rules** (full lists in the reference):
   - 60–720 s long, ≤3 recordings per song
   - field/tradition-bearer recordings ranked above stage 民族唱法
   - exclude pop/remix/广场舞/karaoke/tutorials/compilations and newly composed "folk-style" songs, except
     canonical representatives, which are flagged
   - assign straddling songs by the specific variant's origin
4. **Have agents save their builder scripts in the repo**, not a scratchpad. Two agents overwrote each other's
   builder in a shared scratchpad, and one region set's build logic was lost.
5. **Expect thin classes.** Some classes are flooded by adjacent genres (粤: 广东音乐 instrumentals, 粤剧) or lack
   field recordings (西南高原, 赣). The reference lists the channels that rescued them.

## Phase 2 — Download

Use `src/secaiqu/download_curated.py`:
- browser cookies (Firefox; Chrome stalls on the macOS keychain prompt)
- 1 worker, 45–90 s sleeps, regions visited round-robin
- Node JS runtime for yt-dlp challenge solving
- on "Sign in to confirm you're not a bot": a 1 h cooldown, then resume
- native best audio stream, no transcoding, `.info.json` kept for provenance

Then run `download_fallbacks.py` on whatever failed. In the worked example, 23 of 25 "failures" were transient
403s that a plain default-client retry fixed. The `tv` player client actively *causes* "The page needs to be
reloaded". Rebuild the manifest from disk at any time with `--manifest-only`. Details: `references/downloading.md`.

## Phase 3 — Transcription

1. **Benchmark before choosing.**
   - `build_benchmark.py` builds 160 clips with note-level GT: 60 M4Singer + 60 GTSinger-zh + all 40 vocadito.
   - `build_mix_benchmark.py` mixes each vocal with a Chinese-instrument excerpt at +3 dB.
   - `evaluate.py` reports COnPOff, COnP, COn, ±100 ms variants and median onset bias.
   - Add `human_A2` (a second annotator) as the ceiling.
2. **Candidates tried:** GAME, SOME, ROSVOT, VocalParse, YourMT3+, Basic Pitch. The winner for folk vocals was
   **htdemucs → GAME-1.0-medium (lang zh, seg-threshold 0.1) → 50 ms offset trim**. The trim was chosen by
   singer-disjoint CV: COnPOff 0.299 → 0.357.
3. **Run at scale.** `src/transcription/run_all.sh` puts separation + GAME on the GPU and ROSVOT on the CPU in
   parallel. `follow_downloads.sh` keeps transcribing while downloads continue.
4. **Instrumental fallback and primary selection.** Some "songs" turn out instrumental: GAME writes no MIDI or an
   *empty* one. `select_primary.py` applies explicit coverage rules: GAME by default, ROSVOT when GAME misses sung
   material, YourMT3+ on the full mix for instrumental(-dominant) recordings. Result in the worked example: 586
   GAME / 12 YourMT3+ / 2 ROSVOT.
5. **MusicXML** (`midi_to_musicxml.py`): beat grid from the full mix, 16th/triplet quantization, monophonic. Free
   rhythm (散板, 长调) makes the metre nominal. The MIDI is authoritative for timing.
6. **Index.** `build_dataset_index.py` produces one row per recording with metadata, paths and QC columns.

Model numbers, leakage findings and failure modes: `references/transcription.md`.

## Phase 4 — Audit & correct (no ground truth)

Two layers. Details: `references/auditing.md`.

- **Critic** (`src/transcription/critic/`) audits each note against independent pitch evidence: RMVPE + PESTO F0
  on separated vocals, where "confident" frames are those the two trackers agree on, and each note is judged by the
  median over its middle 60%.
  - Verdicts: ok / wrong_pitch / octave_error / unvoiced / uncertain, plus missed voiced segments.
  - Measured against GT on the benchmark: "ok" notes are 85% correct; the "unvoiced" flag has 79–96% precision
    (deleting those notes helps slightly); the "wrong pitch" flag has only ~0.5 precision, and repitching lands on
    GT 48% of the time.
  - The reason: pitch trackers measure the *performance*, but score-style GT encodes the *intended* note. A
    pitch-based critic audits fidelity to the performance, not correctness against a score. Keep that distinction
    explicit.
- **First-principles in-domain checks** (`src/transcription/audit/`), each with a chance baseline:
  - *Score reference:* same-title, region-consistent Anthology scores. Agreement 0.58 vs 0.45 chance;
    GAME > ROSVOT.
  - *Cross-performance consistency:* same song vs different song within a region. 0.43 vs 0.29.
  - *Domain gap:* the biggest difference between dataset and benchmark was pitch-tracker agreement (0.44 vs 0.87,
    as low as 0.10 in minority regions). The disagreement was soft singing plus instrument bleed, and it was solved
    with a stem-dominance evidence rule. Measure this before trusting any benchmark number.
  - *Invariance:* GAME agrees with itself on only 84% of notes across identical runs. Test run-ensembling.
  - *Human-audited gold set:* blinded A/B listening page (tones in the singer's tuning, ratings in the artifact's
    database). This is the only way to validate note-level corrections, because automatic in-domain checks were
    too coarse to show any effect. Apply no corrections until it's rated.

## Phase 5 — Scaling

See `references/scaling.md`:
- one curation agent per class batch
- a shared, append-only search log
- round-robin downloads that survive interruption
- GPU/CPU process split
- skip-existing everywhere
- configuration points for a new country, genre or source (Bilibili search returned HTTP 412 without extra work;
  archives and field-recording libraries are alternatives)

---

## Decision checklist

- [ ] Envs are native arch; GPU visible from the process that will actually run the model
- [ ] Taxonomy + per-class descriptions exist; target N and over-curation factor chosen (N=30 → 40 candidates)
- [ ] Candidates come only from logged live search; single-video URLs only; builder scripts in repo
- [ ] Downloader throttled (1 worker, 45–90 s), cookies set, cooldown-and-resume on, manifest rebuilt from disk
- [ ] Benchmark includes an independently annotated control, a second-annotator ceiling, onset-bias reporting,
      leakage notes per model, and a mixture variant
- [ ] Separation + transcription launched from arm64 Python; GPU/CPU sides parallel; skip-existing on
- [ ] Instrumental/empty-output fallback and primary-selection rules applied; index rebuilt
- [ ] Critic calibrated against GT *and* in-domain checks run with chance baselines; human gold set planned
- [ ] Research log updated with every decision and number; all code committed
- [ ] Release plan respects source licences (for third-party YouTube audio, release URLs, metadata,
      transcriptions and scripts, not the audio)
