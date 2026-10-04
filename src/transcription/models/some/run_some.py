"""
Run OpenVPI SOME (Singing-Oriented MIDI Extractor) on a folder of audio -> <stem>.mid.

SOME's own infer.py handles one file at a time and only picks CUDA/CPU; this runner loads
the model once and runs on MPS (or CPU), reusing SOME's slicer + MIDI writer unchanged.

Setup (native arm64 conda):
    ~/miniforge3/bin/conda create -y -n some python=3.10
    ~/miniforge3/envs/some/bin/pip install torch torchaudio
    ~/miniforge3/envs/some/bin/pip install click einops==0.6.1 h5py "librosa<0.10.0" "lightning>=2.0.0" \
        matplotlib mido numpy PyYAML scipy tensorboard torchmetrics tqdm praat-parselmouth "setuptools<81"
    # (fairseq / gradio / onnx from requirements.txt are only for training / webui / export — skipped)
    git clone https://github.com/openvpi/SOME third_party/SOME      # commit e523eef70777
    # checkpoints: https://github.com/openvpi/SOME/releases
    #   v1.0.0-baseline/0119_continuous128_5spk.zip -> third_party/ckpt/some/0119_continuous256_5spk/
    #   v0.0.1/0918_continuous256_clean_3spk_fixmel.zip -> third_party/ckpt/some/0918_.../

Usage:
    ~/miniforge3/envs/some/bin/python src/transcription/models/some/run_some.py IN_DIR OUT_DIR \
        [--ckpt 0119] [--device auto|mps|cpu]

Any audio ffmpeg can read is accepted (librosa<0.10 falls back to audioread/ffmpeg for
.m4a/.webm etc.; no manual conversion needed as long as ffmpeg is on PATH).
"""

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

import librosa
import torch
import yaml

ROOT = Path(__file__).resolve().parents[4]
SOME_DIR = ROOT / "third_party" / "SOME"
CKPT_DIR = ROOT / "third_party" / "ckpt" / "some"
CKPTS = {
    "0119": CKPT_DIR / "0119_continuous256_5spk" / "model_ckpt_steps_100000_simplified.ckpt",
    "0918": CKPT_DIR / "0918_continuous256_clean_3spk_fixmel" / "model_steps_64000_simplified.ckpt",
}
AUDIO = {".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac", ".webm", ".opus", ".mp4", ".mkv", ".wma"}

sys.path.insert(0, str(SOME_DIR))
import inference  # noqa: E402  (SOME package)
from utils.infer_utils import build_midi_file  # noqa: E402
from utils.slicer2 import Slicer  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--ckpt", default="0119", choices=list(CKPTS))
    ap.add_argument("--device", default="auto", choices=["auto", "mps", "cpu"])
    args = ap.parse_args()
    device = args.device
    if device == "auto":
        device = "mps" if torch.backends.mps.is_available() else "cpu"

    model_path = CKPTS[args.ckpt]
    config = yaml.safe_load(model_path.with_name("config.yaml").read_text(encoding="utf8"))
    cls_path = inference.task_inference_mapping[config["task_cls"]]
    mod, name = cls_path.rsplit(".", 1)
    infer_ins = getattr(importlib.import_module(mod), name)(config=config, model_path=model_path, device=device)
    sr = config["audio_sample_rate"]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(f for f in args.in_dir.iterdir() if f.suffix.lower() in AUDIO)
    audio_sec, t = 0.0, time.time()
    for f in files:
        waveform, _ = librosa.load(str(f), sr=sr, mono=True)
        audio_sec += len(waveform) / sr
        chunks = Slicer(sr=sr, max_sil_kept=1000).slice(waveform)  # same as SOME infer.py
        midis = infer_ins.infer([c["waveform"] for c in chunks])
        build_midi_file([c["offset"] for c in chunks], midis, tempo=120).save(args.out_dir / f"{f.stem}.mid")
    wall = time.time() - t
    info = {"model": model_path.parent.name, "device": device, "n_files": len(files),
            "audio_sec": audio_sec, "wall_sec": wall,
            "sec_per_audio_min": wall / (audio_sec / 60) if audio_sec else None}
    (args.out_dir / "_timing.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
