"""
Pre-commit checks for the Colour Regions release tables. Run after the rebuild, before committing or uploading.
Exit code 1 if any ERROR; WARN lines need a look but do not block.

Run (repo root, py312): python .claude/skills/colour-regions-curation/scripts/check_release.py
"""

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

VOCAB = {
    "provenance_tier": {"A1", "A2", "B", "C"},
    "performance_type": {"原生态", "field", "民族唱法", "instrumental", "other"},
    "dating_flag": {"traditional", "check", "composed"},
    "song_class": {"folk_traditional", "folk_adapted", "folk_style_composed", "composed", "court", "religious",
                   "narrative_quyi", "opera", "instrumental", "unknown"},
    "song_genre": {"work_song", "mountain_song", "field_song", "ditty", "song_and_dance", "ritual_custom", "narrative",
                   "children", "long_song", "short_song", "multipart", "religious", "other"},
    "composition_period": {"traditional_undated", "ming", "qing", "republic", "prc_1949_1965", "prc_1966_1976",
                           "prc_1977_1999", "after_2000", "unknown"},
    "composition_year_kind": {"composition", "adaptation", "first_publication", "first_recording", "collection",
                              "earliest_attestation"},
    "song_label_confidence": {"high", "medium", "low"},
    "subset": {"core", "folk_style_composed", "excluded"},
    "song_label_check": {"verified", "reviewed", "corrected", "disputed", "unchecked"},
}
PERIOD = [(1368, 1644, "ming"), (1644, 1912, "qing"), (1912, 1949, "republic"), (1949, 1966, "prc_1949_1965"),
          (1966, 1977, "prc_1966_1976"), (1977, 2000, "prc_1977_1999"), (2000, 3000, "after_2000")]
n_err = 0


def err(msg):
    global n_err
    n_err += 1
    print("ERROR", msg)


def warn(msg):
    print("WARN ", msg)


def main() -> None:
    from colour_regions.regions import EN
    r = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    m = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    print(f"{len(r)} recordings, {r['round'].nunique()} rounds")
    if r.item_id.duplicated().any():
        err(f"duplicate item_id: {r.item_id[r.item_id.duplicated()].tolist()[:5]}")
    if set(r.item_id) != set(m.item_id):
        err("metadata/recordings.csv is out of date: run export_metadata.py")
    bad = set(r.region) - set(EN)
    if bad:
        err(f"unknown region names: {bad}")
    for c, voc in VOCAB.items():
        if c in r:
            x = r[c].dropna()
            x = x[~x.astype(str).isin(voc)]
            if len(x):
                err(f"{c}: values outside the vocabulary {sorted(set(x.astype(str)))[:6]}")
    miss = r[r.song_class.isna()]
    if len(miss):
        warn(f"{len(miss)} recordings without song labels (new songs?): run song_table.py, label them, "
             f"run song_labels_check.py — e.g. {miss.song_name.head(5).tolist()}")
    if r.transcription_model.isna().any():
        warn(f"{int(r.transcription_model.isna().sum())} recordings without a transcription (pipeline not run?)")
    # song labels: period consistent with year; folk songs have no composer
    s = pd.read_csv(ROOT / "data" / "colour_regions" / "song_labels.csv")
    for row in s.itertuples():
        if pd.notna(row.year_best) and row.composition_period not in ("traditional_undated", "unknown"):
            y = int(row.year_best)
            want = next((p for a, b, p in PERIOD if a <= y < b), None)
            start = next((a for a, b, p in PERIOD if p == row.composition_period), None)
            if row.year_kind in ("composition", "adaptation") and want and want != row.composition_period:
                err(f"{row.song_id} {row.song_name}: {row.year_kind} year {y} but period {row.composition_period}")
            elif start and y < start:  # an attestation year cannot precede the period of origin
                err(f"{row.song_id} {row.song_name}: {row.year_kind} year {y} before period {row.composition_period}")
        if row.song_class == "folk_traditional" and pd.notna(row.composer):
            err(f"{row.song_id} {row.song_name}: folk_traditional with a composer ({row.composer})")
        if pd.notna(row.year_best) and pd.isna(row.year_kind):
            err(f"{row.song_id} {row.song_name}: year without year_kind")
    ids = pd.read_csv(ROOT / "data" / "colour_regions" / "song_labels" / "song_ids.csv")
    if ids.song_id.duplicated().any() or ids.duplicated(["region", "song_key"]).any():
        err("song_ids.csv: duplicate ids or keys (never edit ids by hand)")
    # privacy: no private singer names in released free text
    from colour_regions.privacy import private_names
    public = {x for v in r.loc[r.provenance_tier == "A1", "singer"].dropna() for x in re.split(r"[、,，/ ]+", v)}
    names = private_names(public)
    if m.singer.notna().sum() > (r.provenance_tier == "A1").sum():
        err("metadata/recordings.csv has singer names outside tier A1")
    for f, col in (("metadata/recordings.csv", "provenance_evidence"), ("metadata/song_labels.csv", "evidence")):
        t = pd.read_csv(ROOT / f)
        hits = {n for v in t[col].dropna().astype(str) for n in names if n in v}
        sl = pd.read_csv(ROOT / "metadata" / "song_labels.csv")
        credited = {x for c in ("composer", "lyricist", "arranger") for v in sl[c].dropna()
                    for x in re.split(r"[、,，/;；() ]+", v) if x}
        hits -= credited
        if hits:
            err(f"{f} {col}: private singer names {sorted(hits)[:8]} — rebuild (privacy.py) or add to region rules")
    print("OK" if n_err == 0 else f"{n_err} error(s)")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
