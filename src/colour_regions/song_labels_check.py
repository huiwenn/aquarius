"""
Check and merge the song labels (docs/song_labelling_protocol.md).

Inputs:  data/colour_regions/song_labels/input_all.csv, labels_<Region>.csv (research agents),
         data/regions_curated/song_dates/all_songs.csv (round-1 dating; withheld from agents for blind songs)
Outputs: data/colour_regions/song_labels.csv      one row per song, validated vocabulary
         data/colour_regions/song_labels/review.csv  rows that fail a check, with the reason
Prints the cross-validation: blind round-1 agreement, Anthology agreement, description and curator consistency.
Run (py312): python src/colour_regions/song_labels_check.py
"""

import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from regionclf.corpus import norm_title  # noqa: E402

D = ROOT / "data" / "colour_regions" / "song_labels"
CLASSES = {"folk_traditional", "folk_adapted", "folk_style_composed", "composed", "court", "religious",
           "narrative_quyi", "opera", "instrumental", "unknown"}
GENRES = {"work_song", "mountain_song", "field_song", "ditty", "song_and_dance", "ritual_custom", "narrative",
          "children", "long_song", "short_song", "multipart", "religious", "other"}
PERIODS = {"traditional_undated", "ming", "qing", "republic", "prc_1949_1965", "prc_1966_1976", "prc_1977_1999",
           "after_2000", "unknown"}
CONF = {"high", "medium", "low"}
COARSE = {"folk_traditional": "traditional", "folk_adapted": "adapted", "folk_style_composed": "composed",
          "composed": "composed", "traditional": "traditional", "traditional-adapted": "adapted",
          "newly-composed-folk-style": "composed"}
# Anthology inferred sections are coarse: field songs sit inside the mountain-song section in most volumes
FAMILY = {"field_song": "mountain_song", "long_song": "mountain_song", "short_song": "ditty"}
VOL_PROV = {"guangdong": "广东", "hainan": "海南", "hebei1": "河北", "hebei2": "河北", "henan": "河南", "jiangsu1": "江苏",
            "jiangsu2": "江苏", "jilin": "吉林", "shanghai": "上海", "sichuan1": "四川", "tianjin": "天津"}


