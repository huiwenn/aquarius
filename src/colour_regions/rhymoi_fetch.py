"""
Fetch video metadata (title, description, duration, upload date; no audio) for the Musical Map of China channel
(中国音乐地图 / Rhymoi Music, YouTube UCN19zbpNCX9lrbKreffuSAQ), for the videos not yet in the corpus.

Input:  data/rhymoi/channel_titles.csv   (from the flat channel listing; columns id, title, song, instr, have)
Output: data/rhymoi/info/<id>.json       (trimmed yt-dlp info; one file per video; idempotent, resumable)
        data/rhymoi/fetch_log.csv        (id, time, status)

Order: song-like titles first, then unclassified titles; titles that are clearly instrumental or opera are skipped.
Pacing 45-90 s per request, no cookies. Stops after 3 consecutive bot-wall errors ("Sign in to confirm").
Run (py312): python src/colour_regions/rhymoi_fetch.py [--limit N] [--all]
"""

import argparse
import csv
import json
import random
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yt_dlp

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "rhymoi"
KEEP = ["id", "title", "description", "duration", "upload_date", "channel", "channel_id", "tags", "categories",
        "view_count", "availability"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true", help="also fetch titles classified as instrumental/opera")
    a = ap.parse_args()
    t = pd.read_csv(D / "channel_titles.csv")
    t = t[~t.have]
    if not a.all:
        t = t[~t.instr]
    t = t.assign(o=(~t.song).astype(int)).sort_values(["o"], kind="stable")
    (D / "info").mkdir(parents=True, exist_ok=True)
    gone = set()
    if (D / "fetch_log.csv").exists():
        lg = pd.read_csv(D / "fetch_log.csv", names=["id", "time", "status"])
        gone = set(lg[lg.status.str.contains("not available|unavailable|Private", na=False)].id)
    todo = [i for i in t.id if not (D / "info" / f"{i}.json").exists() and i not in gone]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(todo)} to fetch", flush=True)
    ydl = yt_dlp.YoutubeDL({"skip_download": True, "quiet": True, "no_warnings": True})
    log = open(D / "fetch_log.csv", "a", newline="")
    w = csv.writer(log)
    walls = 0
    for n, vid in enumerate(todo, 1):
        status = "ok"
        try:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False, process=False)
            (D / "info" / f"{vid}.json").write_text(json.dumps({k: info.get(k) for k in KEEP}, ensure_ascii=False))
            walls = 0
        except Exception as e:  # unavailable, private, or bot wall
            msg = str(e)
            status = "wall" if "confirm you" in msg or "Sign in" in msg else "error: " + msg[:120]
            walls = walls + 1 if status == "wall" else 0
        w.writerow([vid, datetime.now().isoformat(timespec="seconds"), status])
        log.flush()
        print(f"[{n}/{len(todo)}] {vid} {status}", flush=True)
        if walls >= 3:
            print("bot wall: stopping; rerun later to resume", flush=True)
            break
        if n < len(todo):
            time.sleep(random.uniform(45, 90))


if __name__ == "__main__":
    main()
