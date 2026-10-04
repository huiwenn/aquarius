"""Decode any audio container (m4a/webm/opus/mp3/wav) to mono float32 via ffmpeg.
Use this wherever audio is loaded: libsndfile and macOS Core Audio fail on some Bilibili m4a files."""
import subprocess
import numpy as np


def load_audio(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def to_wav(src, dst, sr=44100):
    """For tools that open files themselves: convert once, then pass the WAV."""
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(src), "-ar", str(sr), str(dst)],
                   check=True)
