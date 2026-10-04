"""
Run OpenVPI GAME (Generative Adaptive MIDI Extractor) on a folder of audio -> <stem>.mid.

Setup (native arm64 conda; the default x86 conda on this machine runs under Rosetta and has no MPS):
    ~/miniforge3/bin/conda create -y -n game python=3.12
    ~/miniforge3/envs/game/bin/pip install torch torchaudio
    ~/miniforge3/envs/game/bin/pip install -r third_party/GAME/requirements.txt
    git clone https://github.com/openvpi/GAME third_party/GAME     # commit f4239345f0fe
    # checkpoints: https://github.com/openvpi/GAME/releases/tag/v1.0.0
    #   GAME-1.0-{small,medium,large}.zip -> third_party/ckpt/game/GAME-1.0-<size>/model.pt

Usage:
    ~/miniforge3/envs/game/bin/python src/transcription/models/game/run_game.py IN_DIR OUT_DIR \
        [--size medium] [--lang zh] [--seg-threshold 0.2] [--seg-radius 0.02] [--nsteps 8] \
        [--est-threshold 0.2] [--device auto|mps|cpu]

Any audio ffmpeg can read (.wav/.flac/.mp3/.m4a/.webm/...) is accepted; formats GAME's
loader (librosa/soundfile) can't handle natively are first converted to 44.1 kHz mono wav in a
temp dir. Timing (wall sec / audio min) is written to OUT_DIR/_timing.json.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parents[4]
GAME_DIR = ROOT / "third_party" / "GAME"
CKPT_DIR = ROOT / "third_party" / "ckpt" / "game"
NATIVE = {".wav", ".flac", ".ogg"}
AUDIO = NATIVE | {".mp3", ".m4a", ".aac", ".webm", ".opus", ".mp4", ".mkv", ".wma"}


def stage_inputs(in_dir: Path, tmp: Path, out_dir: Path, overwrite: bool = False) -> float:
    """Symlink/convert every audio file into tmp as <stem>.wav|flac|ogg; return total seconds.
    Files whose <stem>.mid already exists in out_dir are skipped unless overwrite."""
    total = 0.0
    for f in sorted(in_dir.iterdir()):
        ext = f.suffix.lower()
        if ext not in AUDIO:
            continue
        if not overwrite and (out_dir / f"{f.stem}.mid").exists():
            continue
        if ext in NATIVE:
            dst = tmp / f.name
            os.symlink(f.resolve(), dst)
        else:
            dst = tmp / f"{f.stem}.wav"
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(f),
                            "-ac", "1", "-ar", "44100", str(dst)], check=True)
        total += sf.info(str(dst)).duration
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--size", default="medium", choices=["small", "medium", "large"])
    ap.add_argument("--lang", default="zh", help="en/ja/yue/zh, or '' for none")
    ap.add_argument("--seg-threshold", type=float, default=0.2)
    ap.add_argument("--seg-radius", type=float, default=0.02, help="seconds")
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--nsteps", type=int, default=8)
    ap.add_argument("--est-threshold", type=float, default=0.2)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--device", default="auto", choices=["auto", "mps", "cpu"])
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK="1")
    if args.device == "cpu":
        env["PL_TRAINER_ACCELERATOR"] = "cpu"  # honoured by lightning Trainer defaults
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        audio_sec = stage_inputs(args.in_dir.resolve(), tmp, args.out_dir, args.overwrite)
        stems_this_call = [p.stem for p in tmp.iterdir()]
        if not any(tmp.iterdir()):
            print("nothing to do (all outputs exist)")
            return
        cmd = [sys.executable, "infer.py", "extract", str(tmp),
               "-m", str(CKPT_DIR / f"GAME-1.0-{args.size}" / "model.pt"),
               "--seg-threshold", str(args.seg_threshold), "--seg-radius", str(args.seg_radius),
               "--t0", str(args.t0), "--nsteps", str(args.nsteps),
               "--est-threshold", str(args.est_threshold), "--batch-size", str(args.batch_size),
               "--output-formats", "mid", "--output-dir", str(args.out_dir.resolve())]
        if args.lang:
            cmd += ["-l", args.lang]
        t = time.time()
        if subprocess.run(cmd, cwd=GAME_DIR, env=env).returncode != 0:
            # usually MPS out-of-memory on a long recording while the GPU is shared; retry outputs still missing
            # one at a time (batch 1). Raise if that fails too, so callers never mistake a crash for "no singing".
            print("GAME failed; retrying missing outputs with --batch-size 1", flush=True)
            for f in list(tmp.iterdir()):
                if (args.out_dir / f"{f.stem}.mid").exists():
                    f.unlink()
            i = cmd.index("--batch-size")
            subprocess.run(cmd[:i + 1] + ["1"] + cmd[i + 2:], cwd=GAME_DIR, env=env, check=True)
        wall = time.time() - t
        # GAME writes no MIDI when it finds no singing. Record every stem this successful call processed, so a
        # missing MIDI can be told apart from a crash (transcribe_regions.instrumental_fallback, select_primary).
        staged = sorted({p.stem for p in tmp.iterdir()} | set(stems_this_call))
        with open(args.out_dir / "_processed.txt", "a") as fh:
            fh.writelines(s + "\n" for s in staged)
    info = {"model": f"GAME-1.0-{args.size}", "args": {k: str(v) for k, v in vars(args).items()},
            "audio_sec": audio_sec, "wall_sec": wall,
            "sec_per_audio_min": wall / (audio_sec / 60) if audio_sec else None}
    (args.out_dir / "_timing.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
