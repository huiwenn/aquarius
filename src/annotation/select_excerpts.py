"""
Select the excerpts for the expert-notation study (docs/thesis_evidence_plan.md A1; review 02 §2). Run ONCE, after
the plan, the guideline and this script are frozen (dated commit + sha256); the output is frozen the same way.

Design (author decisions 2026-10-02):
  - eligibility uses METADATA ONLY (no F0, transcription or other machine output): core subset; vocal performance
    (not instrumental/other); the dominant Round-1 commercial channel is excluded from every set
  - base: 1 per colour region (15), preferring Round 2 and tier A1/A2/B
  - 苦音 targets: 8 Northwest Plateau excerpts from 8 different singers/channels (the NW base counts as one)
    Han comparators: 15 from other Han regions (the 10 non-NW Han base excerpts + 5 more), matched on field/studio
  - long-song targets: 8 Northern Steppe 长调 excerpts from 8 different singers/channels (the Steppe base counts if 长调)
    free-rhythm comparators: 15 free-rhythm excerpts from other regions, at most 4 per region, never metred.
    Genre metadata marks free rhythm almost only in the Northwest (信天游, 花儿, 山曲), so free/metred is CODED BY EAR
    by the coordinator beforehand (no pitch display) in data/annotation/free_rhythm_coding.csv
    (item_id, free_rhythm ∈ {free, metred, mixed}); `python select_excerpts.py --candidates` writes the candidate list
  - 1 calibration excerpt (not analysed) + 3 blind repeats (drawn from the base set, re-cut 1–2 s later, new IDs)
  - windows: deterministic start at 25% of the duration (base 30 s, targeted 20 s); a coordinator then moves each
    window to the nearest phrase boundary BY EAR, without any pitch display, and logs the change in `window_note`
  - IDs are random; orders differ per notator; repeats are placed in the last quarter of each order
Output: data/annotation/excerpts.csv, data/annotation/orders.csv
Run (py312): python src/annotation/select_excerpts.py
"""

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261002
FREE = re.compile(r"信天游|散板|长调|牧歌|山曲|爬山调|拉伊|鲁|花儿")
LONG = re.compile(r"长调|乌日汀哆")
HAN = ["东北部平原", "西北部高原", "江淮", "江浙平原", "江汉", "湘", "赣", "闽台", "粤", "客家特区", "西南高原"]


