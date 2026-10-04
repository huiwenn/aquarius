"""
Run ROSVOT (Li et al., ACL 2024) on a folder of audio -> one .mid per input file.

Wraps third_party/ROSVOT/inference/rosvot.py (batched "--metadata" mode, with the
RWBD word-boundary predictor applied automatically since we have no lyrics).

- Any format librosa can read (wav/flac/mp3/m4a...) is accepted; audio is loaded
  mono and resampled to ROSVOT's 24 kHz internally, so no pre-conversion needed.
- ROSVOT caps one sample at max_frames=30000 (hop 128 @ 24 kHz = 160 s). Longer
  files are split into <= --max-seg-sec chunks at the quietest point near each
  cut, transcribed separately, and the notes are re-assembled with time offsets.
- Default bsz=1: on CPU, batched padded inference was ~5x slower and changes notes slightly
  (padding leaks into conv context); bsz=1 matches README single-file mode.
- Output: <out_dir>/<stem>.mid (single instrument track named "rosvot").

Env: conda env `rosvot` (native arm64 python 3.9, torch 2.1.1). See setup.sh.

Usage:
  conda run -n rosvot --no-capture-output python src/transcription/models/rosvot/run_rosvot.py \
      IN_DIR OUT_DIR [--device cpu] [--thr 0.85] [--max-seg-sec 60]
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

import librosa
import numpy as np
import pretty_midi
import soundfile as sf

ROOT = Path(__file__).resolve().parents[4]
ROSVOT_DIR = ROOT / "third_party" / "ROSVOT"
SR = 24000
AUDIO_EXT = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aac", ".aiff", ".aif"}


def split_points(y: np.ndarray, sr: int, max_seg: float, search: float = 5.0) -> list[int]:
    """Sample indices at which to cut y so each piece is <= max_seg seconds.
    Each cut is placed at the lowest-RMS 50 ms frame in the last `search` s before the limit."""
    n, cuts, start = len(y), [0], 0
    hop = int(0.05 * sr)
    while n - start > max_seg * sr:
        hi = start + int(max_seg * sr)
        lo = max(start + int((max_seg - search) * sr), start + hop)
        seg = y[lo:hi]
        rms = librosa.feature.rms(y=seg, frame_length=hop * 2, hop_length=hop, center=False)[0]
        cut = lo + int(np.argmin(rms)) * hop + hop if len(rms) else hi
        cuts.append(cut)
        start = cut
    cuts.append(n)
    return cuts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--device", default="cpu", help="cpu (default). mps runs with torch 2.1.1 + our stft patch but gives WRONG notes (F1 ~0.02 vs CPU output) and NaN asserts at bsz>1 -- do not use. cuda untested here.")
    ap.add_argument("--thr", type=float, default=0.85, help="note-boundary threshold (ROSVOT default 0.85)")
    ap.add_argument("--wbd-thr", type=float, default=0.5, help="RWBD word-boundary threshold")
    ap.add_argument("--max-seg-sec", type=float, default=60.0, help="split longer files (must be < 160)")
    ap.add_argument("--bsz", type=int, default=1,
                    help="1 = no padding: output independent of batch composition and ~5x faster on CPU than 16")
    ap.add_argument("--max-tokens", type=int, default=40000)
    ap.add_argument("--work-dir", default=None, help="keep intermediate files here (default: temp dir)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    assert args.max_seg_sec < 160, "ROSVOT max_frames=30000 frames = 160 s"

    in_dir, out_dir = Path(args.in_dir).resolve(), Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in in_dir.iterdir() if p.suffix.lower() in AUDIO_EXT)
    stems = [p.stem for p in files]
    dup = sorted({s for s in stems if stems.count(s) > 1})
    assert not dup, f"duplicate stems (e.g. x.wav + x.flac) would overwrite each other: {dup[:5]}"
    if not args.overwrite:
        files = [p for p in files if not (out_dir / f"{p.stem}.mid").exists()]
    if not files:
        print("nothing to do")
        return

    work = Path(args.work_dir).resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix="rosvot_"))
    seg_dir = work / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)

    # 1. load + resample + split
    t0 = time.time()
    items, segs, total_sec = [], {}, 0.0
    for p in files:
        y, _ = librosa.load(str(p), sr=SR, mono=True)
        total_sec += len(y) / SR
        cuts = split_points(y, SR, args.max_seg_sec)
        segs[p.stem] = []
        for i, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
            name = f"{p.stem}__seg{i:03d}"
            fn = seg_dir / f"{name}.wav"
            sf.write(fn, y[a:b], SR)
            items.append({"item_name": name, "wav_fn": str(fn)})
            segs[p.stem].append((name, a / SR))
    manifest = work / "manifest.json"
    manifest.write_text(json.dumps(items, ensure_ascii=False, indent=1))
    t_load = time.time() - t0

    # 2. run ROSVOT (+RWBD)
    t1 = time.time()
    env = dict(os.environ, PYTHONPATH=str(ROSVOT_DIR), PYTORCH_ENABLE_MPS_FALLBACK="1")
    env.pop("CUDA_VISIBLE_DEVICES", None) if args.device != "cuda" else None
    cmd = [sys.executable, "inference/rosvot.py", "-o", str(work / "rosvot_out"),
           "--metadata", str(manifest), "--device", args.device, "--thr", str(args.thr),
           "--wbd_thr", str(args.wbd_thr), "--bsz", str(args.bsz), "--max_tokens", str(args.max_tokens),
           "--ds_workers", "0", "--no_save_final_npy"]
    subprocess.run(cmd, cwd=ROSVOT_DIR, env=env, check=True)
    t_model = time.time() - t1

    # 3. merge segment MIDIs -> <stem>.mid
    n_empty = 0
    for stem, parts in segs.items():
        pm = pretty_midi.PrettyMIDI()
        inst = pretty_midi.Instrument(program=0, name="rosvot")
        for name, off in parts:
            f = work / "rosvot_out" / "midi" / f"{name}.mid"
            if not f.exists():  # ROSVOT skips segments with no detected notes
                continue
            for ins in pretty_midi.PrettyMIDI(str(f)).instruments:
                for n in ins.notes:
                    inst.notes.append(pretty_midi.Note(velocity=n.velocity, pitch=n.pitch,
                                                       start=n.start + off, end=n.end + off))
        n_empty += not inst.notes
        pm.instruments.append(inst)
        pm.write(str(out_dir / f"{stem}.mid"))

    if not args.work_dir:
        shutil.rmtree(work, ignore_errors=True)
    print(f"| {len(files)} files, {total_sec / 60:.2f} min audio, {n_empty} with no notes")
    print(f"| load/split {t_load:.1f}s, model {t_model:.1f}s "
          f"-> {(t_load + t_model) / (total_sec / 60):.2f} s per minute of audio (incl. model load)")


if __name__ == "__main__":
    main()
