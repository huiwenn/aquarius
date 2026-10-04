"""
In-domain check C: stability of the transcriber under perturbations that should not change the answer.

Stratified sample: `--per-region` recordings per region (seed 0), first `--seconds` of separated vocals.
Perturbations (each transcribed with the production GAME config):
  rerun     identical input, second run (GAME's D3PM sampling is stochastic)
  shift+2   vocals pitch-shifted +2 semitones (librosa, phase vocoder) → every note should move +2
  shift-2   −2 semitones
Metrics vs the unperturbed transcription (note F1, onset ±50 ms, pitch ±50 c after undoing the shift):
low stability flags notes/recordings the model is unsure about, which is useful because it needs no reference.
Per-note stability (a note survives all perturbations) is saved for the human-audit sampler.

Run from an arm64 python with librosa+soundfile+pandas+mir_eval (e.g. py312 for analysis; GAME runs via its env):
  python src/transcription/audit/invariance.py [--per-region 3 --seconds 60]
"""

import argparse
import random
import subprocess
import sys
from pathlib import Path

import librosa
import mir_eval
import numpy as np
import pandas as pd
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from melody import load_notes  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "data" / "regions_transcription"
W = ROOT / "data" / "transcription" / "audit" / "invariance"
GAME = [str(Path.home() / "miniforge3" / "envs" / "game" / "bin" / "python"),
        str(ROOT / "src" / "transcription" / "models" / "game" / "run_game.py")]
GAME_ARGS = ["--size", "medium", "--lang", "zh", "--seg-threshold", "0.1"]


def f1(ref, est, shift=0) -> float:
    if not ref or not est:
        return np.nan
    r, e = np.array(ref), np.array(est)
    return mir_eval.transcription.precision_recall_f1_overlap(
        r[:, :2], mir_eval.util.midi_to_hz(r[:, 2]), e[:, :2], mir_eval.util.midi_to_hz(e[:, 2] - shift),
        offset_ratio=None)[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-region", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    idx = pd.read_csv(T / "dataset_index.csv")
    idx = idx[idx.transcription_model == "game_pp"]
    sample = idx.groupby("region", group_keys=False).apply(
        lambda g: g.sample(min(len(g), args.per_region), random_state=args.seed))

    conds = {"orig": 0, "rerun": 0, "shift+2": 2, "shift-2": -2}
    for c, s in conds.items():
        d = W / "audio" / c
        d.mkdir(parents=True, exist_ok=True)
        for r in sample.itertuples():
            out = d / f"{r.video_id}.wav"
            if out.exists():
                continue
            y, sr = librosa.load(ROOT / r.vocals_path, sr=44100, mono=True, duration=args.seconds)
            if s:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=s)
            sf.write(out, y, sr)
        subprocess.run(GAME + [str(d), str(W / "midi" / c)] + GAME_ARGS, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    rows = []
    for r in sample.itertuples():
        base = load_notes(W / "midi" / "orig" / f"{r.video_id}.mid")
        row = {"region": r.region, "video_id": r.video_id, "n_notes": len(base)}
        for c, s in conds.items():
            if c != "orig":
                row[c] = f1(base, load_notes(W / "midi" / c / f"{r.video_id}.mid"), s)
        rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(W / "invariance.csv", index=False)
    print(d[["rerun", "shift+2", "shift-2"]].describe().round(3).to_string())
    print("\nby region (mean F1 vs original):")
    print(d.groupby("region")[["rerun", "shift+2", "shift-2"]].mean().round(2).to_string())


if __name__ == "__main__":
    main()
