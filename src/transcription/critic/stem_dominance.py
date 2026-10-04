"""
Per-frame stem dominance at the RMVPE pitch: vocal-stem vs accompaniment-stem magnitude (dB) at f0, 2·f0, 3·f0
(max over ±1 bin, summed over harmonics). 10 ms frames aligned with the F0 files.

Why: in-domain, RMVPE and PESTO agree on only ~42% of voiced frames (87% on the benchmark). The
disagreement is mostly RMVPE-voiced frames where PESTO has low confidence. In those frames the vocal stem is
still ~+19 dB over the accompaniment at the tracked pitch, but ~9 dB quieter than agreed frames: soft or breathy
singing, not bleed. Except in heterophonic regions (新疆, 北方草原: +6–8 dB), where instruments double the melody.
Stem dominance therefore decides whether an RMVPE-only frame is trustworthy singing.

Output: data/transcription/critic/dominance/<region>/<id>.npz (dom_db float32; NaN where RMVPE unvoiced)
Run (py312): python src/transcription/critic/stem_dominance.py
"""

from pathlib import Path

import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "data" / "regions_transcription"
C = ROOT / "data" / "transcription" / "critic"
N_FFT, HOP, SR = 2048, 160, 16000


def dominance(vox: Path, acc: Path, f0: np.ndarray) -> np.ndarray:
    v, _ = librosa.load(vox, sr=SR, mono=True)
    a, _ = librosa.load(acc, sr=SR, mono=True)
    n = min(len(f0), len(v) // HOP + 1, len(a) // HOP + 1)
    Sv = np.abs(librosa.stft(v, n_fft=N_FFT, hop_length=HOP))[:, :n]
    Sa = np.abs(librosa.stft(a, n_fft=N_FFT, hop_length=HOP))[:, :n]
    bin_hz = SR / N_FFT
    out = np.full(len(f0), np.nan, np.float32)
    idx = np.where(f0[:n] > 0)[0]
    ev, ea = np.zeros(len(idx)), np.zeros(len(idx))
    for h in (1, 2, 3):
        b = np.clip(np.round(h * f0[idx] / bin_hz).astype(int), 1, Sv.shape[0] - 2)
        ev += np.max([Sv[b + o, idx] for o in (-1, 0, 1)], axis=0)
        ea += np.max([Sa[b + o, idx] for o in (-1, 0, 1)], axis=0)
    out[idx] = 20 * np.log10((ev + 1e-6) / (ea + 1e-6))
    return out


def main() -> None:
    files = sorted((C / "f0_rmvpe").glob("*/*.npz"))
    for i, f in enumerate(files, 1):
        region, vid = f.parent.name, f.stem
        out = C / "dominance" / region / f"{vid}.npz"
        vox, acc = T / "vocals" / region / f"{vid}.wav", T / "accomp" / region / f"{vid}.wav"
        if out.exists() or not acc.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(out, dom_db=dominance(vox, acc, np.load(f)["f0"]))
        if i % 25 == 0:
            print(f"[{i}/{len(files)}]", flush=True)


if __name__ == "__main__":
    main()
