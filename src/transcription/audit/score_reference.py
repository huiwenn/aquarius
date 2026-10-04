"""
In-domain check B: do transcriptions agree with independently collected folk-song scores
(《中国民间歌曲集成》 Anthology, data/raw/anthology_chinese_folk_songs) more than chance?

Reference set: recordings whose song title exactly matches an Anthology score title AND whose
region is consistent with the score's province volume (a same-titled song from another province is
usually a different tune). The Anthology score is a decades-old variant of the song, not a transcript of
this recording, so absolute agreement is bounded well below 1. The quantity of interest is the gap to chance:
  matched  max melodic agreement over the k same-title scores
  chance   max melodic agreement over k random scores from the same volume(s)   (k matched → fair)
Comparisons are transposition-invariant, ornament-tolerant and semi-global (a one-verse score located
inside a multi-verse performance). See audit/melody.py.

Evaluates several transcription variants side by side (default: primary, GAME, ROSVOT).
Run (py312): python src/transcription/audit/score_reference.py [--variants game_pp,rosvot] [--seed 0]
"""

import argparse
import os
import random
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from melody import load_notes, melodic_agreement, skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ANTH = ROOT / "data" / "raw" / "anthology_chinese_folk_songs"
T = ROOT / "data" / "regions_transcription"
# AQ_INDEX: alternative index, e.g. data/colour_regions/transcription_index.csv (rounds 1 + 2); AQ_TAG names the output
INDEX = Path(os.environ.get("AQ_INDEX", T / "dataset_index.csv"))
TAG = os.environ.get("AQ_TAG", "")
OUT = ROOT / "data" / "transcription" / "audit"

REGION_VOLUMES = {  # 色彩区 → Anthology province volumes that fall inside it
    "东北部平原": ["hebei1", "hebei2", "tianjin", "jilin"],
    "江浙平原": ["jiangsu1", "jiangsu2", "shanghai"],
    "江淮": ["jiangsu1", "jiangsu2"],
    "粤": ["guangdong", "hainan"],
    "客家特区": ["guangdong"],
    "西南高原": ["sichuan1", "sichuan2", "sichuan"],
    "江汉": ["henan"],
}


def title(p: Path) -> str:
    t = re.sub(r"^\d+[_\-\s.]*", "", p.stem)
    return re.sub(r"[（(].*?[)）]", "", t).strip()


def norm(s) -> str:
    return re.sub(r"[《》\s（）()·]", "", str(s)).split("/")[0]


def score_skeleton(p: Path) -> np.ndarray:
    # scores are at a nominal tempo; drop grace notes (< 1/8 beat at 120 bpm ≈ 0.06 s)
    return skeleton(load_notes(p), min_dur=0.06)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="primary,game_pp,rosvot")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    scores = [p for p in ANTH.rglob("*.mid")]
    by_vol: dict[str, list[Path]] = {}
    by_title: dict[str, list[Path]] = {}
    for p in scores:
        by_vol.setdefault(p.parent.name, []).append(p)
        by_title.setdefault(norm(title(p)), []).append(p)

    idx = pd.read_csv(INDEX)
    rows = []
    for r in idx.itertuples():
        vols = REGION_VOLUMES.get(r.region)
        if not vols:
            continue
        cands = [p for p in by_title.get(norm(r.song_name), []) if p.parent.name in vols]
        if not cands:
            continue
        pool = [p for v in vols for p in by_vol.get(v, []) if p not in cands]
        randoms = rng.sample(pool, min(len(pool), len(cands)))
        cand_sk = [score_skeleton(p) for p in cands]
        rand_sk = [score_skeleton(p) for p in randoms]
        for var in args.variants.split(","):
            path = {"primary": r.midi_path, "game_pp": r.midi_game_path,
                    "rosvot": r.midi_rosvot_path}.get(
                var, str((T / "midi" / var / r.region / f"{r.video_id}.mid").relative_to(ROOT)))
            if not isinstance(path, str) or not (ROOT / path).exists():
                continue
            perf = skeleton(load_notes(ROOT / path), min_dur=0.08)
            m = [melodic_agreement(perf, s, local_a=True)["acc"] for s in cand_sk]
            c = [melodic_agreement(perf, s, local_a=True)["acc"] for s in rand_sk]
            rows.append({"region": r.region, "video_id": r.video_id, "song": r.song_name,
                         "variant": var, "k": len(cands), "matched": np.nanmax(m), "chance": np.nanmax(c),
                         "best_score": str(cands[int(np.nanargmax(m))].relative_to(ANTH))})
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / f"score_reference{TAG}.csv", index=False)
    d["gap"] = d.matched - d.chance
    print(f"{d.video_id.nunique()} recordings with region-consistent same-title scores")
    print(d.groupby("variant")[["matched", "chance", "gap"]].agg(["mean", "median"]).round(3).to_string())
    w = d.pivot_table(index="video_id", columns="variant", values="gap")
    print("\nfraction of recordings where matched > chance:",
          d.assign(win=d.gap > 0).groupby("variant").win.mean().round(2).to_dict())
    if {"game_pp", "rosvot"} <= set(w.columns):
        print("GAME better than ROSVOT on", (w.game_pp > w.rosvot).mean().round(2), "of recordings")


if __name__ == "__main__":
    main()
