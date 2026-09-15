"""
Aquarius Phase 4: Unify all datasets into a single master table.

Reads raw data from data/raw/<dataset>/, maps fields to the unified schema
(docs/unified_schema.md), and outputs data/unified/master_table.parquet + CSV sample.
"""

import os
import json
import glob
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "unified"

SCHEMA_COLS = [
    "unified_id", "dataset", "original_id", "granularity",
    "title", "title_en", "subtitle", "artist", "composer", "arranger",
    "album", "singer_id", "voice_type", "role_type",
    "period", "dynasty", "year", "score_source",
    "province", "region", "country", "ethnic_group", "location",
    "genre", "sub_genre", "folk_song_type", "shengqiang", "theme",
    "arrangement_role",
    "instrument", "instrument_code", "instrument_pinyin",
    "bayin_family", "ensemble_type",
    "key", "key_transpose", "mode", "tempo_bpm", "time_signature",
    "tuning", "pitch_range_low", "pitch_range_high", "duration_seconds",
    "language", "lyrics_text", "lyrics_format", "phonemes",
    "has_audio", "has_midi", "has_musicxml", "has_jianpu",
    "has_lyrics", "has_score", "has_metadata_only",
    "audio_format", "sample_rate", "channels",
    "chord_labels", "beat_annotations",
    "emotion_valence", "emotion_arousal",
    "playing_technique", "singing_technique",
    "source_dataset", "source_url", "license", "access_status",
]


def make_id(dataset: str, original_id) -> str:
    return f"{dataset}__{original_id}"


def empty_row(dataset: str) -> dict:
    row = {c: None for c in SCHEMA_COLS}
    row["dataset"] = dataset
    row["source_dataset"] = dataset
    return row


# ── POP909 ──────────────────────────────────────────────────────────────────

def load_pop909() -> list[dict]:
    path = RAW / "pop909"
    idx = path / "POP909" / "index.xlsx"
    if not idx.exists():
        idx = path / "index.xlsx"
    if not idx.exists():
        return []
    df = pd.read_excel(idx)
    rows = []
    for _, r in df.iterrows():
        row = empty_row("pop909")
        sid = str(r["song_id"]).zfill(3)
        row["original_id"] = sid
        row["unified_id"] = make_id("pop909", sid)
        row["granularity"] = "song"
        row["title"] = str(r["name"])
        row["artist"] = str(r["artist"])
        ts = r.get("num_beats_per_measure", "")
        row["time_signature"] = f"{ts}/4" if ts else None
        row["has_audio"] = False
        row["has_midi"] = True
        row["has_musicxml"] = False
        row["chord_labels"] = True
        row["beat_annotations"] = True
        row["language"] = "Mandarin"
        row["genre"] = "C-pop"
        row["country"] = "China"
        row["source_url"] = "https://github.com/music-x-lab/POP909-Dataset"
        row["license"] = "MIT"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── ChMusic ─────────────────────────────────────────────────────────────────

CHMUSIC_INSTRUMENTS = {
    "1": ("Erhu", "二胡", "silk"),
    "2": ("Pipa", "琵琶", "silk"),
    "3": ("Sanxian", "三弦", "silk"),
    "4": ("Dizi", "笛子", "bamboo"),
    "5": ("Suona", "唢呐", "metal"),
    "6": ("Zhuiqin", "坠琴", "silk"),
    "7": ("Zhongruan", "中阮", "silk"),
    "8": ("Liuqin", "柳琴", "silk"),
    "9": ("Guzheng", "古筝", "silk"),
    "10": ("Yangqin", "扬琴", "silk"),
    "11": ("Sheng", "笙", "gourd"),
}

def load_chmusic() -> list[dict]:
    path = RAW / "chmusic" / "ChMusic" / "Musics"
    if not path.exists():
        return []
    rows = []
    for wav in sorted(path.glob("*.wav")):
        parts = wav.stem.split(".")
        inst_num = parts[0]
        track_num = parts[1] if len(parts) > 1 else "1"
        info = CHMUSIC_INSTRUMENTS.get(inst_num, (inst_num, "", ""))
        row = empty_row("chmusic")
        row["original_id"] = wav.stem
        row["unified_id"] = make_id("chmusic", wav.stem)
        row["granularity"] = "song"
        row["instrument"] = info[0]
        row["instrument_pinyin"] = info[1]
        row["bayin_family"] = info[2]
        row["has_audio"] = True
        row["audio_format"] = "WAV"
        row["sample_rate"] = 44100
        row["channels"] = 2
        row["genre"] = "traditional instrumental"
        row["country"] = "China"
        row["source_url"] = "https://github.com/YuanAllen/ChMusic"
        row["license"] = "unspecified"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── Guqin ───────────────────────────────────────────────────────────────────

