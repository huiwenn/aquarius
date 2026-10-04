"""
Unified symbolic corpus for 色彩区 region classification.

Sources (each → one pickle of records under data/regionclf/):
  anthology   《中国民间歌曲集成》 OMR scores (MIDI, 9 province volumes → 5 色彩区). Pitch is 简谱 rendered with
              1=C (movable-do); time in quarter-note beats.
  essen       Essen Folksong Collection, China subset (Humdrum **kern; han / shanxi / natmin / xinhua).
              Region from the !!!ARE province keywords (Han) or the ethnic group (minorities). Real keys; beats.
  trans_<v>   Our transcriptions of the 600 色彩区 recordings, variant v ∈ {primary, game_pp, game_ens3_pp,
              rosvot}. Absolute sung pitch; time in seconds.
  trans_merged  Primary transcriptions of the merged Colour Regions pool (rounds 1 + 2), read through the release
              table data/colour_regions/recordings.csv (src/colour_regions/build_release.py); core subset only. `channel`
              holds the channel ∪ singer group (group_id), so folds follow the release protocol; `round` is kept so round-1 → round-2 transfer can be evaluated.

Record = dict(source, item_id, region, province, group, title, ethnic, channel, time_unit,
              notes=np.ndarray[n, 3] (onset, duration, midi_pitch), sorted by onset, monophonic-ized).
`group` is used for grouped CV: the same song (normalized title) never appears in both train and test.

Run (py312): python src/regionclf/corpus.py [--sources anthology,essen,trans_primary,trans_rosvot,...]
"""

import argparse
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pretty_midi

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from secaiqu.mapping import PROVINCE_TO_SECAIQU  # noqa: E402

OUT = ROOT / "data" / "regionclf"
ANTH = ROOT / "data" / "raw" / "anthology_chinese_folk_songs"
ESSEN = ROOT / "data" / "raw" / "essen" / "asia" / "china"
T = ROOT / "data" / "regions_transcription"

VOLUME_PROVINCE = {"hebei1": "Hebei", "hebei2": "Hebei", "tianjin": "Tianjin", "jilin": "Jilin",
                   "jiangsu1": "Jiangsu", "jiangsu2": "Jiangsu", "shanghai": "Shanghai",
                   "guangdong": "Guangdong", "hainan": "Hainan", "henan": "Henan", "sichuan1": "Sichuan"}

# Essen: province keywords (pinyin as spelled in !!!ARE) → province name used by mapping.py
ESSEN_PROVINCES = {"shanbei": "Northern Shaanxi", "shaanxi": "Shaanxi", "shsanxi": "Shanxi", "shanxi": "Shanxi",
                   "fujian": "Fujian", "hebei": "Hebei", "jiangsu": "Jiangsu", "sichuan": "Sichuan",
                   "henan": "Henan", "gansu": "Gansu", "yunnan": "Yunnan", "taiwan": "Taiwan",
                   "qinghai": "Qinghai", "hubei": "Hubei", "anhui": "Anhui", "zhejiang": "Zhejiang",
                   "shandong": "Shandong", "hunan": "Hunan", "jiangxi": "Jiangxi", "guangdong": "Guangdong",
                   "guangxi": "Guangxi", "guizhou": "Guizhou", "liaoning": "Liaoning", "jilin": "Jilin",
                   "heilongjiang": "Heilongjiang", "ningxia": "Ningxia", "neimeng": "Inner Mongolia"}
