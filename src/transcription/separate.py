"""
Vocal separation front-end (python-audio-separator). Default model BS-RoFormer; the full
dataset uses htdemucs (--model htdemucs.yaml), which is 7-15x faster at equal downstream accuracy.

Writes <out_dir>/<stem>.wav (vocals) and, with --keep-accomp, <out_dir>/accomp/<stem>.wav.
Skips stems whose output already exists.

Env: arm64 conda env `sep` (audio-separator 0.47.0, torch MPS)
  ~/miniforge3/envs/sep/bin/python src/transcription/separate.py IN_DIR OUT_DIR [--keep-accomp]
"""

import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import soundfile as sf
from audio_separator.separator import Separator

MODEL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
EXTS = {".wav", ".webm", ".m4a", ".opus", ".mp3", ".flac", ".ogg", ".mp4"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--keep-accomp", action="store_true")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--overlap", type=int, default=None,
                    help="MDXC overlap (model default if unset; 2 is ~3x faster, see docs/transcription.md)")
    ap.add_argument("--autocast", action="store_true")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in args.in_dir.iterdir() if p.suffix in EXTS
                   and not (args.out_dir / f"{p.stem}.wav").exists())
    print(f"{len(files)} files to separate with {args.model}")
    if not files:
        return

    tmp = Path(tempfile.mkdtemp())
    sep = Separator(output_dir=str(tmp), output_format="WAV", use_autocast=args.autocast,
                    model_file_dir=str(Path.home() / ".cache" / "audio-separator"),
                    mdxc_params={"segment_size": 256, "override_model_segment_size": False,
                                 "batch_size": 1, "overlap": args.overlap, "pitch_shift": 0})
    sep.load_model(model_filename=args.model)
    t0 = time.time()
    for i, f in enumerate(files, 1):
        names = {"Vocals": f"{f.stem}_vocals", "Instrumental": f"{f.stem}_accomp"}
        try:
            outs = sep.separate(str(f), names)
        except Exception as e:  # e.g. Core Audio can't decode some Bilibili m4a → decode with ffmpeg instead
            print(f"  decode failed ({type(e).__name__}); retrying via ffmpeg WAV", flush=True)
            wav = tmp / f"{f.stem}.input.wav"
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(f), "-ar", "44100",
                            str(wav)], check=True)
            outs = sep.separate(str(wav), names)
            wav.unlink()
        others = []
        for o in outs:
            o = tmp / Path(o).name
            if o.stem.endswith("_vocals"):
                shutil.move(o, args.out_dir / f"{f.stem}.wav")
            else:
                others.append(o)
        if args.keep_accomp and others:
            # 2-stem models give one instrumental; demucs gives drums/bass/other → sum them
            (args.out_dir / "accomp").mkdir(exist_ok=True)
            acc, sr = sf.read(others[0])
            for o in others[1:]:
                acc = acc + sf.read(o)[0]
            sf.write(args.out_dir / "accomp" / f"{f.stem}.wav", acc, sr)
        for o in others:
            o.unlink()
        print(f"[{i}/{len(files)}] {f.name}  ({time.time() - t0:.0f}s)", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