def load_guqin() -> list[dict]:
    csv_path = RAW / "guqin_dataset" / "Guqin_Dataset_v1" / "reference.csv"
    if not csv_path.exists():
        return []
    df = pd.read_csv(csv_path)
    rows = []
    for _, r in df.iterrows():
        row = empty_row("guqin_dataset")
        title = str(r.get("曲谱名称", ""))
        row["original_id"] = title
        row["unified_id"] = make_id("guqin_dataset", title)
        row["granularity"] = "song"
        row["title"] = title
        row["artist"] = str(r.get("演奏者", "")) if pd.notna(r.get("演奏者")) else None
        row["arranger"] = str(r.get("打谱/记谱者", "")) if pd.notna(r.get("打谱/记谱者")) else None
        row["score_source"] = str(r.get("琴谱来源", "")) if pd.notna(r.get("琴谱来源")) else None
        row["dynasty"] = str(r.get("琴曲来源", "")) if pd.notna(r.get("琴曲来源")) else None
        row["tuning"] = str(r.get("定弦", "")) if pd.notna(r.get("定弦")) else None
        row["instrument"] = "Guqin"
        row["bayin_family"] = "silk"
        row["has_musicxml"] = True
        row["has_midi"] = False
        row["has_audio"] = False
        row["genre"] = "guqin solo"
        row["country"] = "China"
        row["source_url"] = "https://github.com/lukewys/Guqin-Dataset"
        row["license"] = "unspecified"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── Anthology of Chinese Folk Songs ─────────────────────────────────────────

ANTHOLOGY_VOLUMES = {
    "guangdong": "Guangdong", "jiangsu1": "Jiangsu",
    "jiangsu2": "Jiangsu", "hainan": "Hainan",
    "hebei1": "Hebei", "hebei2": "Hebei",
    "henan": "Henan", "jilin": "Jilin",
    "shanghai": "Shanghai", "sichuan1": "Sichuan",
    "tianjin": "Tianjin",
}

def load_anthology() -> list[dict]:
    base = RAW / "anthology_chinese_folk_songs"
    if not base.exists():
        return []
    rows = []
    for subset in ["lyrics-included", "melody-only"]:
        subset_path = base / subset
        if not subset_path.exists():
            continue
        for vol_dir in sorted(subset_path.iterdir()):
            if not vol_dir.is_dir():
                continue
            vol_name = vol_dir.name
            province = None
            for key, prov in ANTHOLOGY_VOLUMES.items():
                if key in vol_name.lower().replace(" ", "").replace("-", ""):
                    province = prov
                    break
            for mid in sorted(vol_dir.glob("*.mid")):
                parts = mid.stem.split("_", 1)
                song_num = parts[0]
                title = parts[1] if len(parts) > 1 else ""
                row = empty_row("anthology_chinese_folk_songs")
                oid = f"{vol_name}/{song_num}"
                row["original_id"] = oid
                row["unified_id"] = make_id("anthology", oid)
                row["granularity"] = "song"
                row["title"] = title
                row["province"] = province
                row["has_midi"] = True
                row["has_musicxml"] = True
                row["has_lyrics"] = subset == "lyrics-included"
                row["has_audio"] = False
                row["genre"] = "folk song"
                row["folk_song_type"] = None
                row["language"] = "Chinese"
                row["country"] = "China"
                row["source_url"] = "https://github.com/m-july/Anthology-of-Chinese-Folk-Songs-v251103"
                row["license"] = "unspecified"
                row["access_status"] = "open"
                rows.append(row)
    return rows


# ── PMEmo ───────────────────────────────────────────────────────────────────