def main() -> None:
    import sys
    rng = np.random.default_rng(SEED)
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    r1 = rec[rec["round"] == 1]
    dominant = r1.channel_key.value_counts().index[0]  # the Round-1 commercial series
    pool = rec[rec.core & rec.performance_type.isin(["原生态", "field", "民族唱法"]) & (rec.channel_key != dominant)].copy()
    pool["text"] = pool.genre.fillna("") + " " + pool.song_name.fillna("") + " " + pool.title.fillna("")
    pool["free"] = pool.text.str.contains(FREE)
    pool["long"] = pool.text.str.contains(LONG)
    pool["field"] = pool.performance_type.isin(["原生态", "field"])
    pool["prio"] = (pool.provenance_tier.map({"A1": 0, "A2": 0, "B": 1}).fillna(2) + (pool["round"] == 1) * 0.5
                    + rng.random(len(pool)))
    pool["who"] = pool.singer_id.fillna(pool.channel_key)  # distinct singers; anonymous → distinct channels
    chosen = {}

    def take(df, n, role, distinct_who=True):
        df = df[~df.item_id.isin(chosen)].sort_values("prio")
        got = []
        seen = {pool.set_index("item_id").loc[i, "who"] for i in chosen if chosen[i] in (role,)}
        for r in df.itertuples():
            if len(got) == n:
                break
            if distinct_who and r.who in seen:
                continue
            got.append(r.item_id)
            seen.add(r.who)
        for i in got:
            chosen[i] = role
        return got

    for reg in pool.region.unique():
        take(pool[pool.region == reg], 1, "base", distinct_who=False)
    base = [i for i, v in chosen.items() if v == "base"]
    nw_base = [i for i in base if pool.set_index("item_id").loc[i, "region"] == "西北部高原"]
    take(pool[pool.region == "西北部高原"], 8 - len(nw_base), "target_kuyin")
    for i in nw_base:
        chosen[i] = "base+target_kuyin"
    han_base = [i for i in base if pool.set_index("item_id").loc[i, "region"] in HAN and i not in nw_base]
    for i in han_base:
        chosen[i] = "base+comp_kuyin"
    want_field = pool.set_index("item_id").loc[[i for i, v in chosen.items() if "kuyin" in v and "target" in v],
                                               "field"].mean()
    comp = pool[pool.region.isin([h for h in HAN if h != "西北部高原"])]
    comp = comp.assign(prio=comp.prio + np.where(comp.field == (want_field >= 0.5), 0, 1))
    take(comp, 15 - len(han_base), "comp_kuyin")
    st_base = [i for i in base if pool.set_index("item_id").loc[i, "region"] == "北方草原文化民歌区"
               and pool.set_index("item_id").loc[i, "long"]]
    for i in st_base:
        chosen[i] = chosen[i] + "+target_long"
    take(pool[(pool.region == "北方草原文化民歌区") & pool.long], 8 - len(st_base), "target_long")
    coding = ROOT / "data" / "annotation" / "free_rhythm_coding.csv"
    if not coding.exists():
        sys.exit("Missing data/annotation/free_rhythm_coding.csv: the coordinator must first code free/metred by ear "
                 "for the candidates written by --candidates. Selection not run.")
    code = pd.read_csv(coding).set_index("item_id").free_rhythm
    free_comp = pool[(pool.item_id.map(code) == "free") & ~pool.long & (pool.region != "北方草原文化民歌区")]
    free_comp = free_comp.sort_values("prio").groupby("region").head(4)  # at most 4 per region
    already = [i for i in chosen if pool.set_index("item_id").loc[i, "free"] and not pool.set_index("item_id").loc[i, "long"]
               and pool.set_index("item_id").loc[i, "region"] != "北方草原文化民歌区"]
    for i in already:
        chosen[i] = chosen[i] + "+comp_long"
    take(free_comp, max(0, 15 - len(already)), "comp_long")
    take(pool, 1, "calibration", distinct_who=False)

    out = pool.set_index("item_id").loc[list(chosen)].reset_index()
    out["role"] = out.item_id.map(chosen)
    length = np.where(out.role.str.startswith("base") | (out.role == "calibration"), 30.0, 20.0)
    out["start_s"] = (0.25 * out.duration_s).clip(lower=2.0).round(2)
    out["end_s"] = (out.start_s + length).clip(upper=out.duration_s).round(2)
    out["window_note"] = ""  # filled by the coordinator after the by-ear adjustment
    reps = out[out.role.str.startswith("base")].sample(3, random_state=SEED).copy()
    reps["role"] = "repeat_of:" + reps.item_id
    reps["start_s"] = (reps.start_s + rng.uniform(1, 2, 3)).round(2)
    reps["end_s"] = (reps.end_s + (reps.start_s - reps.start_s.round(0))).round(2)
    out = pd.concat([out, reps], ignore_index=True)
    ids = rng.permutation(np.arange(1, len(out) + 1))
    out.insert(0, "excerpt", [f"E{i:02d}" for i in ids])
    out.loc[out.role == "calibration", "excerpt"] = "E00"
    cols = ["excerpt", "item_id", "role", "round", "region", "region_en", "genre", "performance_type",
            "provenance_tier", "free", "long", "start_s", "end_s", "window_note"]
    d = ROOT / "data" / "annotation"
    d.mkdir(parents=True, exist_ok=True)
    out[cols].sort_values("excerpt").to_csv(d / "excerpts.csv", index=False)
    rows = []
    main = out[(out.role != "calibration") & ~out.role.str.startswith("repeat")].excerpt.tolist()
    rep_ids = out[out.role.str.startswith("repeat")].excerpt.tolist()
    for k in ("N1", "N2", "N3"):
        order = ["E00"] + list(rng.permutation(main))
        cut = int(len(order) * 0.75)
        tail = order[cut:] + rep_ids
        order = order[:cut] + list(rng.permutation(tail))
        rows += [dict(notator=k, position=i + 1, excerpt=e) for i, e in enumerate(order)]
    pd.DataFrame(rows).to_csv(d / "orders.csv", index=False)
    print(out.role.str.split("+").explode().value_counts().to_string())
    print("excerpts:", len(out), "| unique recordings:", out.item_id.nunique())
    for f in ("excerpts.csv", "orders.csv"):
        print(f, "sha256", hashlib.sha256((d / f).read_bytes()).hexdigest()[:16])


def candidates() -> None:
    """Candidate list for the by-ear free/metred coding: up to 8 per region outside Northern Steppe, chosen by
    metadata only (core, vocal, not the dominant channel), in random order."""
    rng = np.random.default_rng(SEED + 1)
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    dominant = rec[rec["round"] == 1].channel_key.value_counts().index[0]
    p = rec[rec.core & rec.performance_type.isin(["原生态", "field", "民族唱法"]) & (rec.channel_key != dominant)
            & (rec.region != "北方草原文化民歌区")]
    c = p.groupby("region", group_keys=False).apply(lambda g: g.sample(min(8, len(g)), random_state=SEED))
    c = c.sample(frac=1, random_state=SEED)[["item_id", "url"]].assign(free_rhythm="")
    d = ROOT / "data" / "annotation"
    d.mkdir(parents=True, exist_ok=True)
    c.to_csv(d / "free_rhythm_candidates.csv", index=False)
    print(len(c), "candidates → data/annotation/free_rhythm_candidates.csv (fill free_rhythm, save as "
          "free_rhythm_coding.csv)")


if __name__ == "__main__":
    import sys
    candidates() if "--candidates" in sys.argv else main()
