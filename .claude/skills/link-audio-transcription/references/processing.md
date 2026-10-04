# Processing: decode, separate, F0, transcribe, ensemble, select

## Contents
1. Decoding
2. Separation
3. F0
4. Speech screen
5. Transcription runs
6. Ensembles and offset trim
7. Primary selection and fallbacks
8. MusicXML
9. Throughput on one laptop (M1 Pro)

---

## 1. Decoding

Use `scripts/decode.py` (`load_audio(path, sr)`): ffmpeg to float32 mono. Tools that open files themselves need a wrapper like this, which was added to a separation script:

```python
try:
    outs = sep.separate(str(f), names)
except Exception:  # some Bilibili m4a: Core Audio / libsndfile cannot decode
    wav = tmp / f"{f.stem}.input.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(f), "-ar", "44100", str(wav)], check=True)
    outs = sep.separate(str(wav), names)
```

Without it, one bad file killed a whole multi-hour separation run.

## 2. Separation

- **Model:** htdemucs through `audio-separator`. Accompaniment = the sum of drums, bass and other.
  - BS-RoFormer gave the same downstream transcription accuracy at 8–15× the time.
- **Throughput:** about 35 s per recording alone, about 70–110 s while GAME shares the GPU.
- **Architecture:** launch from a **native arm64** Python. A process started from an x86 (Rosetta) Python makes its children report `i386`, and audio-separator then silently falls back to CPU.
- **Naming:** audio-separator renames `__vocals` to `_vocals`; match outputs by glob, not by exact name.

## 3. F0

- **RMVPE:** on CPU, in chunks of 60 s to bound memory.
- **PESTO:** returns a confidence. Use `pesto.predict`; its model call returns outputs in a different order. Fold sub-second tails into the previous chunk, because the CQT padding fails on tiny inputs.
- **Confident frame:** RMVPE detects voice AND (PESTO agrees OR the voice is ≥ 12 dB above the accompaniment at the tracked pitch).
- **Ornament layer:** keep the continuous F0 as the primary layer for any ornament or intonation analysis. Quantised MIDI is one view of it.

## 4. Speech screen

- **Method:** AST (`MIT/ast-finetuned-audioset-10-10-0.4593`) on 10 s windows of the full mix, keeping the speech, singing, music and silence classes.
  - A window is **speech** if: speech ≥ 0.5, speech > 2 × singing, and music < 0.5.
  - A window is **silence** if silence ≥ 0.5.
- **Calibration:** macOS `say` voices give synthetic speech (only some voices are installed; check that the output length is > 0).
- **Failure mode:** unaccompanied, speech-like traditional singing scores high, so use the two-signal rule in SKILL.md.
- **Environment:** it needs `transformers` + `librosa` + `pandas` in one environment; install librosa into the ML environment if it is missing.

## 5. Transcription runs

- **GAME** (openvpi): one call per folder, on MPS.
  - Record the inputs that each **successful** call processed in `_processed.txt`, because GAME writes no MIDI when it finds no singing.
  - On failure (usually MPS out of memory while another job holds the GPU), retry the still-missing outputs with `--batch-size 1`. If that also fails, raise.
- **ROSVOT:** CPU only (wrong output on MPS); about 6.7 s per audio-minute. Run it in parallel with GPU work, on folders whose separation is complete (`--only-ready`).
- **YourMT3+:** faster on CPU than MPS. Use it as the instrumental fallback on the full mix.

## 6. Ensembles and offset trim

- **Ensemble:** three GAME runs; keep a note present in ≥ 2 runs with the same pitch and onsets within 50 ms; use median times; enforce monophony. Two disjoint 3-run ensembles agreed on 90% of notes, against 84% for single runs.
- **Offset trim:** GAME offsets are late; subtracting 50 ms (chosen by 2-fold singer-disjoint cross-validation on vocadito) raised COnPOff from 0.299 to 0.357.
- **Keep the single run too:** in one downstream study, the single run kept slightly more style information than the ensemble.

## 7. Primary selection and fallbacks

Use coverage = total note duration / recording duration, with fixed rules:
1. GAME processed the item and found nothing, or GAME coverage < 0.05 and ROSVOT coverage < 0.10 → YourMT3+ (instrumental).
2. GAME coverage < 0.15 and ROSVOT coverage > max(0.20, 2 × GAME coverage) → ROSVOT.
3. Otherwise → the GAME ensemble with the trim.

GAME not having processed an item is an **error to report, not a fallback**. See `failure_modes.md`, entries F1 and F2.

## 8. MusicXML

- **Method:** beat-track the full mix (accompaniment carries the pulse), map note times to the grid by interpolation, quantise to 16ths and eighth-note triplets, cut each note at the next onset, then write the file with music21.
- **Free rhythm:** the beat tracker imposes a pulse on free-rhythm songs, so a coefficient-of-variation "free rhythm" flag never fires. Treat the metre as nominal and the MIDI timing as the reference.

## 9. Throughput (one M1 Pro, ~700 recordings, ~39 h of audio)

| Step | Time |
|---|---|
| Separation | ~10 h while sharing the GPU |
| GAME single pass | a few hours |
| GAME runs 2 + 3 for the ensemble | ~8 h (20–40 min per region of ~47 recordings) |
| RMVPE + PESTO | ~2 h |
| ROSVOT | overlaps the GPU work |

Plan for an overnight-plus-day run, and check progress through the logs, not through memory of what was started.