def load_pmemo() -> list[dict]:
    meta = RAW / "pmemo" / "dataset" / "PMEmo" / "PMEmo2019" / "metadata.csv"
    if not meta.exists():
        return []
    df = pd.read_csv(meta)
    static_path = RAW / "pmemo" / "dataset" / "PMEmo" / "PMEmo2019" / "annotations" / "static_annotations.csv"
    static = {}
    if static_path.exists():
        sdf = pd.read_csv(static_path)
        for _, r in sdf.iterrows():
            mid = r.get("musicId")
            if pd.notna(mid):
                static[int(mid)] = {
                    "valence": r.get("Valence(mean)"),
                    "arousal": r.get("Arousal(mean)")
                }
    rows = []
    for _, r in df.iterrows():
        row = empty_row("pmemo")
        mid = str(int(r["musicId"]))
        row["original_id"] = mid
        row["unified_id"] = make_id("pmemo", mid)
        row["granularity"] = "song"
        row["title"] = str(r.get("title", ""))
        row["artist"] = str(r.get("artist", ""))
        row["album"] = str(r.get("album", "")) if pd.notna(r.get("album")) else None
        row["duration_seconds"] = float(r.get("duration", 0)) if pd.notna(r.get("duration")) else None
        row["has_audio"] = True
        row["audio_format"] = "MP3"
        row["genre"] = "pop"
        if int(mid) in static:
            row["emotion_valence"] = static[int(mid)]["valence"]
            row["emotion_arousal"] = static[int(mid)]["arousal"]
        row["language"] = "English"
        row["country"] = "International"
        row["source_url"] = "https://github.com/HuiZhangDB/PMEmo"
        row["license"] = "research"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── M4Singer ────────────────────────────────────────────────────────────────

def load_m4singer() -> list[dict]:
    meta = RAW / "m4singer" / "m4singer" / "meta.json"
    if not meta.exists():
        return []
    with open(meta) as f:
        data = json.load(f)
    seen_songs = {}
    for item in data:
        name = item.get("item_name", "")
        parts = name.split("#")
        if len(parts) >= 2:
            singer = parts[0]
            rest = "#".join(parts[1:])
            song_parts = rest.rsplit("#", 1)
            song_title = song_parts[0]
            song_key = f"{singer}#{song_title}"
            if song_key not in seen_songs:
                vtype = None
                for vt in ["Soprano", "Alto", "Tenor", "Bass"]:
                    if singer.startswith(vt):
                        vtype = vt
                        break
                seen_songs[song_key] = {
                    "singer": singer,
                    "title": song_title,
                    "voice_type": vtype,
                    "segment_count": 0,
                    "has_lyrics": False,
                }
            seen_songs[song_key]["segment_count"] += 1
            if item.get("txt"):
                seen_songs[song_key]["has_lyrics"] = True

    rows = []
    for song_key, info in seen_songs.items():
        row = empty_row("m4singer")
        row["original_id"] = song_key
        row["unified_id"] = make_id("m4singer", song_key)
        row["granularity"] = "song"
        row["title"] = info["title"]
        row["singer_id"] = info["singer"]
        row["voice_type"] = info["voice_type"]
        row["has_audio"] = True
        row["has_midi"] = True
        row["has_lyrics"] = info["has_lyrics"]
        row["audio_format"] = "WAV"
        row["genre"] = "C-pop"
        row["language"] = "Mandarin"
        row["country"] = "China"
        row["source_url"] = "https://github.com/M4Singer/M4Singer"
        row["license"] = "research"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── MGD ─────────────────────────────────────────────────────────────────────

PROVINCE_MAP = {
    "京": "Beijing", "津": "Tianjin", "冀": "Hebei", "晋": "Shanxi",
    "蒙": "Inner Mongolia", "辽": "Liaoning", "吉": "Jilin", "黑": "Heilongjiang",
    "沪": "Shanghai", "苏": "Jiangsu", "浙": "Zhejiang", "皖": "Anhui",
    "闽": "Fujian", "赣": "Jiangxi", "鲁": "Shandong", "豫": "Henan",
    "鄂": "Hubei", "湘": "Hunan", "粤": "Guangdong", "桂": "Guangxi",
    "琼": "Hainan", "川渝": "Sichuan/Chongqing", "贵": "Guizhou",
    "云": "Yunnan", "陕": "Shaanxi", "陕北": "Northern Shaanxi",
    "甘": "Gansu", "青": "Qinghai", "宁": "Ningxia", "新": "Xinjiang",
    "台": "Taiwan",
}

