"""
Build the notator package from data/annotation/excerpts.csv (src/annotation/select_excerpts.py):
  data/annotation_package/E##_mix.wav    the excerpt ±2 s from the original audio (44.1 kHz)
  data/annotation_package/E##_voice.wav  the same span of the separated voice
  data/annotation_package/E##_info.txt   start/end inside the clip only (region, genre, title, singer withheld)
  data/annotation_package/GUIDELINE.md   copy of docs/annotation_guideline.md
The package is for the notators only and is not redistributed.
Run (py312): python src/annotation/build_package.py
"""

import shutil
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PAD = 2.0


def cut(src: Path, dst: Path, start: float, dur: float) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
                    "-i", str(src), "-ar", "44100", str(dst)], check=True)


def main() -> None:
    ex = pd.read_csv(ROOT / "data" / "annotation" / "excerpts.csv")
    out = ROOT / "data" / "annotation_package"
    out.mkdir(parents=True, exist_ok=True)
    audio = {}
    for man, idc in ((ROOT / "data" / "regions_audio" / "manifest.csv", "video_id"),
                     (ROOT / "data" / "regions_v2" / "manifest.csv", "id")):
        m = pd.read_csv(man)
        audio.update(dict(zip(m[idc], m.audio_path)))
    for r in ex.itertuples():
        t = ROOT / "data" / ("regions_transcription" if r.round == 1 else "regions_v2/transcription")
        s0 = max(0.0, r.start_s - PAD)
        dur = (r.end_s + PAD) - s0
        cut(ROOT / audio[r.item_id], out / f"{r.excerpt}_mix.wav", s0, dur)
        cut(t / "vocals" / r.region / f"{r.item_id}.wav", out / f"{r.excerpt}_voice.wav", s0, dur)
        (out / f"{r.excerpt}_info.txt").write_text(
            f"Excerpt {r.excerpt}\nNotate from {r.start_s - s0:.2f} s to {r.end_s - s0:.2f} s of the clip "
            f"({PAD:.0f} s of context before and after).\n")
    shutil.copy(ROOT / "docs" / "annotation_guideline.md", out / "GUIDELINE.md")
    print(len(ex), "excerpts →", out)


if __name__ == "__main__":
    main()
