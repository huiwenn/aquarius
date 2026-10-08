"""
Export the git-tracked metadata release: links + metadata for every recording, no audio, no derived data.

Input : data/colour_regions/recordings.csv (build_release.py; privacy filtering is already applied there:
        singer names only for listed heritage bearers, names redacted from evidence text)
Output: metadata/recordings.csv            all recordings, release columns only
        metadata/by_region/<Region>.csv    one file per colour region (English name)
        metadata/link_status.csv           latest link check, if available
Run (py312): python src/colour_regions/export_metadata.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "colour_regions"
OUT = ROOT / "metadata"
COLS = ["item_id", "round", "platform", "url", "title", "channel", "channel_key", "upload_date", "duration_s",
        "region", "region_en", "region_code", "region_type", "province", "county_or_area", "geo_level", "lon", "lat",
        "ethnic_group", "ethnic_subgroup", "song_name", "song_key", "genre", "performance_type", "singer",
        "singer_id", "singer_inheritor", "provenance_tier", "provenance_evidence", "feature_flags", "dating_flag", "label_status",
        "speech_share", "core", "core_exclusion", "group_id", "fold"]


def main() -> None:
    rec = pd.read_csv(SRC / "recordings.csv")
    rec = rec[[c for c in COLS if c in rec.columns]]
    (OUT / "by_region").mkdir(parents=True, exist_ok=True)
    rec.to_csv(OUT / "recordings.csv", index=False)
    for en, g in rec.groupby("region_en"):
        g.to_csv(OUT / "by_region" / f"{en.replace('–', '-').replace(' ', '_')}.csv", index=False)
    ls = SRC / "link_status.csv"
    if ls.exists():
        l = pd.read_csv(ls)
        l[l.checked_on == l.checked_on.max()].to_csv(OUT / "link_status.csv", index=False)
    print(len(rec), "recordings,", rec.region_en.nunique(), "region files →", OUT)


if __name__ == "__main__":
    main()