def load_mgd() -> list[dict]:
    path = RAW / "mgd"
    if not path.exists():
        return []
    rows = []
    for xlsx in sorted(path.glob("*.xlsx")):
        prov_abbr = xlsx.stem.replace("分省信息-", "")
        province = PROVINCE_MAP.get(prov_abbr, prov_abbr)
        try:
            df = pd.read_excel(xlsx)
        except Exception:
            continue
        for _, r in df.iterrows():
            row = empty_row("mgd")
            num = str(r.get("No.", ""))
            row["original_id"] = f"{prov_abbr}_{num}"
            row["unified_id"] = make_id("mgd", f"{prov_abbr}_{num}")
            row["granularity"] = "song"
            row["title"] = str(r.get("Title", "")) if pd.notna(r.get("Title")) else None
            row["subtitle"] = str(r.get("Sub-Title", "")) if pd.notna(r.get("Sub-Title")) else None
            row["province"] = province
            row["location"] = str(r.get("Location", "")) if pd.notna(r.get("Location")) else None
            row["genre"] = "folk song"
            row["folk_song_type"] = str(r.get("Genre", "")) if pd.notna(r.get("Genre")) else None
            row["key"] = str(r.get("Keys", "")) if pd.notna(r.get("Keys")) else None
            row["key_transpose"] = str(r.get("Key_Transpose_Postion", "")) if pd.notna(r.get("Key_Transpose_Postion")) else None
            row["time_signature"] = str(r.get("Regular_TS", "")) if pd.notna(r.get("Regular_TS")) else None
            row["has_metadata_only"] = True
            row["has_audio"] = False
            row["has_midi"] = False
            row["language"] = "Chinese"
            row["country"] = "China"
            row["source_url"] = "https://chinglohsiu.github.io/files/MGD.html"
            row["license"] = "unspecified"
            row["access_status"] = "open"
            rows.append(row)
    return rows


# ── CTIS ────────────────────────────────────────────────────────────────────

def load_ctis() -> list[dict]:
    path = RAW / "ctis" / "default" / "train"
    info_path = path / "dataset_info.json"
    if not info_path.exists():
        return []
    with open(info_path) as f:
        info = json.load(f)
    label_names = info.get("features", {}).get("label", {}).get("names", [])
    rows = []
    for i, label in enumerate(label_names):
        row = empty_row("ctis")
        row["original_id"] = label
        row["unified_id"] = make_id("ctis", label)
        row["granularity"] = "clip"
        row["instrument_code"] = label
        row["has_audio"] = True
        row["audio_format"] = "WAV"
        row["sample_rate"] = 44100
        row["genre"] = "traditional instrumental"
        row["country"] = "China"
        row["source_url"] = "https://huggingface.co/datasets/ccmusic-database/CTIS"
        row["license"] = "research"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── GZ_IsoTech ──────────────────────────────────────────────────────────────

def load_gz_isotech() -> list[dict]:
    info_path = RAW / "gz_isotech" / "default" / "train" / "dataset_info.json"
    if not info_path.exists():
        return []
    with open(info_path) as f:
        info = json.load(f)
    label_names = info.get("features", {}).get("label", {}).get("names", [])
    rows = []
    for label in label_names:
        row = empty_row("gz_isotech")
        row["original_id"] = label
        row["unified_id"] = make_id("gz_isotech", label)
        row["granularity"] = "clip"
        row["instrument"] = "Guzheng"
        row["bayin_family"] = "silk"
        row["playing_technique"] = label
        row["has_audio"] = True
        row["audio_format"] = "WAV"
        row["sample_rate"] = 44100
        row["genre"] = "traditional instrumental"
        row["country"] = "China"
        row["source_url"] = "https://huggingface.co/datasets/ccmusic-database/GZ_IsoTech"
        row["license"] = "research"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── Kaggle Folk Music ───────────────────────────────────────────────────────

