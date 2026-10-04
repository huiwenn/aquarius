"""
Build the Colour Regions release tables from the two collection rounds and the score corpora.

Inputs
  Round 1  data/regions_audio/manifest.csv, data/regions_transcription/dataset_index_dated.csv,
           data/regions_curated/v1_provenance.csv (re-curation of round 1 under the round-2 tier rules)
  Round 2  data/regions_v2/manifest.csv, data/regions_v2/transcription/dataset_index.csv (when transcribed)
  Both     <round dir>/speech_screen/speech_screen.csv (src/secaiqu/v2/speech_screen.py)
  Scores   data/regionclf/corpus_anthology.pkl, corpus_essen.pkl (src/regionclf/corpus.py)

Outputs (data/colour_regions/)
  recordings.csv   one row per recording, harmonised fields (see FIELDS), recommended CV fold, and `core`:
                   the default analysis subset = not a clear label error (data/regions_curated/v1_label_review.csv),
                   not a non-traditional arrangement (v1_content_review.csv), not a composed song, not mostly speech
  scores.csv       one row per score (Anthology, Essen) with region and basic statistics
Missing inputs are tolerated: their columns stay empty, so the tables can be rebuilt as work finishes.

Run (py312): python src/colour_regions/build_release.py
"""

import pickle
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from colour_regions.regions import CODE, EN, TYPE  # noqa: E402
from regionclf.corpus import norm_title  # noqa: E402

OUT = ROOT / "data" / "colour_regions"
R1 = ROOT / "data" / "regions_transcription"
R2 = ROOT / "data" / "regions_v2"

FIELDS = ["item_id", "round", "platform", "url", "title", "channel", "channel_key", "upload_date", "duration_s",
          "region", "region_en", "region_code", "region_type", "province", "county_or_area", "ethnic_group", "ethnic_subgroup",
          "song_name", "song_key", "genre", "performance_type", "singer", "singer_id", "singer_inheritor", "provenance_tier", "provenance_tier_curator",
          "provenance_evidence", "dating_flag", "song_type", "label_concern", "content_concern",
          "label_status", "speech_share", "speech_doc_meta", "sung_share", "music_share", "transcription_model", "n_notes",
          "notes_per_s", "vocal_db", "game_rosvot_agreement", "core", "core_exclusion", "group_id", "fold"]
# Speech rule (docs/collection_v2.md, "Speech screen"): the AudioSet classifier also scores unaccompanied, speech-like
# folk singing (elderly singers, 咸水歌, 褒歌, 童谣, 号子) as speech, so speech share alone is not evidence of talk.
# An item leaves the core subset only if BOTH signals agree: speech share ≥ SPEECH_MIN and title or curator note
# marks it as documentary / news / interview / heritage-application film.
SPEECH_MIN = 0.3
DOC_PATTERN = ("申报|纪录|记录片|新闻|采访|访谈|专题|讲述|解说|旁白|介绍|宣传|展播|探访|走进|报道|节目|news|documentar|"
               "interview|narrat|lecture|讲座|commentary|主持|introduc|National Park|boast")


def read(path: Path, **kw) -> pd.DataFrame:
    return pd.read_csv(path, **kw) if path.exists() else pd.DataFrame()


def speech(dir_: Path) -> pd.DataFrame:
    s = read(dir_ / "speech_screen" / "speech_screen.csv")
    return s[["id", "speech_share", "sung_share", "music_share"]].rename(columns={"id": "item_id"}) if len(s) else s


def probe_duration(path: Path) -> float:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(path)], capture_output=True, text=True, check=True).stdout
        return round(float(out.strip()), 3)
    except Exception:
        return np.nan


# Titles that name a genre (optionally after a place), not a song: "客家山歌", "咸水歌", "兴国山歌", "花儿".
# They get a per-item song_key so that different songs of one genre are not treated as one song.
GENERIC = re.compile(r"^.{0,4}(山歌|号子|花儿|小调|民歌|咸水歌|长调|短调|童谣|田歌|茶歌|渔歌|情歌|对歌|大歌|酒歌|"
                     r"牧歌|儿歌|歌谣|小曲|山曲|木卡姆|锅庄|酒曲)$")


def song_key(name, item_id) -> str:
    k = norm_title(name) if pd.notna(name) else ""
    if not k or GENERIC.match(k) or re.search(r"未标|未详|不详|unknown", str(name), re.I):
        return f"{k or 'untitled'}#{item_id}"
    return k