# Essen minority ethnic groups → minority 色彩区 (others, e.g. Chaoxian/Korean, are dropped)
ESSEN_ETHNIC = {"menggu": "北方草原文化民歌区", "dawoer": "北方草原文化民歌区", "elunchun": "北方草原文化民歌区",
                "ewenke": "北方草原文化民歌区", "hezhe": "北方草原文化民歌区",
                "weiwuer": "新疆民歌区", "hasake": "新疆民歌区", "keerkezi": "新疆民歌区", "tajike": "新疆民歌区",
                "zang": "藏族民歌区",
                "miao": "西南多民族古老原始文化民歌区", "dong": "西南多民族古老原始文化民歌区",
                "zhuang": "西南多民族古老原始文化民歌区", "yao": "西南多民族古老原始文化民歌区",
                "yi": "西南多民族古老原始文化民歌区", "bai": "西南多民族古老原始文化民歌区",
                "maonan": "西南多民族古老原始文化民歌区", "hani": "西南多民族古老原始文化民歌区",
                "naxi": "西南多民族古老原始文化民歌区", "lisu": "西南多民族古老原始文化民歌区",
                "hui": "西北部高原", "yugu": "西北部高原"}


def norm_title(t: str) -> str:
    t = re.sub(r"^\d+[_\-\s.]*", "", str(t))
    t = re.sub(r"[（(\[].*?[)）\]]", "", t)
    return re.sub(r"[\s《》·,，.。'\"-]", "", t).lower()


def monophonize(notes: np.ndarray) -> np.ndarray:
    """Keep the highest pitch at each onset; cut each note at the next onset."""
    if len(notes) == 0:
        return notes.reshape(0, 3)
    notes = notes[np.lexsort((-notes[:, 2], notes[:, 0]))]
    keep = np.r_[True, np.diff(notes[:, 0]) > 1e-6]
    notes = notes[keep]
    nxt = np.r_[notes[1:, 0], np.inf]
    notes[:, 1] = np.minimum(notes[:, 1], nxt - notes[:, 0])
    return notes[notes[:, 1] > 0]


def midi_notes(path: Path, beats: bool) -> np.ndarray:
    pm = pretty_midi.PrettyMIDI(str(path))
    rows = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            if beats:
                s = pm.time_to_tick(n.start) / pm.resolution
                e = pm.time_to_tick(n.end) / pm.resolution
            else:
                s, e = n.start, n.end
            if e > s:
                rows.append((s, e - s, n.pitch))
    return monophonize(np.array(rows, float)) if rows else np.zeros((0, 3))


def build_anthology() -> list[dict]:
    recs = []
    for p in sorted(ANTH.rglob("*.mid")):
        vol = p.parent.name
        prov = VOLUME_PROVINCE.get(vol)
        region = PROVINCE_TO_SECAIQU.get(prov) if prov else None
        if not region:
            continue
        notes = midi_notes(p, beats=True)
        if len(notes) < 8:
            continue
        title = re.sub(r"^\d+[_\-\s.]*", "", p.stem)
        recs.append(dict(source="anthology", item_id=f"{vol}/{p.stem}", region=region, province=prov,
                         group="t:" + norm_title(title), title=title, ethnic="Han", channel=vol,
                         time_unit="beat", notes=notes, subset=p.parent.parent.name))
    return recs


