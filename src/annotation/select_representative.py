"""
A small representative subset per colour region for human annotation (author request 2026-10-18): N recordings per
region (default 4; 3-5), chosen from metadata only, reproducibly.

Eligible: core subset; 60-420 s; speech share < 0.2; link alive at the latest check; vocal primary transcription
(not the instrumental fallback); song label not disputed; not a CREM / Europeana item (links-only).
Representative: picks walk down the region's most frequent genres (song_genre), one genre per pick while genres last,
so the subset mirrors what the region's recordings actually contain.
Diverse: every pick has a new channel ∪ singer group (group_id), a new song and a new singer; at most one item from the
Musical Map of China series per region (it is a single studio production).
Trustworthy first: tier A1/A2 > B > C, tradition bearer / field > 民族唱法 > other, then cleaner voice (vocal_db),
then a random tie-break (fixed seed).

Output: data/annotation/representative_subset.csv (one row per recording: link, start/end for a 30 s excerpt at 25%
of the duration, metadata the annotator may see, and the reason it was picked).
Run (py312): python src/annotation/select_representative.py [--per-region 4]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261018
TIER = {"A1": 0, "A2": 0, "B": 1, "C": 2}
PERF = {"原生态": 0, "field": 0, "民族唱法": 1}
SERIES = "series:musical_map_of_china"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-region", type=int, default=4)
    k = ap.parse_args().per_region
    rng = np.random.default_rng(SEED)
    r = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    link = pd.read_csv(ROOT / "metadata" / "link_status.csv")
    alive = set(link.loc[link.available.astype(str).str.lower() == "true", "item_id"])
    pool = r[r.core & r.duration_s.between(60, 420) & (r.speech_share.fillna(0) < 0.2) & r.item_id.isin(alive)
             & (r.transcription_model != "yourmt3") & (r.song_label_check != "disputed")
             & (r.platform != "europeana")].copy()  # CREM items are links-only: their annotations could not be released
    pool["series"] = pool.feature_flags.fillna("").str.contains(SERIES)
    pool["rank"] = (pool.provenance_tier.map(TIER).fillna(3) * 10 + pool.performance_type.map(PERF).fillna(2) * 3
                    - pool.vocal_db.fillna(0).clip(-20, 40) / 20 + rng.random(len(pool)) * 0.5)
    rows = []
    for reg, g in pool.groupby("region"):
        genres = r[(r.region == reg) & r.core].song_genre.value_counts().index.tolist()
        g = g.sort_values("rank")
        picked, groups, songs, singers, series_used = [], set(), set(), set(), False
        gi = 0
        while len(picked) < k:
            want = genres[gi] if gi < len(genres) else None
            gi += 1
            cand = g[~g.item_id.isin([p["item_id"] for p in picked]) & ~g.group_id.isin(groups)
                     & ~g.song_key.isin(songs) & ~(g.singer_id.isin(singers) & g.singer_id.notna())]
            if series_used:
                cand = cand[~cand.series]
            c = cand[cand.song_genre == want] if want is not None else cand
            if not len(c):
                if want is not None and gi <= len(genres):
                    continue  # no usable recording of this genre; try the next genre
                c = cand
            if not len(c):
                break
            x = c.iloc[0]
            why = f"genre #{genres.index(x.song_genre) + 1 if x.song_genre in genres else '-'} of the region " \
                  f"({x.song_genre}); tier {x.provenance_tier}; {x.performance_type}"
            picked.append(dict(x, pick_reason=why))
            groups.add(x.group_id)
            songs.add(x.song_key)
            if pd.notna(x.singer_id):
                singers.add(x.singer_id)
            series_used |= bool(x.series)
        rows += picked
        if len(picked) < 3:
            print(f"WARNING {reg}: only {len(picked)} eligible picks")
    d = pd.DataFrame(rows)
    d["excerpt_start_s"] = (d.duration_s * 0.25).round(1)
    d["excerpt_end_s"] = (d.excerpt_start_s + 30).clip(upper=d.duration_s).round(1)
    cols = ["region_en", "region", "item_id", "url", "platform", "round", "duration_s", "excerpt_start_s",
            "excerpt_end_s", "song_name", "song_genre", "song_genre_native", "song_class", "province", "county_or_area",
            "ethnic_group", "performance_type", "provenance_tier", "singer_id", "group_id", "feature_flags",
            "transcription_model", "vocal_db", "song_label_check", "pick_reason"]
    out = ROOT / "data" / "annotation" / "representative_subset.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    d[cols].sort_values(["region_en", "song_genre"]).to_csv(out, index=False)
    print(len(d), "recordings,", d.region_en.nunique(), "regions →", out)
    print(d.groupby("region_en").agg(n=("item_id", "size"), genres=("song_genre", "nunique"),
                                     series=("feature_flags", lambda s: s.fillna("").str.contains(SERIES).sum()),
                                     tierAB=("provenance_tier", lambda s: s.isin(["A1", "A2", "B"]).sum()),
                                     rounds=("round", lambda s: "".join(map(str, sorted(set(s)))))).to_string())


if __name__ == "__main__":
    main()
