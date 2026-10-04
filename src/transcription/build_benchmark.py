"""
Build a small, fixed benchmark for comparing audio→MIDI models on Chinese singing.

Sources (both already in data/raw, both have note-level ground truth):
  - M4Singer  (wav + .mid per phrase; studio Mandarin pop singing)
  - GTSinger Chinese  (wav + .json note annotations; includes Glissando/Vibrato
    technique groups, the closest thing we have to folk ornamentation)

Output: data/transcription/benchmark/{audio/*.wav, gt/*.csv, index.csv}
gt csv columns: onset,offset,pitch   (seconds, seconds, MIDI number)

Run: conda activate py312 && python src/transcription/build_benchmark.py
"""

import json
import random
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pretty_midi

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "transcription" / "benchmark"
N_PER_SOURCE = 60
SEED = 0


def m4singer_items() -> list[dict]:
    items = []
    for wav in sorted((RAW / "m4singer" / "m4singer").glob("*/*.wav")):
        mid = wav.with_suffix(".mid")
        if mid.exists():
            items.append({"source": "m4singer", "wav": wav, "gt": mid})
    return items


def gtsinger_items() -> list[dict]:
    items = []
    for wav in sorted((RAW / "gtsinger" / "Chinese").glob("*/*/*/*/*.wav")):
        js = wav.with_suffix(".json")
        if js.exists() and "Paired_Speech" not in str(wav):
            items.append({"source": "gtsinger", "wav": wav, "gt": js})
    return items


def vocadito_items() -> list[dict]:
    root = RAW / "vocadito"
    return [{"source": "vocadito", "wav": wav, "gt": root / "Annotations" / "Notes" / f"{wav.stem}_notesA1.csv"}
            for wav in sorted((root / "Audio").glob("*.wav"),
                              key=lambda p: int(p.stem.split("_")[1]))]


def notes_from_vocadito(path: Path) -> list[tuple]:
    df = pd.read_csv(path, header=None, names=["onset", "hz", "dur"])
    return [(r.onset, r.onset + r.dur, float(69 + 12 * np.log2(r.hz / 440))) for r in df.itertuples()]


def notes_from_midi(path: Path) -> list[tuple]:
    pm = pretty_midi.PrettyMIDI(str(path))
    return [(n.start, n.end, n.pitch) for inst in pm.instruments for n in inst.notes]


def notes_from_gtsinger(path: Path) -> list[tuple]:
    notes = []
    for word in json.loads(path.read_text()):
        for p, s, e in zip(word["note"], word["note_start"], word["note_end"]):
            if p > 0 and e > s:  # 0 = rest
                notes.append((s, e, p))
    return notes


def main() -> None:
    rng = random.Random(SEED)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "audio").mkdir(parents=True)
    (OUT / "gt").mkdir(parents=True)

    rows = []
    for items, reader in [(m4singer_items(), notes_from_midi), (gtsinger_items(), notes_from_gtsinger)]:
        for i, it in enumerate(rng.sample(items, N_PER_SOURCE)):
            notes = reader(it["gt"])
            if not notes:
                continue
            clip_id = f"{it['source']}_{i:03d}"
            shutil.copy(it["wav"], OUT / "audio" / f"{clip_id}.wav")
            pd.DataFrame(sorted(notes), columns=["onset", "offset", "pitch"]).to_csv(
                OUT / "gt" / f"{clip_id}.csv", index=False)
            rows.append({"clip_id": clip_id, "source": it["source"], "n_notes": len(notes),
                         "orig_path": str(it["wav"].relative_to(ROOT))})
    # vocadito: all clips (not sampled), plus the second annotator for a human ceiling
    (OUT / "gt_A2").mkdir()
    for i, it in enumerate(vocadito_items()):
        clip_id = f"vocadito_{i:03d}"
        shutil.copy(it["wav"], OUT / "audio" / f"{clip_id}.wav")
        for ann, d in [("A1", "gt"), ("A2", "gt_A2")]:
            notes = notes_from_vocadito(it["gt"].with_name(f"{it['wav'].stem}_notes{ann}.csv"))
            pd.DataFrame(sorted(notes), columns=["onset", "offset", "pitch"]).to_csv(
                OUT / d / f"{clip_id}.csv", index=False)
        rows.append({"clip_id": clip_id, "source": "vocadito", "n_notes": len(notes),
                     "orig_path": str(it["wav"].relative_to(ROOT))})
    pd.DataFrame(rows).to_csv(OUT / "index.csv", index=False)
    print(f"{len(rows)} clips → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