def essen_meta(path: Path) -> dict:
    meta = {}
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith("!!!OTL:"):
            meta["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("!!!ARE:"):
            meta["are"] = line.split(":", 1)[1].strip()
        elif "Ethnic Group:" in line:
            meta["ethnic"] = line.split(":", 1)[1].strip()
        elif line.startswith("!!!SCT:"):
            meta["sct"] = line.split(":", 1)[1].strip()
    return meta


def essen_region(meta: dict) -> tuple[str | None, str | None]:
    eth = re.sub(r"[^a-z]", " ", meta.get("ethnic", "").lower()).split()
    if eth and eth[0] not in ("han", "ha", "hanzu") and eth[0] in ESSEN_ETHNIC:
        return ESSEN_ETHNIC[eth[0]], None
    if eth and eth[0] not in ("han", "ha", "hanzu") and eth[0] not in ESSEN_ETHNIC:
        return None, None  # a minority we don't map (e.g. Chaoxian)
    are = meta.get("are", "").lower().replace(",", " ")
    for kw, prov in ESSEN_PROVINCES.items():  # 'shanbei' before 'shanxi' (dict order)
        if re.search(rf"\b{kw}\b", are):
            if prov == "Inner Mongolia":
                return "北方草原文化民歌区", prov
            return PROVINCE_TO_SECAIQU.get(prov), prov
    return None, None


def build_essen() -> list[dict]:
    import music21 as m21
    recs = []
    for p in sorted(ESSEN.glob("*/*.krn")):
        meta = essen_meta(p)
        region, prov = essen_region(meta)
        if not region:
            continue
        try:
            s = m21.converter.parse(str(p), format="humdrum")
        except Exception:
            continue
        rows = []
        for n in s.flatten().notes:
            if n.duration.isGrace or n.quarterLength <= 0:
                continue
            pitch = max(p_.midi for p_ in n.pitches)
            rows.append((float(n.offset), float(n.quarterLength), pitch))
        notes = monophonize(np.array(rows, float)) if rows else np.zeros((0, 3))
        if len(notes) < 8:
            continue
        # merge tied continuations: consecutive same pitch with no gap came from ties → merge
        recs.append(dict(source="essen", item_id=f"{p.parent.name}/{p.stem}", region=region, province=prov,
                         group="t:" + norm_title(meta.get("title", p.stem)), title=meta.get("title", p.stem),
                         ethnic=meta.get("ethnic", ""), channel=p.parent.name, time_unit="beat", notes=notes,
                         subset=p.parent.name))
    return recs


def build_transcriptions(variant: str) -> list[dict]:
    idx = pd.read_csv(T / "dataset_index.csv")
    recs = []
    for r in idx.itertuples():
        if variant == "primary":
            path = ROOT / r.midi_path
        else:
            path = T / "midi" / variant / r.region / f"{r.video_id}.mid"
        if not path.exists():
            continue
        notes = midi_notes(path, beats=False)
        if len(notes) < 8:
            continue
        recs.append(dict(source=f"trans_{variant}", item_id=r.video_id, region=r.region, province=None,
                         group="t:" + norm_title(r.song_name), title=r.song_name,
                         ethnic=str(getattr(r, "ethnic_group", "") or ""), channel=str(r.channel),
                         time_unit="sec", notes=notes, subset=r.transcription_model,
                         performance_type=r.performance_type))
    return recs


def build_merged() -> list[dict]:
    rel = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    rel = rel[rel.core]  # the paper's experiments use the core subset
    paths = {}
    for t in (T, ROOT / "data" / "regions_v2" / "transcription"):
        idx = t / "dataset_index.csv"
        if idx.exists():
            for r in pd.read_csv(idx).itertuples():
                paths[r.video_id] = ROOT / r.midi_path
    recs = []
    for r in rel.itertuples():
        path = paths.get(r.item_id)
        if path is None or not path.exists():
            continue
        notes = midi_notes(path, beats=False)
        if len(notes) < 8:
            continue
        recs.append(dict(source="trans_merged", item_id=r.item_id, region=r.region, province=r.province,
                         group="t:" + str(r.song_key), title=r.song_name, ethnic=str(r.ethnic_group or ""),
                         channel=f"g{r.group_id}", time_unit="sec", notes=notes, subset=r.transcription_model,  # channel = channel ∪ singer group
                         performance_type=r.performance_type, round=int(r.round), tier=r.provenance_tier))
    return recs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="anthology,essen,trans_primary,trans_game_pp,trans_rosvot")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for src in args.sources.split(","):
        if src == "anthology":
            recs = build_anthology()
        elif src == "essen":
            recs = build_essen()
        elif src == "trans_merged":
            recs = build_merged()
        else:
            recs = build_transcriptions(src.removeprefix("trans_"))
        with open(OUT / f"corpus_{src}.pkl", "wb") as f:
            pickle.dump(recs, f)
        counts = pd.Series([r["region"] for r in recs]).value_counts()
        print(f"{src}: {len(recs)} items, {counts.size} regions\n{counts.to_string()}\n", flush=True)


if __name__ == "__main__":
    main()
