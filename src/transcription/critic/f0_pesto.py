"""
PESTO F0 (Riou et al. 2023, self-supervised, model mir-1k_g7) → <out>/<stem>.npz
(f0 Hz, conf in [0,1]; 10 ms hop).

Second, architecturally unrelated pitch tracker: frames where RMVPE and PESTO agree are the
critic's "confident" frames, and their disagreement rate measures how far the critic itself can be trusted.

Env: arm64 `sep` env (MPS):
  ~/miniforge3/envs/sep/bin/python src/transcription/critic/f0_pesto.py IN OUT
"""

import sys
from pathlib import Path

import librosa
import numpy as np
import pesto
import torch

EXTS = {".wav", ".flac", ".webm", ".m4a", ".mp3", ".ogg", ".opus"}
CHUNK_S = 60


def main() -> None:
    inp, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    files = sorted(f for f in inp.iterdir() if f.suffix in EXTS and not (out / f"{f.stem}.npz").exists())
    for i, f in enumerate(files, 1):
        y, _ = librosa.load(f, sr=16000, mono=True)
        n_frames = len(y) // 160 + 1
        f0s, confs = [], []
        with torch.inference_mode():
            L = CHUNK_S * 16000
            starts = list(range(0, len(y), L))
            if len(starts) > 1 and len(y) - starts[-1] < 16000:  # fold a <1 s tail into the previous chunk
                starts.pop()                                    # (PESTO's CQT padding fails on tiny inputs)
            for k, s in enumerate(starts):
                e = starts[k + 1] if k + 1 < len(starts) else len(y)
                x = torch.from_numpy(y[s:e]).float().to(dev)
                _, f0, conf, _ = pesto.predict(x, 16000, step_size=10.0, model_name="mir-1k_g7")
                f0s.append(f0.cpu().numpy().ravel())
                confs.append(conf.cpu().numpy().ravel())
        f0, conf = np.concatenate(f0s), np.concatenate(confs)
        f0 = np.pad(f0, (0, max(0, n_frames - len(f0))))[:n_frames]
        conf = np.pad(conf, (0, max(0, n_frames - len(conf))))[:n_frames]
        np.savez_compressed(out / f"{f.stem}.npz", f0=f0.astype(np.float32),
                            conf=conf.astype(np.float32), hop_s=0.01)
        print(f"[{i}/{len(files)}] {f.name}", flush=True)


if __name__ == "__main__":
    main()
