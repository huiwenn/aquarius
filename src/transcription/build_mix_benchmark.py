"""
Harder benchmark variant: each benchmark vocal clip mixed with a random excerpt of
Chinese instrumental music (ChMusic: 二胡, 琵琶, 笛子, 古筝, 唢呐 ...).

This mimics the real 色彩区 recordings (voice + accompaniment). The accompaniment
is not musically aligned with the voice, so any instrument notes a model outputs
count as false positives. That measures how well a model locks onto the voice.

GT is unchanged, so clip ids match data/transcription/benchmark/gt/.
Output: data/transcription/benchmark_mix/audio/<clip_id>.wav (44.1 kHz mono)
Vocal-to-accompaniment ratio: +3 dB (voice clearly dominant, as in most folk recordings).

Run: python src/transcription/build_mix_benchmark.py
"""

import random
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent.parent
BENCH = ROOT / "data" / "transcription" / "benchmark"
OUT = ROOT / "data" / "transcription" / "benchmark_mix" / "audio"
ACCOMP = sorted((ROOT / "data" / "raw" / "chmusic" / "ChMusic" / "Musics").glob("*.wav"))
SR = 44100
VAR_DB = 3.0
SEED = 0


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    for wav in sorted((BENCH / "audio").glob("*.wav")):
        voice, _ = librosa.load(wav, sr=SR, mono=True)
        acc_path = rng.choice(ACCOMP)
        dur = librosa.get_duration(path=acc_path)
        start = rng.uniform(0, max(0.0, dur - len(voice) / SR - 1))
        if (OUT / wav.name).exists():  # rng draws above keep later clips reproducible
            continue
        acc, _ = librosa.load(acc_path, sr=SR, mono=True, offset=start, duration=len(voice) / SR + 0.1)
        acc = np.pad(acc, (0, max(0, len(voice) - len(acc))))[: len(voice)]
        acc *= rms(voice) / rms(acc) / (10 ** (VAR_DB / 20))
        mix = voice + acc
        mix /= max(1.0, np.abs(mix).max() / 0.99)
        sf.write(OUT / wav.name, mix, SR)
    print(f"wrote {len(list(OUT.glob('*.wav')))} mixes → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
