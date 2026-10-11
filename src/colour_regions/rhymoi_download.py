"""
Round 3: download the eligible Musical Map of China items that are not yet in the corpus
(data/rhymoi/rhymoi_items.csv, eligible & not in_round1; src/colour_regions/rhymoi.py).

Output: data/regions_v3/audio/<region>/<id>.<ext>  and  data/regions_v3/manifest.csv in the round-2 manifest format,
so the transcription pipeline runs with AQ_MANIFEST=data/regions_v3/manifest.csv AQ_TRANS=data/regions_v3/transcription.
Pacing 45-90 s, no cookies (author decision 2026-10-04); stops after 3 consecutive bot-wall errors. Re-runnable.
Run (py312): python src/colour_regions/rhymoi_download.py [--limit N] [--manifest-only]
"""

import argparse
import random
import re
import time
from pathlib import Path

import pandas as pd
import yt_dlp

ROOT = Path(__file__).resolve().parents[2]
V3 = ROOT / "data" / "regions_v3"
OUT, MANIFEST = V3 / "audio", V3 / "manifest.csv"
NODE = Path.home() / "miniforge3" / "envs" / "node" / "bin" / "node"
AUDIO_EXTS = {".webm", ".m4a", ".opus", ".mp3", ".ogg", ".mp4", ".wav", ".flac", ".aac"}
CHANNEL = "Musical Map of China 中国音乐地图.瑞鸣音乐 Rhymoi Music"


def on_disk(region: str, vid: str) -> Path | None:
    return next((f for f in (OUT / region).glob(f"{vid}.*") if f.suffix in AUDIO_EXTS), None)


def song_name(title: str) -> str | None:
    """《阿依勒汗 . 红苹果》 → 阿依勒汗 (the Chinese title, before any transliterated subtitle); as song_table.py."""
    m = re.search(r"《\s*([^》]+?)\s*》", str(title))
    return re.split(r"\s*\.\s*", m.group(1))[0] if m else None


def manifest(items: pd.DataFrame, status: dict) -> pd.DataFrame:
    rows = []
    for r in items.itertuples():
        f = on_disk(r.region, r.item_id)
        rows.append(dict(
            region=r.region, rank=None, platform="yt", id=r.item_id, url=f"https://www.youtube.com/watch?v={r.item_id}",
            title=r.title, channel=CHANNEL, channel_id="UCN19zbpNCX9lrbKreffuSAQ", duration_s=r.duration_s,
            song_name=song_name(r.title), province=r.province, county_or_area=r.county_or_area, ethnic_group=r.ethnic_native,
            genre=r.genre_native, performance_type="原生态", singer=r.singers, singer_inheritor=None,
            provenance_tier="A" if r.tier == "A2" else "C",
            provenance_evidence=f"Musical Map of China description: 地区 {r.area}" + (
                " (county stated), named singer" if r.tier == "A2" else ""),
            dating_flag="check", note=f"rhymoi form={r.form}; region rule {r.region_rule}", curator="rhymoi.py",
            video_id=r.item_id, audio_path=str(f.relative_to(ROOT)) if f else None,
            status="ok" if f else status.get(r.item_id, "pending"), uploader=CHANNEL,
            uploader_id="UCN19zbpNCX9lrbKreffuSAQ", upload_date=r.upload_date, duration_s_actual=r.duration_s))
    m = pd.DataFrame(rows)
    m["rank"] = m.groupby("region").cumcount() + 1  # order within region, as in the round-1/2 manifests
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--manifest-only", action="store_true")
    a = ap.parse_args()
    it = pd.read_csv(ROOT / "data" / "rhymoi" / "rhymoi_items.csv")
    it = it[it.eligible & ~it.in_round1].reset_index(drop=True)
    V3.mkdir(parents=True, exist_ok=True)
    status = {}
    if MANIFEST.exists():
        old = pd.read_csv(MANIFEST)
        status = dict(zip(old.id, old.status))
    if not a.manifest_only:
        todo = it[[on_disk(r, i) is None and not str(status.get(i, "")).startswith("unavailable")
                   for r, i in zip(it.region, it.item_id)]]
        todo = todo.sample(frac=1, random_state=0)  # regions interleaved
        if a.limit:
            todo = todo.head(a.limit)
        print(f"{len(todo)} to download", flush=True)
        walls = 0
        for n, r in enumerate(todo.itertuples(), 1):
            (OUT / r.region).mkdir(parents=True, exist_ok=True)
            opts = {"format": "bestaudio/best", "outtmpl": str(OUT / r.region / "%(id)s.%(ext)s"), "quiet": True,
                    "no_warnings": True, "noprogress": True}
            if NODE.exists():
                opts["js_runtimes"] = {"node": {"path": str(NODE)}}
            try:
                with yt_dlp.YoutubeDL(opts) as y:
                    y.download([f"https://www.youtube.com/watch?v={r.item_id}"])
                status[r.item_id], walls = "ok", 0
            except Exception as e:
                msg = str(e)
                wall = "confirm you" in msg or "Sign in" in msg
                status[r.item_id] = "wall" if wall else ("unavailable" if "not available" in msg else "error: " + msg[:100])
                walls = walls + 1 if wall else 0
            print(f"[{n}/{len(todo)}] {r.region} {r.item_id} {status[r.item_id]}", flush=True)
            if n % 10 == 0:
                manifest(it, status).to_csv(MANIFEST, index=False)
            if walls >= 3:
                print("bot wall: stopping; rerun later to resume", flush=True)
                break
            if n < len(todo):
                time.sleep(random.uniform(45, 90))
    m = manifest(it, status)
    m.to_csv(MANIFEST, index=False)
    print(m.status.value_counts().to_string())


if __name__ == "__main__":
    main()
