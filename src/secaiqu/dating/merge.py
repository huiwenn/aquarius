"""
Merge the per-region song-dating tables (data/regions_curated/song_dates/<region>.csv, researched by three agents
with web sources; see docs/region_classification.md §21) into one table with a unified schema, and join to the
dataset index.

Per-region generators (kept for provenance): write_dates_north_han.py (东北 西北 江淮 江浙 闽台),
build_dates_south_han.py (粤 客家 江汉 湘 赣), build_minority_sw.py + research.json (西南高原 and the 4 minority regions).

Output:
  data/regions_curated/song_dates/all_songs.csv                 one row per (region, song_name)
  data/regions_transcription/dataset_index_dated.csv            dataset index + dating columns + `date_best`
`date_best` = composition/adaptation year if known, else earliest attestation year (the lower bound of the
song's existence), else NA. Ranges like "1960-1964" or "1875–1908" are reduced to their first year for date_best,
with the raw string kept.

Run (py312): python src/secaiqu/dating/merge.py
"""

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DIR = ROOT / "data" / "regions_curated" / "song_dates"
COLS = ["region", "song_name", "ethnic_group", "song_type", "origin_period", "earliest_attestation_year",
        "attestation_source", "composer_or_adapter", "composition_or_adaptation_year", "evidence_urls",
        "confidence", "notes"]


def first_year(v):
    if pd.isna(v):
        return pd.NA
    m = re.search(r"(1[5-9]\d\d|20[0-2]\d)", str(v))
    return int(m.group(1)) if m else pd.NA


def main() -> None:
    frames = []
    for f in sorted(DIR.glob("*.csv")):
        if f.name == "all_songs.csv":
            continue
        d = pd.read_csv(f)
        for c in COLS:
            if c not in d.columns:
                d[c] = pd.NA
        frames.append(d[COLS])
    allsongs = pd.concat(frames, ignore_index=True)
    allsongs["comp_year"] = allsongs.composition_or_adaptation_year.map(first_year)
    allsongs["attest_year"] = allsongs.earliest_attestation_year.map(first_year)
    allsongs["date_best"] = allsongs.comp_year.fillna(allsongs.attest_year)
    allsongs.to_csv(DIR / "all_songs.csv", index=False)

    idx = pd.read_csv(ROOT / "data" / "regions_transcription" / "dataset_index.csv")
    out = idx.merge(allsongs.drop(columns=["ethnic_group"]).rename(columns={"notes": "dating_notes"}),
                    on=["region", "song_name"], how="left")
    out.to_csv(ROOT / "data" / "regions_transcription" / "dataset_index_dated.csv", index=False)
    print(f"{len(allsongs)} songs; types: {allsongs.song_type.value_counts().to_dict()}")
    print(f"songs with date_best: {allsongs.date_best.notna().sum()} ({allsongs.date_best.notna().mean():.0%}); "
          f"recordings joined: {out.song_type.notna().sum()}/{len(out)}")
    print("date_best by decade:", allsongs.date_best.dropna().astype(int).floordiv(10).mul(10).value_counts()
          .sort_index().to_dict())


if __name__ == "__main__":
    main()
