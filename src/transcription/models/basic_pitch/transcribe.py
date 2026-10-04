"""
Spotify Basic Pitch (ICASSP 2022, pip `basic-pitch`): folder of audio -> folder of .mid.

Single polyphonic, instrument-agnostic track (no source separation / instrument labels);
on vocals+accompaniment it will mix melody and accompaniment notes together.
Uses the package's default ICASSP_2022 model (CoreML backend on macOS) and default
thresholds unless overridden. Audio is decoded with ffmpeg first, so any format works.

Usage (arm64 conda env `basicpitch`):
  /Users/sophiasun/miniforge3/envs/basicpitch/bin/python src/transcription/models/basic_pitch/transcribe.py \
      IN_DIR OUT_DIR [--onset-threshold 0.5] [--frame-threshold 0.3] [--min-note-ms 127.7]
      [--fmin HZ] [--fmax HZ]
"""

import argparse
import csv
import subprocess
import tempfile
import time
from pathlib import Path

AUDIO_EXT = {".wav", ".flac", ".mp3", ".m4a", ".webm", ".ogg", ".opus", ".aac", ".mp4"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--onset-threshold", type=float, default=0.5)
    ap.add_argument("--frame-threshold", type=float, default=0.3)
    ap.add_argument("--min-note-ms", type=float, default=127.70)
    ap.add_argument("--fmin", type=float, default=None, help="min frequency (Hz), e.g. 65 for voice")
    ap.add_argument("--fmax", type=float, default=None, help="max frequency (Hz), e.g. 1400 for voice")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import Model, predict

    model = Model(ICASSP_2022_MODEL_PATH)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in args.in_dir.iterdir() if p.suffix.lower() in AUDIO_EXT)
    timing = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(files):
            dst = args.out_dir / f"{f.stem}.mid"
            if dst.exists() and not args.overwrite:
                continue
            t0 = time.time()
            wav = Path(tmp) / "in.wav"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(f), "-ac", "1",
                            "-ar", "22050", str(wav)], check=True)
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                        "-of", "csv=p=0", str(wav)], capture_output=True, text=True).stdout)
            _, midi, _ = predict(str(wav), model, onset_threshold=args.onset_threshold,
                                 frame_threshold=args.frame_threshold, minimum_note_length=args.min_note_ms,
                                 minimum_frequency=args.fmin, maximum_frequency=args.fmax)
            for inst in midi.instruments:
                inst.name = "Basic Pitch"
            midi.write(str(dst))
            el = time.time() - t0
            n = sum(len(inst.notes) for inst in midi.instruments)
            timing.append({"file": f.name, "audio_sec": round(dur, 3), "proc_sec": round(el, 3)})
            print(f"[{i + 1}/{len(files)}] {f.name}: {dur:.1f}s audio, {el:.2f}s, {n} notes", flush=True)

    if timing:
        with open(args.out_dir / "_timing.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(timing[0]))
            w.writeheader()
            w.writerows(timing)
        a, p = sum(t["audio_sec"] for t in timing), sum(t["proc_sec"] for t in timing)
        print(f"TOTAL {a:.1f}s audio in {p:.1f}s -> {60 * p / a:.2f} s per minute of audio")


if __name__ == "__main__":
    main()
