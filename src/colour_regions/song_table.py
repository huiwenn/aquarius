"""
Song-level input table for the song-labelling research (composer, period of composition, song class, genre).

One row per song = (colour region, song_key) over rounds 1-3 (round 3 = eligible Musical Map of China items, from
data/rhymoi/rhymoi_items.csv). Each row carries the evidence we already hold, so the research agents start from it:
  - curator metadata (genre, performance type, places, ethnic group) and two example video titles
  - Musical Map of China description fields (composer / lyricist lines, 体裁)
  - Anthology of Chinese Folk Songs matches by normalised title, with the score's volume and the GENRE SECTION
    inferred from the volume order (anthology_sections() below)
  - round-1 dating (data/regions_curated/song_dates/all_songs.csv), WITHHELD for a random 25% of round-1 songs
    (blind = True) so the new labels can be checked against the old ones

Also writes data/colour_regions/anthology_sections.csv (every Anthology score with its inferred section).

Genre vocabulary (folk-song genres as classified in 《中国民间歌曲集成》, plus minority genres):
  work_song 号子 · mountain_song 山歌 (信天游, 花儿, 爬山调, 飞歌 …) · field_song 田歌/秧田歌 · ditty 小调 ·
  song_and_dance 灯歌/歌舞曲 (花灯, 采茶, 秧歌, 锅庄, 弦子, 堆谐 …) · ritual_custom 风俗/仪式歌 (婚嫁, 哭嫁, 酒歌, 祭祀) ·
  narrative 叙事歌 · children 儿歌/摇篮曲 · long_song 长调 · short_song 短调 · multipart 多声部 (侗族大歌 …) ·
  religious 宗教歌曲 · other

Song ids are stable: data/colour_regions/song_labels/song_ids.csv is the registry (never edit ids by hand).
Run (py312): python src/colour_regions/song_table.py
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from colour_regions.regions import EN  # noqa: E402
from regionclf.corpus import norm_title  # noqa: E402

OUT = ROOT / "data" / "colour_regions" / "song_labels"
SEED = 20261008

# title keyword → genre (first match wins; order matters: specific before general)
GENRE_WORDS = [
    ("long_song", r"长调|乌日汀哆"), ("short_song", r"短调|宝古尔"),
    ("multipart", r"大歌|多声部|复调"),
    ("work_song", r"号子|夯歌|打夯|硪歌|船工|纤夫|搬运|车水|打麦|劳动歌|打场"),
    ("children", r"儿歌|童谣|摇篮|催眠|摇儿|哄娃|月光光"),
    ("ritual_custom", r"哭嫁|嫁歌|婚|丧|祭|神歌|拜|敬酒|酒歌|劝酒|祝酒|迎客|送客|拦门|礼歌|祝福|吉祥|开天门|梯玛|仪式"),
    ("narrative", r"叙事|长诗|唱本|古歌"),
    ("song_and_dance", r"花灯|灯歌|灯调|采茶|花鼓|秧歌|旱船|莲湘|锅庄|弦子|堆谐|踏歌|舞曲|歌舞|囊玛"),
    ("field_song", r"田歌|秧歌号|插秧|薅草|栽秧|耘田|车水歌|田秧"),
    ("mountain_song", r"山歌|信天游|顺天游|花儿|爬山调|山曲|飞歌|漫瀚调|^.{1,6}令$|对歌"),
    ("ditty", r"小调|小曲|五更|十二月|四季|绣荷包|调$"),
]


def genre_from_title(t: str) -> str | None:
    t = str(t or "")
    return next((g for g, pat in GENRE_WORDS if re.search(pat, t)), None)


def anthology_sections() -> pd.DataFrame:
    """The volumes print songs grouped by genre section (号子, 山歌, 小调, …) in a fixed order. Order the scores of a
    volume by their number, label the titles that contain a genre word, and fill each run between two anchors that
    carry the same label. Titles between anchors with different labels stay unknown (a section boundary lies there)."""
    s = pd.read_csv(ROOT / "data" / "colour_regions" / "scores.csv")
    a = s[s.source == "anthology"].copy()
    a["num"] = a.item_id.str.extract(r"/(\d+)_").astype(float)
    a = a.sort_values(["volume", "num"])
    a["anchor"] = a.title.map(genre_from_title)
    out = []
    for vol, g in a.groupby("volume", sort=False):
        lab = g.anchor.tolist()
        idx = [i for i, x in enumerate(lab) if x]
        fill = list(lab)
        for i, j in zip(idx, idx[1:]):
            if lab[i] == lab[j]:
                for k in range(i + 1, j):
                    fill[k] = lab[i]
        out.append(g.assign(section=fill, section_source=["title" if x else ("run" if f else None)
                                                          for x, f in zip(lab, fill)]))
    a = pd.concat(out)
    return a[["item_id", "volume", "num", "province", "title", "song_key", "region", "section", "section_source"]]


def round3() -> pd.DataFrame:
    it = pd.read_csv(ROOT / "data" / "rhymoi" / "rhymoi_items.csv")
    it = it[it.eligible & ~it.in_round1]
    name = it.title.str.extract(r"《\s*([^》]+?)\s*》")[0].str.split(r"\s*\.\s*").str[0]
    from colour_regions.build_release import song_key
    return pd.DataFrame({"item_id": it.item_id, "round": 3, "region": it.region, "song_name": name,
                         "song_key": [song_key(n, i) for n, i in zip(name, it.item_id)], "title": it.title,
                         "province": it.province, "county_or_area": it.county_or_area, "ethnic_group": it.ethnic_native,
                         "genre": it.genre_native, "performance_type": "原生态"})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    rh = pd.read_csv(ROOT / "data" / "rhymoi" / "rhymoi_items.csv").set_index("item_id")
    r3 = round3()  # only items not yet in the release (recordings.csv already holds built rounds)
    allrec = pd.concat([rec, r3[~r3.item_id.isin(rec.item_id)]], ignore_index=True)
    # songs are keyed by the CURATOR's region: a later region move (region_overrides.csv) must not change song ids
    if "region_curator" in allrec:
        allrec["region"] = allrec.region_curator.fillna(allrec.region)
    allrec["rh_composer"] = allrec.item_id.map(rh.composer)
    allrec["rh_form"] = allrec.item_id.map(rh.form)
    sec = anthology_sections()
    sec.to_csv(ROOT / "data" / "colour_regions" / "anthology_sections.csv", index=False)
    anth = sec.groupby("song_key").apply(lambda g: "; ".join(
        f"{v}#{int(n)}:{s or '?'}" for v, n, s in zip(g.volume, g.num, g.section))[:300], include_groups=False)
    dates = pd.read_csv(ROOT / "data" / "regions_curated" / "song_dates" / "all_songs.csv")
    dates["song_key"] = dates.song_name.map(norm_title)
    dates = dates.drop_duplicates(["region", "song_key"]).set_index(["region", "song_key"])

    def j(x, n=6):
        v = [str(y) for y in pd.unique(x.dropna()) if str(y).strip()]
        return "; ".join(v[:n]) or None
    g = allrec.groupby(["region", "song_key"])
    t = pd.DataFrame({
        "song_name": g.song_name.agg(lambda s: s.mode().iat[0] if s.notna().any() else None),
        "alt_names": g.song_name.agg(j), "n_recordings": g.size(), "item_ids": g.item_id.agg(j, n=50),
        "rounds": g["round"].agg(lambda s: ",".join(str(int(x)) for x in sorted(set(s)))),
        "provinces": g.province.agg(j), "places": g.county_or_area.agg(j), "ethnic_groups": g.ethnic_group.agg(j),
        "genre_meta": g.genre.agg(j), "performance_types": g.performance_type.agg(j),
        "example_titles": g.title.agg(lambda s: " || ".join(str(x)[:110] for x in s.dropna().head(2))),
        "curator_dating_flag": g.dating_flag.agg(j), "rhymoi_composer": g.rh_composer.agg(j),
        "rhymoi_form": g.rh_form.agg(j)}).reset_index()
    t["region_en"] = t.region.map(EN)
    t["generic_title"] = t.song_key.str.contains("#")
    t["title_genre"] = t.song_name.map(genre_from_title)
    t["anthology_matches"] = t.song_key.map(anth)
    # round-1 dating as prior evidence, withheld for a blind 25% of the round-1 songs
    has = [(r, k) in dates.index for r, k in zip(t.region, t.song_key)]
    # stable song ids and the frozen blind set: registry song_ids.csv (song_id, region, song_key, blind).
    # Existing songs keep their id; a new song gets the next free number (never reused).
    reg_p = OUT / "song_ids.csv"
    reg = pd.read_csv(reg_p) if reg_p.exists() else pd.DataFrame(columns=["song_id", "region", "song_key", "blind"])
    known = {(r, k): (i, b) for i, r, k, b in zip(reg.song_id, reg.region, reg.song_key, reg.blind)}
    nxt = 1 + max([int(i.split("-")[1]) for i in reg.song_id] or [-1])
    ids, blind, new = [], [], []
    for r, k in zip(t.region, t.song_key):
        if (r, k) in known:
            i, b = known[(r, k)]
        else:
            i, b = f"{EN[r][:3].upper()}-{nxt:04d}", False  # new songs are never blind
            nxt += 1
            new.append(dict(song_id=i, region=r, song_key=k, blind=b))
        ids.append(i)
        blind.append(bool(b))
    t["song_id"], t["blind"] = ids, blind
    if new:
        pd.concat([reg, pd.DataFrame(new)], ignore_index=True).to_csv(reg_p, index=False)
    print(len(new), "new songs added to", reg_p.name)
    cols = ["song_type", "origin_period", "composer_or_adapter", "composition_or_adaptation_year", "date_best",
            "confidence", "evidence_urls"]
    for c in cols:
        t["prior_" + c] = [dates.loc[(r, k), c] if h and not b else None
                           for r, k, h, b in zip(t.region, t.song_key, has, t.blind)]
    t.to_csv(OUT / "input_all.csv", index=False)
    for r, gg in t.groupby("region"):
        gg.to_csv(OUT / f"input_{EN[r].replace('–', '-').replace(' ', '_')}.csv", index=False)
    print(len(t), "songs;", int(t.generic_title.sum()), "generic titles;", int(t.anthology_matches.notna().sum()),
          "with an Anthology title match;", int(t.blind.sum()), "blind round-1 songs")
    print("anthology sections:", sec.section.notna().mean().round(3), "of scores labelled;",
          sec.section.value_counts().to_dict())
    print(t.groupby("region_en").size().to_string())


if __name__ == "__main__":
    main()
