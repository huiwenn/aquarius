"""
RMVPE F0 for every audio file in a directory → <out>/<stem>.npz (f0 Hz, 0 = unvoiced; 10 ms hop).

RMVPE is the vocal pitch extractor bundled with ROSVOT (third_party/ROSVOT/checkpoints/rmvpe).
It's the critic's primary pitch evidence: independent of GAME's note decoder.

Env: ROSVOT env (arm64 torch 2.1, CPU):
  /usr/local/Caskroom/miniforge/base/envs/rosvot/bin/python src/transcription/critic/f0_rmvpe.py IN OUT
"""

import sys
from pathlib import Path

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ROSVOT = ROOT / "third_party" / "ROSVOT"
sys.path.insert(0, str(ROSVOT))
from modules.pe.rmvpe.inference import RMVPE  # noqa: E402

EXTS = {".wav", ".flac", ".webm", ".m4a", ".mp3", ".ogg", ".opus"}
CHUNK_S = 60  # bound memory on long recordings


def main() -> None:
    inp, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    model = RMVPE(str(ROSVOT / "checkpoints" / "rmvpe" / "model.pt"), hop_length=160, device="cpu")
    files = sorted(f for f in inp.iterdir() if f.suffix in EXTS and not (out / f"{f.stem}.npz").exists())
    for i, f in enumerate(files, 1):
        y, _ = librosa.load(f, sr=16000, mono=True)
        n_frames = len(y) // 160 + 1
        parts = []
        for s in range(0, len(y), CHUNK_S * 16000):
            seg = y[s: s + CHUNK_S * 16000]
            f0 = model.infer_from_audio(seg, sample_rate=16000, thred=0.03)
            f0 = model.postprocess(np.asarray(f0, dtype=float), fmin=60, fmax=1100)
            parts.append(f0[: len(seg) // 160 + (1 if s + CHUNK_S * 16000 >= len(y) else 0)])
        f0 = np.concatenate(parts)[:n_frames]
        np.savez_compressed(out / f"{f.stem}.npz", f0=f0.astype(np.float32), hop_s=0.01)
        print(f"[{i}/{len(files)}] {f.name}", flush=True)


if __name__ == "__main__":
    main()
