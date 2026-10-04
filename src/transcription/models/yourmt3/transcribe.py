"""
YourMT3+ multi-instrument transcription: folder of audio -> folder of multi-track .mid.

Code + checkpoints come from the HF Space mimbres/YourMT3 (cloned to
third_party/yourmt3_space, see README.md next to this file). Mirrors the Space's
model_helper.transcribe(), with these changes:
  - device = cpu (default; faster than mps on M1 Pro) or mps (Space hard-codes cuda)
  - audio decoded with ffmpeg (any format: wav/webm/m4a/mp3) to 16 kHz mono
  - MIDI written straight to <out_dir>/<stem>.mid
  - per-file timing log (<out_dir>/_timing.csv)

The vocal melody track is named "Singing Voice" (program 100 -> GM 65 Alto Sax);
"Singing Voice (chorus)" (program 101) may also appear. Use --track-filter "singing".

Usage (arm64 conda env `ymt3`):
  /Users/sophiasun/miniforge3/envs/ymt3/bin/python src/transcription/models/yourmt3/transcribe.py \
      IN_DIR OUT_DIR [--model moe_ps|moe_nops] [--device cpu|mps] [--bsz 8]
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
SPACE = ROOT / "third_party" / "yourmt3_space"
AUDIO_EXT = {".wav", ".flac", ".mp3", ".m4a", ".webm", ".ogg", ".opus", ".aac", ".mp4"}

_COMMON = ['-p', '2024', '-tk', 'mc13_full_plus_256', '-dec', 'multi-t5', '-nl', '26',
           '-enc', 'perceiver-tf', '-sqr', '1', '-ff', 'moe', '-wf', '4', '-nmoe', '8',
           '-kmoe', '2', '-act', 'silu', '-epe', 'rope', '-rp', '1', '-ac', 'spec',
           '-hop', '300', '-atc', '1', '-pr', '32']
# Exact names/args from the Space's app.py ("YPTF.MoE+Multi (noPS)" is the Space default).
MODELS = {
    "moe_nops": ["mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops@last.ckpt", *_COMMON],
    "moe_ps": ["mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b80_ps2@model.ckpt", *_COMMON],
}


def load_audio(path: Path, sr: int) -> torch.Tensor:
    """Decode any format with ffmpeg -> (1, n) float32 mono at sr."""
    out = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return torch.from_numpy(np.frombuffer(out, dtype=np.float32).copy()).unsqueeze(0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--model", default="moe_ps", choices=MODELS)  # PS scored best on our benchmark
    # CPU is ~1.4-2.3x faster than MPS on M1 Pro (autoregressive decode, small batches).
    ap.add_argument("--device", default="cpu", choices=["cpu", "mps"])
    ap.add_argument("--bsz", type=int, default=8)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    in_dir, out_dir = args.in_dir.resolve(), args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # The Space code resolves checkpoints relative to its root ("amt/logs/...").
    os.chdir(SPACE)
    sys.path[:0] = [str(SPACE / "amt" / "src"), str(SPACE)]
    sys.argv = sys.argv[:1]
    from model_helper import load_model_checkpoint  # noqa: E402
    from utils.audio import slice_padded_array  # noqa: E402
    from utils.event2note import merge_zipped_note_events_and_ties_to_notes  # noqa: E402
    from utils.note2event import mix_notes  # noqa: E402
    from utils.utils import write_model_output_as_midi  # noqa: E402

    model = load_model_checkpoint(args=MODELS[args.model], device="cpu").to(args.device)
    sr, seg = model.audio_cfg["sample_rate"], model.audio_cfg["input_frames"]

    files = sorted(p for p in in_dir.iterdir() if p.suffix.lower() in AUDIO_EXT)
    timing = []
    for i, f in enumerate(files):
        dst = out_dir / f"{f.stem}.mid"
        if dst.exists() and not args.overwrite:
            continue
        t0 = time.time()
        audio = load_audio(f, sr)
        dur = audio.shape[1] / sr
        segs = slice_padded_array(audio, seg, seg)
        segs = torch.from_numpy(segs.astype("float32")).to(args.device).unsqueeze(1)
        with torch.inference_mode():
            pred_token_arr, _ = model.inference_file(bsz=args.bsz, audio_segments=segs)
        starts = [seg * k / sr for k in range(segs.shape[0])]
        notes_per_ch, err = [], Counter()
        for ch in range(model.task_manager.num_decoding_channels):
            arr_ch = [a[:, ch, :] for a in pred_token_arr]
            zipped, _, _ = model.task_manager.detokenize_list_batches(arr_ch, starts, return_events=True)
            notes_ch, err_ch = merge_zipped_note_events_and_ties_to_notes(zipped)
            notes_per_ch.append(notes_ch)
            err += err_ch
        notes = mix_notes(notes_per_ch)
        write_model_output_as_midi(notes, str(out_dir / "_tmp"), f.stem, model.midi_output_inverse_vocab)
        (out_dir / "_tmp" / "model_output" / f"{f.stem}.mid").replace(dst)
        el = time.time() - t0
        timing.append({"file": f.name, "audio_sec": round(dur, 3), "proc_sec": round(el, 3)})
        print(f"[{i + 1}/{len(files)}] {f.name}: {dur:.1f}s audio, {el:.1f}s, {len(notes)} notes", flush=True)

    for d in [out_dir / "_tmp" / "model_output", out_dir / "_tmp"]:
        if d.exists():
            d.rmdir()
    if timing:
        with open(out_dir / "_timing.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(timing[0]))
            w.writeheader()
            w.writerows(timing)
        a, p = sum(t["audio_sec"] for t in timing), sum(t["proc_sec"] for t in timing)
        print(f"TOTAL {a:.1f}s audio in {p:.1f}s -> {60 * p / a:.2f} s per minute of audio ({args.device})")


if __name__ == "__main__":
    main()
