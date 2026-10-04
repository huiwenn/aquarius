"""
Search YouTube for candidate folk-song recordings (metadata only, no download).

Uses yt-dlp's flat `ytsearchN:` extractor, which returns real, currently-listed
video IDs. It works even while video extraction is bot-walled.

Every query and its results are appended to data/regions_curated/search_log.jsonl
so the curation is reproducible and auditable.

Usage:
  python src/secaiqu/search_candidates.py --region 西北部高原 -n 15 "陕北民歌 信天游 原生态" "山西民歌 左权开花调"
Prints one TSV line per hit: video_id, duration_s, channel, title
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parent.parent.parent
LOG = ROOT / "data" / "regions_curated" / "search_log.jsonl"


def search(query: str, n: int) -> list[dict]:
    opts = {"extract_flat": True, "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
    return [{
        "video_id": e.get("id"),
        "title": e.get("title"),
        "channel": e.get("channel") or e.get("uploader"),
        "duration_s": e.get("duration"),
        "view_count": e.get("view_count"),
        "url": f"https://www.youtube.com/watch?v={e.get('id')}",
    } for e in res.get("entries", []) if e.get("id")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--region", required=True)
    ap.add_argument("-n", type=int, default=15)
    args = ap.parse_args()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    for q in args.queries:
        hits = search(q, args.n)
        with LOG.open("a") as f:
            f.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "region": args.region,
                                "query": q, "hits": hits}, ensure_ascii=False) + "\n")
        print(f"# {q}")
        for h in hits:
            print(f"{h['video_id']}\t{h['duration_s']}\t{h['channel']}\t{h['title']}")
        time.sleep(2)


if __name__ == "__main__":
    main()