def singer_ids(d: pd.DataFrame) -> pd.Series:
    """Stable pseudonymous id per singer (one id per normalised name, per platform-independent spelling)."""
    def norm(n):
        if pd.isna(n) or not str(n).strip():
            return None
        n = re.sub(r"[（(].*?[)）]", "", str(n))
        return re.sub(r"\s|演唱|领唱|等$", "", n) or None
    names = d.singer.map(norm)
    ids = {n: f"S{i:04d}" for i, n in enumerate(sorted(set(names.dropna())), 1)}
    return names.map(ids)


PROV_ZH = {"Hebei": "河北", "Tianjin": "天津", "Jilin": "吉林", "Jiangsu": "江苏", "Shanghai": "上海", "Guangdong": "广东",
           "Hainan": "海南", "Henan": "河南", "Sichuan": "四川", "Shandong": "山东", "Shanxi": "山西", "Shaanxi": "陕西",
           "Northern Shaanxi": "陕西", "Fujian": "福建", "Gansu": "甘肃", "Yunnan": "云南", "Taiwan": "台湾",
           "Qinghai": "青海", "Hubei": "湖北", "Anhui": "安徽", "Zhejiang": "浙江", "Hunan": "湖南", "Jiangxi": "江西",
           "Guangxi": "广西", "Guizhou": "贵州", "Liaoning": "辽宁", "Heilongjiang": "黑龙江", "Ningxia": "宁夏",
           "Inner Mongolia": "内蒙古"}


def round1() -> pd.DataFrame:
    m = pd.read_csv(ROOT / "data" / "regions_audio" / "manifest.csv")
    m = m[m.status == "ok"]
    idx = read(R1 / "dataset_index_dated.csv")
    prov = read(ROOT / "data" / "regions_curated" / "v1_provenance.csv")
    d = pd.DataFrame({
        "item_id": m.video_id, "round": 1, "platform": "youtube", "url": m.url, "title": m.yt_title.fillna(m.title),
        "channel": m.uploader.fillna(m.channel), "channel_key": "youtube:" + m.channel_id.astype(str),
        "upload_date": m.upload_date, "duration_s": m.duration_s_actual, "region": m.region,
        "province_or_area": m.province_or_area, "ethnic_group": m.ethnic_group, "song_name": m.song_name,
        "genre": m.genre, "performance_type": m.performance_type})
    if len(prov):
        p = prov.rename(columns={"video_id": "item_id"}).drop(columns=["region"]).drop_duplicates("item_id")
        d = d.drop(columns=["ethnic_group"]).merge(p, on="item_id", how="left")
        d["ethnic_group"] = d["ethnic_group"].fillna(d.item_id.map(m.set_index("video_id").ethnic_group))
        d["performance_type"] = d.pop("performance_type_v2").fillna(d["performance_type"])
    else:
        d["province"] = d["province_or_area"]
    if len(idx):
        q = idx.rename(columns={"video_id": "item_id", "game_rosvot_conp": "game_rosvot_agreement"})
        d = d.merge(q[["item_id", "song_type", "transcription_model", "n_notes", "notes_per_s", "vocal_db",
                       "game_rosvot_agreement"]], on="item_id", how="left")
    return d.drop(columns=["province_or_area"]).merge(speech(R1), on="item_id", how="left") if len(speech(R1)) \
        else d.drop(columns=["province_or_area"])


def round2() -> pd.DataFrame:
    m = pd.read_csv(R2 / "manifest.csv")
    m = m[m.status == "ok"]
    plat = m.platform.map({"bili": "bilibili", "yt": "youtube", "europeana": "europeana"})
    m = m.copy()
    m["duration_s_actual"] = [d if pd.notna(d) else probe_duration(ROOT / p)
                              for d, p in zip(m.duration_s_actual, m.audio_path)]
    d = pd.DataFrame({
        "item_id": m.id, "round": 2, "platform": plat, "url": m.url, "title": m.title,
        "channel": m.uploader.fillna(m.channel), "channel_key": plat + ":" + m.channel_id.astype(str),
        "upload_date": m.upload_date, "duration_s": m.duration_s_actual, "region": m.region,
        "province": m.province, "county_or_area": m.county_or_area, "ethnic_group": m.ethnic_group,
        "song_name": m.song_name, "genre": m.genre, "performance_type": m.performance_type, "singer": m.singer,
        "singer_inheritor": m.singer_inheritor, "provenance_tier": m.provenance_tier,
        "provenance_evidence": m.provenance_evidence, "dating_flag": m.dating_flag,
        "content_concern": m.note})
    idx = read(R2 / "transcription" / "dataset_index.csv")
    if len(idx):
        q = idx.rename(columns={"video_id": "item_id", "game_rosvot_conp": "game_rosvot_agreement"})
        d = d.merge(q[["item_id", "transcription_model", "n_notes", "notes_per_s", "vocal_db",
                       "game_rosvot_agreement"]], on="item_id", how="left")
    s = speech(R2)
    return d.merge(s, on="item_id", how="left") if len(s) else d