def main() -> None:
    inp = pd.read_csv(D / "input_all.csv")
    files = sorted(glob.glob(str(D / "labels_*.csv")))
    lab = pd.concat([pd.read_csv(f, dtype=str) for f in files], ignore_index=True) if files else pd.DataFrame()
    print(len(files), "label files;", len(lab), "rows for", len(inp), "songs")
    if not len(lab):
        return
    lab = lab.drop_duplicates("song_id", keep="last")
    m = inp.merge(lab.drop(columns=[c for c in ("song_key", "region", "song_name") if c in lab]), on="song_id",
                  how="left")
    # manual adjudication (data/colour_regions/song_labels/adjudication.csv): field overrides, and accepted reviews
    adj = D / "adjudication.csv"
    adj = pd.read_csv(adj) if adj.exists() else pd.DataFrame(columns=["song_id", "field", "value", "decision", "reason"])
    ov = adj[adj.decision == "override"]
    for r in ov.itertuples():
        m.loc[m.song_id == r.song_id, r.field] = r.value if pd.notna(r.value) else None
    for sid, g in ov.groupby("song_id"):  # one note per song, listing the fields changed
        note = f" [adjudicated ({', '.join(g.field)}): {g.reason.iloc[0]}]"
        m.loc[m.song_id == sid, "evidence"] = m.loc[m.song_id == sid, "evidence"].fillna("") + note
    accepted = set(adj[adj.decision == "accept"].song_id)
    rev = []

    def flag(rows, why):
        for r in rows.itertuples():
            rev.append(dict(song_id=r.song_id, region=r.region, song_name=r.song_name, reason=why,
                            song_class=getattr(r, "song_class", None), composer=getattr(r, "composer", None),
                            evidence=getattr(r, "evidence", None)))

    flag(m[m.song_class.isna()], "missing label")
    for col, voc in (("song_class", CLASSES), ("genre", GENRES), ("composition_period", PERIODS),
                     ("confidence", CONF)):
        bad = m[m[col].notna() & ~m[col].isin(voc)]
        flag(bad, f"{col} not in vocabulary")
    # protocol rule 2: folk songs have no composer
    flag(m[(m.song_class == "folk_traditional") & m.composer.notna()], "folk_traditional with a composer")
    # names need a source other than knowledge
    named = m.composer.notna() | m.lyricist.notna() | m.arranger.notna()
    flag(m[named & (m.sources.fillna("").str.strip() == "knowledge")], "name with knowledge-only source")

    # 1. blind round-1 subset vs withheld prior dating
    prior = pd.read_csv(ROOT / "data" / "regions_curated" / "song_dates" / "all_songs.csv")
    prior["song_key"] = prior.song_name.map(norm_title)
    prior = prior.drop_duplicates(["region", "song_key"]).set_index(["region", "song_key"])
    b = m[m.blind & m.song_class.notna()].copy()
    b["prior_type"] = [prior.loc[(r, k), "song_type"] for r, k in zip(b.region, b.song_key)]
    b["prior_comp"] = [prior.loc[(r, k), "composer_or_adapter"] for r, k in zip(b.region, b.song_key)]
    b["a"], b["p"] = b.song_class.map(COARSE), b.prior_type.map(COARSE)
    bb = b[b.a.notna() & b.p.notna()]
    print(f"\n[1] blind round-1 songs: {len(b)} labelled; coarse class agreement "
          f"{(bb.a == bb.p).mean():.2f} on {len(bb)} with both labels")
    print(pd.crosstab(bb.p, bb.a, rownames=["prior"], colnames=["new"]).to_string())
    both = b[b.composer.notna() | b.arranger.notna()]
    both = both[both.prior_comp.notna()]
    if len(both):
        same = [any(n and n in str(pc) for n in re.split(r"[、,，/ ]+", f"{c or ''} {a or ''}") if len(n) >= 2)
                for c, a, pc in zip(both.composer.fillna(""), both.arranger.fillna(""), both.prior_comp)]
        print(f"    named author agreement: {sum(same)}/{len(both)}")
    flag(bb[bb.a != bb.p], "blind disagreement with round-1 dating")

    # 2. Anthology
    m["anth_same_prov"] = [isinstance(a, str) and isinstance(p, str) and any(
        VOL_PROV.get(x.split("#")[0], "?") in p for x in a.split("; ")) for a, p in zip(m.anthology_matches, m.provinces)]
    a = m[m.anth_same_prov & m.song_class.notna()]
    print(f"\n[2] Anthology same-province matches: {len(a)} songs; labelled folk (traditional/adapted): "
          f"{a.song_class.isin(['folk_traditional', 'folk_adapted']).mean():.2f}")
    flag(a[~a.song_class.isin(["folk_traditional", "folk_adapted", "unknown"])], "in Anthology (same province) but not folk")

    def sec(s):
        secs = [x.split(":")[-1] for x in str(s).split("; ") if not x.endswith(":?")]
        return pd.Series(secs).mode().iat[0] if secs else None
    g = m[m.anthology_matches.notna() & m.genre.notna()].copy()
    g["sec"] = g.anthology_matches.map(sec)
    g = g[g.sec.notna()]
    fam = g.genre.map(lambda x: FAMILY.get(x, x))
    print(f"    genre vs inferred Anthology section: {(fam == g.sec).mean():.2f} on {len(g)} songs (weak check)")

    # 3. Musical Map of China composer lines; 4. curator 'composed' flags
    c3 = m[m.rhymoi_composer.notna() & (m.song_class == "folk_traditional")]
    print(f"\n[3] description names a composer: {int(m.rhymoi_composer.notna().sum())} songs; labelled "
          f"folk_traditional: {len(c3)}")
    flag(c3, "description names a composer, labelled folk_traditional")
    c4 = m[m.curator_dating_flag.fillna("").str.contains("composed") & (m.song_class == "folk_traditional")]
    print(f"[4] curator flagged composed: {int(m.curator_dating_flag.fillna('').str.contains('composed').sum())}; "
          f"labelled folk_traditional: {len(c4)}")
    flag(c4, "curator flagged composed, labelled folk_traditional")

    print("\nsong_class:", m.song_class.value_counts().to_dict())
    print("genre:", m.genre.value_counts().to_dict())
    print("period:", m.composition_period.value_counts().to_dict())
    print("confidence:", m.confidence.value_counts().to_dict(), "| searched:",
          int(m.searched.astype(str).str.lower().eq("true").sum()))
    print("region_check:", m.region_check.fillna("").str.split(":").str[0].value_counts().to_dict())
    # song_label_check (docs/song_labelling_protocol.md, "Rules added 2026-10-14"):
    #   corrected  changed by an adjudication after an independent review (verification 2026-10-10, review 2 2026-10-14)
    #   disputed   a reviewer raised an issue left for the author (song_labels/disputed.csv)
    #   verified   high/medium-confidence rows (all checked against sources by the 2026-10-10 verifier) or a row a
    #              second reviewer confirmed against a source it read
    #   reviewed   a second reviewer found it consistent with all the evidence, without reading a source
    #   unchecked  the rest
    corrected = set(adj.loc[(adj.decision == "override") & adj.reason.str.contains("Verification|Review2", na=False),
                            "song_id"])
    disputed = set(pd.read_csv(D / "disputed.csv").song_id) if (D / "disputed.csv").exists() else set()
    r2 = [pd.read_csv(f) for f in sorted(D.glob("review2_*.csv"))]
    r2 = pd.concat(r2, ignore_index=True) if r2 else pd.DataFrame(columns=["song_id", "outcome"])
    src_ok = set(r2.loc[r2.outcome == "confirmed_source", "song_id"])
    kept = set(adj.loc[(adj.decision == "accept") & adj.reason.str.contains("Review2", na=False), "song_id"])
    consistent = (set(r2.loc[r2.outcome == "confirmed_consistency", "song_id"])
                  - set(r2.loc[r2.outcome == "issue", "song_id"])) | kept  # issue raised, label kept after review
    m["song_label_check"] = [
        "disputed" if i in disputed else "corrected" if i in corrected
        else "verified" if (c in ("high", "medium") or i in src_ok) else "reviewed" if i in consistent else "unchecked"
        for i, c in zip(m.song_id, m.confidence)]
    print("song_label_check:", m.song_label_check.value_counts().to_dict())
    cols = ["song_id", "region", "region_en", "song_key", "song_name", "item_ids", "n_recordings", "song_class",
            "genre", "genre_native", "composer", "lyricist", "arranger", "composition_period", "year_best",
            "year_kind", "region_check", "evidence", "sources", "confidence", "song_label_check", "searched", "anthology_matches",
            "anth_same_prov", "blind"]
    # evidence text: redact recording singers (privacy.py); credited authors of the song keep their names
    from colour_regions.privacy import private_names, redact
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    public = {x for v in rec.loc[rec.provenance_tier == "A1", "singer"].dropna() for x in re.split(r"[、,，/ ]+", v)}
    names = private_names(public)
    m["evidence"] = [redact(e, names, keep={x for v in (c, l, a) if isinstance(v, str)
                                           for x in re.split(r"[、,，/;；() ]+", v) if x})
                     for e, c, l, a in zip(m.evidence, m.composer, m.lyricist, m.arranger)]
    m[[c for c in cols if c in m]].to_csv(ROOT / "data" / "colour_regions" / "song_labels.csv", index=False)
    r = pd.DataFrame(rev)
    if len(r):
        r["adjudication"] = r.song_id.map(dict(zip(adj.song_id, adj.reason)))
        print(f"adjudicated: {int(r.song_id.isin(accepted).sum())} accepted; "
              f"{int((~r.song_id.isin(accepted)).sum())} open")
    r.to_csv(D / "review.csv", index=False)
    print(f"\nreview: {len(r)} rows →", D / "review.csv")
    if len(r):
        print(r.reason.value_counts().to_string())


if __name__ == "__main__":
    main()
