# Failure modes seen in practice (symptom → cause → fix)

Read this before a long run. Most of these produced wrong outputs, not errors.

| # | Symptom | Cause | Fix |
|---|---|---|---|
| F1 | 33 of 46 recordings in one region "instrumental" (YourMT3+ fallback) | GAME crashed with MPS out of memory mid-folder; primary selection read the missing MIDI as "no notes" | `_processed.txt` per output folder; fallback only for processed items; missing + unprocessed = error; GAME retries with batch 1 |
| F2 | 47 of 48 recordings in one region "instrumental", although GAME found hundreds of notes | The fallback checked the **post-processed** file (offset-trimmed), which did not exist yet after an interrupted run | Judge emptiness from the raw model output |
| F3 | Separation died at file 23 of 50 in one region; whole run stopped | One m4a undecodable by Core Audio/libsndfile | ffmpeg fallback inside the separator loop |
| F4 | Speech screen died at item 157 | Same undecodable m4a in librosa/audioread | Load all audio through ffmpeg |
| F5 | Every staged audio link broken after the user moved the repo | Absolute symlinks and absolute paths in indexes | `os.path.relpath` for links; repo-relative paths in CSVs; convert existing links once |
| F6 | Index build failed: path "not in the subpath of" the repo root | `relative_to(ROOT)` on a path that was already relative, because the output folder came from an env var | Make paths absolute before calling `relative_to` |
| F7 | Orchestrator loop ended early, then ran the ensemble on partial data | `pgrep` condition on the separation process, which had crashed (F3) | Check that upstream completed (counts), not just whether a process is alive |
| F8 | Out-of-memory crashes when a classifier, separation and GAME shared MPS | Concurrent GPU jobs on unified memory | Run the classifier on CPU or alone; batch-1 retry in GAME |
| F9 | A subsequent field silently missing from a pickle (`KeyError: 'notes'` far downstream) | An inline `# comment` inserted mid-line by a text substitution commented out the rest of the dict | After scripted edits, re-read the edited line or run a key-presence check on the output |
| F10 | Watcher reported "done" immediately | The `until ! pgrep ...` condition was true because the job had already crashed | Make watchers print the log tail and check for a completion marker plus non-zero output counts |
| F11 | A pitch-based and an audio-classifier "speech" screen both flagged real singing | Unaccompanied or recitative folk singing looks like speech to both | Two independent signals, including metadata; release the scores rather than delete items |
| F12 | Link check: Bilibili API 412, empty video pages | Request signing and anti-bot pages | yt-dlp metadata extraction with cookies |
| F13 | Bash orchestrator edited while running | bash reads scripts incrementally | Edit only below the currently executing line, or stop and restart (steps are idempotent) |
| F14 | Seven `say` TTS voices produced 16 ms files | Voices not installed | Check the output duration of every calibration file |
| F15 | A run "finished" with many YouTube 403s | Transient 403s | Retry with the default player client (not `tv`) |

## A habit that would have caught most of these sooner

After each stage, print per-group counts of inputs, outputs, fallbacks and missing items (`scripts/stage_report.py`), and compare them with what is plausible. A rate that jumps in one group is nearly always a pipeline bug, not a property of the data.