def add_core(d: pd.DataFrame) -> None:
    cur = ROOT / "data" / "regions_curated"
    lab = read(cur / "v1_label_review.csv")
    con = read(cur / "v1_content_review.csv")
    d["label_status"] = d.item_id.map(dict(zip(lab.video_id, lab.label_status))) if len(lab) else np.nan
    why = pd.Series("", index=d.index)
    why[d.label_status == "exclude"] += "label;"
    if len(con):
        why[d.item_id.isin(con.video_id)] += "arrangement;"
    why[d.dating_flag == "composed"] += "composed;"
    doc = (d.title.fillna("") + " " + d.content_concern.fillna("")).str.contains(DOC_PATTERN, case=False, regex=True)
    d["speech_doc_meta"] = doc
    why[(d.speech_share >= SPEECH_MIN) & doc] += "speech;"
    d["core_exclusion"] = why.str.rstrip(";").replace("", np.nan)
    d["core"] = d.core_exclusion.isna()


def channel_singer_groups(d: pd.DataFrame) -> pd.Series:
    """Connected components of 'same channel' ∪ 'same singer' (union-find): no channel and no named singer
    can then occur on both sides of a split."""
    parent = list(range(len(d)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for col in ("channel_key", "singer_id"):
        first = {}
        for i, v in enumerate(d[col]):
            if pd.isna(v):
                continue
            if v in first:
                parent[find(i)] = find(first[v])
            else:
                first[v] = i
    return pd.Series([find(i) for i in range(len(d))], index=d.index)


def add_folds(d: pd.DataFrame, n_splits: int = 5, seed: int = 0) -> pd.Series:
    """Recommended evaluation folds: stratified by region, grouped by channel ∪ singer components (group_id).
    Training on folds != k must also drop items whose song_key occurs in fold k (src/regionclf/common.folds)."""
    fold = np.full(len(d), -1)
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for k, (_, te) in enumerate(skf.split(np.zeros(len(d)), d.region, d.group_id)):
        fold[te] = k
    return pd.Series(fold, index=d.index)


def scores_table() -> pd.DataFrame:
    rows = []
    for src in ("anthology", "essen"):
        f = ROOT / "data" / "regionclf" / f"corpus_{src}.pkl"
        if not f.exists():
            continue
        for r in pickle.load(open(f, "rb")):
            n = r["notes"]
            rows.append(dict(item_id=f"{src}:{r['item_id']}", source=src, volume=r["subset"] if src == "essen"
                             else r["item_id"].split("/")[0], region=r["region"], region_en=EN[r["region"]],
                             region_code=CODE[r["region"]], province=r["province"], ethnic=r["ethnic"],
                             title=r["title"], song_key=r["group"].removeprefix("t:"), n_notes=len(n),
                             pitch_range=int(n[:, 2].max() - n[:, 2].min()) if len(n) else 0))
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.concat([round1(), round2()], ignore_index=True)
    d["region_en"], d["region_code"], d["region_type"] = d.region.map(EN), d.region.map(CODE), d.region.map(TYPE)
    d["song_key"] = [song_key(n, i) for n, i in zip(d.song_name, d.item_id)]
    d["singer_id"] = singer_ids(d)

    # one spelling per ethnic group: "达斡尔族" → "达斡尔"; "汉族（客家）" → group "汉", subgroup "客家";
    # "回/土/汉" kept as a list
    def split_ethnic(e):
        if pd.isna(e) or not str(e).strip():
            return np.nan, np.nan
        m = re.match(r"^(.*?)\s*[（(](.*?)[)）]\s*$", str(e).strip())
        main, sub = (m.group(1), m.group(2)) if m else (str(e), np.nan)
        main = "/".join(x.strip().removesuffix("族") for x in main.replace("、", "/").split("/"))
        if main in ("疍家", "客家", "闽南", "潮汕"):  # Han subgroups written as the group
            main, sub = "汉", main
        return main, (np.nan if sub == "未详" else sub)
    eth = d.ethnic_group.map(split_ethnic)
    d["ethnic_group"], d["ethnic_subgroup"] = eth.str[0], eth.str[1]
    for c in ("speech_share", "dating_flag"):
        if c not in d:
            d[c] = np.nan
    # tier A split (src/colour_regions/check_inheritors.py): A1 = named singer found on the national heritage-bearer
    # list with a matching province (also upgrades B/C items); A2 = other tier-A items (uploader states the place)
    ih = read(ROOT / "data" / "regions_curated" / "ihchina_items.csv")
    d["provenance_tier_curator"] = d.provenance_tier
    if len(ih):
        on = d.item_id.isin(ih.loc[ih.on_national_list, "item_id"])
        d.loc[on, "provenance_tier"] = "A1"
        d.loc[~on & (d.provenance_tier == "A"), "provenance_tier"] = "A2"
    # names are released only for singers on the national heritage-bearer list (tier A1, a public role);
    # every other singer keeps only the pseudonymous singer_id
    keep = d.provenance_tier == "A1"
    public = set()
    for n in d.loc[keep, "singer"].dropna():
        public |= {x.strip() for x in re.split(r"[、,，/&和与 ]+", str(n))}
    private = sorted({x for n in d.loc[~keep, "singer"].dropna()
                      for x in (re.sub(r"[（(].*?[)）]", "", y).strip() for y in re.split(r"[、,，/&和与 ]+", str(n)))
                      if len(x) >= 2 and not any(x in p for p in public)
                      and re.fullmatch(r"[\u4e00-\u9fff·]+", x)},
                     key=len, reverse=True)  # Chinese-character names only: short Latin strings match inside words
    def redact_all(ev):
        if pd.isna(ev):
            return ev
        for n in private:
            ev = str(ev).replace(n, "[singer]")
        return ev
    d["provenance_evidence"] = d.provenance_evidence.map(redact_all)
    d["singer"] = d.singer.where(keep)
    add_core(d)
    d["group_id"] = channel_singer_groups(d)
    d["fold"] = add_folds(d)
    for c in FIELDS:
        if c not in d:
            d[c] = np.nan
    d[FIELDS].to_csv(OUT / "recordings.csv", index=False)
    if (ROOT / "data" / "geo" / "gazetteer.csv").exists():  # adds geo_level, geo_name, lon, lat
        from colour_regions import geocode
        geocode.main()
    # merged transcription index of both rounds (repo-relative paths) for the audits in src/transcription/audit/
    ix = [read(R1 / "dataset_index.csv").assign(round=1), read(R2 / "transcription" / "dataset_index.csv").assign(round=2)]
    ix = pd.concat([i for i in ix if len(i)], ignore_index=True)
    ix = ix[ix.video_id.isin(d.loc[d.core, "item_id"])]
    ix.to_csv(OUT / "transcription_index.csv", index=False)
    s = scores_table()
    s.to_csv(OUT / "scores.csv", index=False)
    # recording ↔ score links by normalised title (generic genre titles excluded: their song_key has a '#')
    rr = d.loc[~d.song_key.str.contains("#"), ["item_id", "region", "province", "song_key", "core"]]
    sm = rr.merge(s[["item_id", "source", "region", "province", "song_key"]], on="song_key", suffixes=("", "_score"))
    sm = sm.rename(columns={"item_id": "recording_id", "item_id_score": "score_id"})
    sm["same_region"] = sm.region == sm.region_score
    sm["same_province"] = [isinstance(a, str) and isinstance(b, str) and (a[:2] in PROV_ZH.get(b, b))
                           for a, b in zip(sm.province, sm.province_score)]
    sm.to_csv(OUT / "score_matches.csv", index=False)
    print(f"score matches: {len(sm)} pairs, {sm.recording_id.nunique()} recordings, "
          f"{sm[sm.same_region].recording_id.nunique()} with a same-region score, "
          f"{sm[sm.same_province].recording_id.nunique()} with a same-province score")
    print(f"recordings: {len(d)} ({(d['round'] == 1).sum()} round 1, {(d['round'] == 2).sum()} round 2); "
          f"scores: {len(s)}")
    print("core:", int(d.core.sum()), "| exclusions:", d.core_exclusion.value_counts().to_dict())
    print(d.groupby("region_en").agg(n=("item_id", "size"), core=("core", "sum"), channels=("channel_key", "nunique"),
                                     tierAB=("provenance_tier", lambda t: t.isin(["A1", "A2", "A", "B"]).mean())).to_string())


if __name__ == "__main__":
    main()
