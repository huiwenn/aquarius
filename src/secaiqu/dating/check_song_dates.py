"""Validate data/regions_curated/song_dates/<region>.csv against the dataset index and summarise.

Usage: python -m src.secaiqu.dating.check_song_dates 东北部平原 西北部高原 ...
(no args = every CSV present in song_dates/)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
INDEX = ROOT / "data/regions_transcription/dataset_index.csv"
OUT = ROOT / "data/regions_curated/song_dates"
COLS = ["song_name", "region", "song_type", "origin_period", "earliest_attestation_year",
        "attestation_source", "composer_or_adapter", "composition_or_adaptation_year",
        "evidence_urls", "confidence", "notes"]
TYPES = {"traditional", "traditional-adapted", "newly-composed-folk-style", "unknown"}


def main(regions):
    idx = pd.read_csv(INDEX)
    regions = regions or sorted(p.stem for p in OUT.glob("*.csv"))
    for r in regions:
        df = pd.read_csv(OUT / f"{r}.csv", dtype=str, keep_default_na=False)
        want = set(idx.loc[idx.region == r, "song_name"])
        got = set(df.song_name)
        assert list(df.columns) == COLS, f"{r}: bad columns"
        assert set(df.song_type) <= TYPES, f"{r}: bad song_type {set(df.song_type) - TYPES}"
        assert set(df.confidence) <= {"high", "medium", "low"}, f"{r}: bad confidence"
        if want != got:
            print(f"{r}: missing {sorted(want - got)} extra {sorted(got - want)}")
        dated = (df.earliest_attestation_year != "NA").mean()
        print(f"{r}: n={len(df)} {df.song_type.value_counts().to_dict()} attested_year={dated:.0%}")


if __name__ == "__main__":
    main(sys.argv[1:])
