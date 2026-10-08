"""
Build one private package per notator from data/annotation/excerpts.csv and orders.csv
(src/annotation/select_excerpts.py):

  data/annotation_package/N1/
    index.html            offline annotation page (src/annotation/portal_template.html): guideline, the notator's
                          order, excerpt player, notes / background / debrief forms, format checks, export.
                          Runs from the folder with no network; answers stay in the browser until exported.
    audio/E##_mix.wav     the excerpt ±2 s from the original audio (44.1 kHz)  [primary]
    audio/E##_voice.wav   the same span of the separated voice                 [optional]
    audio/E##_guide.wav   1 kHz clicks at the start and the end of the excerpt
    GUIDELINE.md, jianpu_examples.txt, README.txt
Region, genre, title and singer are withheld. The audio is cut once into data/annotation_package/_audio/ and
hard-linked into each notator folder. The packages are for the notators only and are never redistributed.

Run (py312): python src/annotation/build_package.py [--demo]
  --demo  builds a 3-excerpt test package from arbitrary core recordings into data/annotation_package_demo/
          (to test the page; not part of the study)
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from colour_regions.regions import REGIONS  # noqa: E402

PAD = 2.0
SR = 44100
STUDY_VERSION = "v1.1-draft"


def cut(src: Path, dst: Path, start: float, dur: float) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
                    "-i", str(src), "-ar", str(SR), str(dst)], check=True)


def clicks(dst: Path, dur: float, at: list[float]) -> None:
    import soundfile as sf
    y = np.zeros(int(dur * SR), dtype=np.float32)
    t = np.arange(int(0.03 * SR)) / SR
    c = 0.5 * np.sin(2 * np.pi * 1000 * t) * np.hanning(len(t))
    for a in at:
        i = int(a * SR)
        y[i:i + len(c)] = c[: len(y) - i]
    sf.write(dst, y, SR)


def audio_paths() -> dict:
    out = {}
    for man, idc in ((ROOT / "data" / "regions_audio" / "manifest.csv", "video_id"),
                     (ROOT / "data" / "regions_v2" / "manifest.csv", "id")):
        m = pd.read_csv(man)
        out.update(dict(zip(m[idc], m.audio_path)))
    return out


def demo_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    p = rec[rec.core & (rec.duration_s > 60)].sample(3, random_state=7)
    ex = pd.DataFrame({"excerpt": ["E00", "E17", "E42"], "item_id": p.item_id.values,
                       "role": ["calibration", "base", "base"], "round": p["round"].values, "region": p.region.values,
                       "start_s": (p.duration_s * 0.25).round(2).values})
    ex["end_s"] = ex.start_s + 30.0
    orders = pd.DataFrame([dict(notator=k, position=i + 1, excerpt=e) for k in ("N1", "N2", "N3")
                           for i, e in enumerate(["E00", "E42", "E17"])])
    return ex, orders


def main() -> None:
    demo = "--demo" in sys.argv
    if demo:
        ex, orders = demo_inputs()
        out = ROOT / "data" / "annotation_package_demo"
    else:
        ex = pd.read_csv(ROOT / "data" / "annotation" / "excerpts.csv")
        orders = pd.read_csv(ROOT / "data" / "annotation" / "orders.csv")
        out = ROOT / "data" / "annotation_package"
    shared = out / "_audio"
    shared.mkdir(parents=True, exist_ok=True)
    audio = audio_paths()
    meta = {}
    for r in ex.itertuples():
        t = ROOT / "data" / ("regions_transcription" if r.round == 1 else "regions_v2/transcription")
        s0 = max(0.0, r.start_s - PAD)
        dur = (r.end_s + PAD) - s0
        cut(ROOT / audio[r.item_id], shared / f"{r.excerpt}_mix.wav", s0, dur)
        voice = t / "vocals" / r.region / f"{r.item_id}.wav"
        if voice.exists():
            cut(voice, shared / f"{r.excerpt}_voice.wav", s0, dur)
        a, b = round(r.start_s - s0, 2), round(r.end_s - s0, 2)
        clicks(shared / f"{r.excerpt}_guide.wav", dur, [a, b])
        meta[r.excerpt] = dict(start=a, end=b, clip=round(dur, 2), voice=voice.exists(),
                               calibration=r.role == "calibration")
    guideline = (ROOT / "docs" / "annotation_guideline.md").read_text()
    examples = (ROOT / "docs" / "jianpu_examples.txt").read_text()
    template = (ROOT / "src" / "annotation" / "portal_template.html").read_text()
    regions = [dict(code=c, zh=zh, en=en) for c, zh, en, *_ in REGIONS]
    for k, g in orders.groupby("notator"):
        d = out / k
        (d / "audio").mkdir(parents=True, exist_ok=True)
        for e in g.excerpt:
            for f in shared.glob(f"{e}_*.wav"):
                dst = d / "audio" / f.name
                if dst.exists():
                    dst.unlink()
                os.link(f, dst)
        cfg = dict(notator=k, study_version=STUDY_VERSION + ("-DEMO" if demo else ""),
                   guideline_sha256=hashlib.sha256(guideline.encode()).hexdigest(), guideline=guideline,
                   jianpu_examples=examples, regions=regions, pay="",
                   order=[dict(position=int(p), excerpt=e, **meta[e]) for p, e in zip(g.position, g.excerpt)])
        html = template.replace("/*__CONFIG__*/", json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"))
        (d / "index.html").write_text(html)
        (d / "GUIDELINE.md").write_text(guideline)
        (d / "jianpu_examples.txt").write_text(examples)
        (d / "README.txt").write_text(
            f"Notator {k}: open index.html in Chrome, Firefox or Safari. It works offline.\n"
            "Keep this folder together: the page plays the files in audio/.\n"
            "Times are measured from the start of each E##_mix.wav. The audio is for this task only:\n"
            "do not share it, and delete it when the task is finished.\n")
    print(len(ex), "excerpts,", orders.notator.nunique(), "notator packages →", out)


if __name__ == "__main__":
    main()
