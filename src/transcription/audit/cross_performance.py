"""
In-domain check D: cross-performance consistency.

The curation allows up to 3 recordings of the same song per region. Transcriptions of two performances
of the same song should share a melody (after transposition) far more than two different songs from the
same region, which share only style/mode. The gap (same − different) measures how much melodic identity
the transcriptions preserve, with no ground truth needed.

  same   all pairs of recordings with the same song_name in a region
  diff   for each same-pair, a random pair from the same region with different song names (matched count)
Metric: global transposition-invariant melodic agreement of skeletons (audit/melody.py), on the first
`max_len` skeleton notes (the first verse(s)).

Run (py312): python src/transcription/audit/cross_performance.py [--variants primary,game_pp,rosvot]
"""

import argparse
import os
import itertools
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from melody import load_notes, melodic_agreement, skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "data" / "regions_transcription"
# AQ_INDEX: alternative index, e.g. data/colour_regions/transcription_index.csv (rounds 1 + 2); AQ_TAG names the output
INDEX = Path(os.environ.get("AQ_INDEX", T / "dataset_index.csv"))
TAG = os.environ.get("AQ_TAG", "")
OUT = ROOT / "data" / "transcription" / "audit"
COLS = {"primary": "midi_path", "game_pp": "midi_game_path", "rosvot": "midi_rosvot_path"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="primary,game_pp,rosvot")
    ap.add_argument("--max-len", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    idx = pd.read_csv(INDEX)
    idx = idx[idx.transcription_model != "yourmt3"]  # vocal melodies only

    same, diff = [], []
    for region, g in idx.groupby("region"):
        for song, gs in g.groupby("song_name"):
            for a, b in itertools.combinations(gs.index, 2):
                same.append((a, b))
                others = g[g.song_name != song].index.tolist()
                if len(others) >= 2:
                    diff.append(tuple(rng.sample(others, 2)))

    cache = {}

    def sk(i, var):
        key = (i, var)
        if key not in cache:
            p = idx.loc[i, COLS[var]] if var in COLS else str(
                (T / "midi" / var / idx.loc[i, "region"] / f"{idx.loc[i, 'video_id']}.mid").relative_to(ROOT))
            p = p if isinstance(p, str) and (ROOT / p).exists() else None
            cache[key] = skeleton(load_notes(ROOT / p), 0.08)[: args.max_len] if isinstance(p, str) else np.array([])
        return cache[key]

    rows = []
    for var in args.variants.split(","):
        for kind, pairs in [("same", same), ("diff", diff)]:
            for a, b in pairs:
                rows.append({"variant": var, "kind": kind, "region": idx.loc[a, "region"],
                             "acc": melodic_agreement(sk(a, var), sk(b, var))["acc"]})
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / f"cross_performance{TAG}.csv", index=False)
    print(f"{len(same)} same-song pairs, {len(diff)} different-song control pairs")
    t = d.pivot_table(index="variant", columns="kind", values="acc", aggfunc="mean")
    t["gap"] = t["same"] - t["diff"]
    print(t.round(3).to_string())


if __name__ == "__main__":
    main()