def load_kaggle_folk() -> list[dict]:
    csv_path = RAW / "traditional_chinese_folk_music_kaggle" / "traditional_music_dataset.csv"
    if not csv_path.exists():
        return []
    df = pd.read_csv(csv_path)
    rows = []
    for _, r in df.iterrows():
        row = empty_row("traditional_chinese_folk_music_kaggle")
        row["original_id"] = str(r.get("file_name", ""))
        row["unified_id"] = make_id("kaggle_folk", row["original_id"])
        row["granularity"] = "song"
        row["province"] = str(r.get("region", ""))
        row["instrument"] = str(r.get("instrument", ""))
        row["genre"] = "folk"
        row["sub_genre"] = str(r.get("style_label", ""))
        row["theme"] = str(r.get("theme_label", ""))
        row["key"] = str(r.get("pitch_key", ""))
        row["tempo_bpm"] = float(r.get("tempo_bpm", 0)) if pd.notna(r.get("tempo_bpm")) else None
        row["has_metadata_only"] = True
        row["has_audio"] = False
        row["country"] = "China"
        row["source_url"] = "https://www.kaggle.com/datasets/ziya07/traditional-chinese-folk-music-composition-dataset"
        row["license"] = "CC0"
        row["access_status"] = "open"
        rows.append(row)
    return rows


# ── Jingju Singing Audio ───────────────────────────────────────────────────

def load_jingju_singing_audio() -> list[dict]:
    path = RAW / "jingju_singing_audio"
    rows = []
    for csv_name in ["catalogue_dan.csv", "catalogue_laosheng.csv"]:
        csv_path = path / csv_name
        if not csv_path.exists():
            continue
        role = csv_name.replace("catalogue_", "").replace(".csv", "")
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            try:
                df = pd.read_csv(csv_path, encoding="gbk")
            except Exception:
                continue
        for _, r in df.iterrows():
            row = empty_row("jingju_singing_audio")
            row["original_id"] = str(r.iloc[0]) if len(r) > 0 else ""
            row["unified_id"] = make_id("jingju_singing", row["original_id"])
            row["granularity"] = "song"
            row["role_type"] = role
            row["genre"] = "jingju"
            row["has_audio"] = True
            row["audio_format"] = "WAV"
            row["language"] = "Mandarin"
            row["country"] = "China"
            row["source_url"] = "https://zenodo.org/record/1245941"
            row["license"] = "CC"
            row["access_status"] = "open"
            rows.append(row)
    return rows


# ── Main ────────────────────────────────────────────────────────────────────

LOADERS = [
    ("pop909", load_pop909),
    ("chmusic", load_chmusic),
    ("guqin_dataset", load_guqin),
    ("anthology", load_anthology),
    ("pmemo", load_pmemo),
    ("m4singer", load_m4singer),
    ("mgd", load_mgd),
    ("ctis", load_ctis),
    ("gz_isotech", load_gz_isotech),
    ("kaggle_folk", load_kaggle_folk),
    ("jingju_singing_audio", load_jingju_singing_audio),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    all_rows = []
    for name, loader in LOADERS:
        print(f"Loading {name}...", end=" ")
        rows = loader()
        print(f"{len(rows)} items")
        all_rows.extend(rows)

    print(f"\nTotal items: {len(all_rows)}")

    df = pd.DataFrame(all_rows)
    for col in SCHEMA_COLS:
        if col not in df.columns:
            df[col] = None

    df = df[SCHEMA_COLS + [c for c in df.columns if c not in SCHEMA_COLS]]

    parquet_path = OUT / "master_table.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"Saved {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB)")

    sample = df.head(100)
    csv_path = OUT / "master_table_sample.csv"
    sample.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")

    print("\n── Coverage Summary ──")
    print(f"Datasets: {df['dataset'].nunique()}")
    print(f"Total items: {len(df)}")
    print(f"\nPer-dataset counts:")
    print(df["dataset"].value_counts().to_string())
    print(f"\nGranularity distribution:")
    print(df["granularity"].value_counts().to_string())
    print(f"\nModality coverage:")
    for mod in ["has_audio", "has_midi", "has_musicxml", "has_lyrics", "has_metadata_only"]:
        count = df[mod].sum() if mod in df.columns else 0
        pct = count / len(df) * 100 if len(df) > 0 else 0
        print(f"  {mod}: {int(count)} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
