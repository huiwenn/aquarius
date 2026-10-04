"""
Collection v2 search tool: YouTube (yt-dlp flat ytsearch) and Bilibili (web search API), metadata only.

Every query and its hits are appended to data/regions_v2/logs/search_<platform>.jsonl (reproducible, auditable).
Each hit is annotated against v1 so curators can enforce the v2 rules (docs/collection_v2.md):
  v1_channel  channel already used in v1 (data/regions_transcription/dataset_index.csv) → not allowed in the held-out set
  v1_video    exact recording already in v1 → skip

Usage (py312):
  python src/secaiqu/v2/search.py --region 湘 --platform bili -n 20 "湘西 苗族 山歌 原生态" "桑植民歌 老艺人"
  python src/secaiqu/v2/search.py --region 湘 --platform yt   -n 15 "桑植民歌 原生态"
Output TSV: platform, id, duration_s, channel, plays, flags, title
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
LOGS = ROOT / "data" / "regions_v2" / "logs"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")


def v1_sets():
    d = pd.read_csv(ROOT / "data" / "regions_transcription" / "dataset_index.csv")
    return set(d.channel.astype(str)), set(d.video_id.astype(str))


def dur_s(x):
    if isinstance(x, (int, float)):
        return int(x)
    parts = [int(p) for p in str(x).split(":") if p.isdigit()]
    s = 0
    for p in parts:
        s = s * 60 + p
    return s


_opener = None


def bili_opener():
    global _opener
    if _opener is None:
        _opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        _opener.addheaders = [("User-Agent", UA), ("Referer", "https://search.bilibili.com/")]
        _opener.open("https://www.bilibili.com/", timeout=30).read()  # sets buvid3 cookies
    return _opener


def search_bili(q: str, n: int) -> list[dict]:
    out, page = [], 1
    while len(out) < n and page <= 3:
        url = "https://api.bilibili.com/x/web-interface/search/type?" + urllib.parse.urlencode(
            {"search_type": "video", "keyword": q, "page": page})
        d = json.loads(bili_opener().open(url, timeout=30).read())
        if d.get("code") != 0:
            raise RuntimeError(f"bilibili search error {d.get('code')}: {d.get('message')}")
        res = (d.get("data") or {}).get("result") or []
        if not res:
            break
        for r in res:
            out.append({"id": r["bvid"], "url": f"https://www.bilibili.com/video/{r['bvid']}",
                        "title": re.sub(r"<[^>]+>", "", r["title"]), "channel": r.get("author"),
                        "channel_id": r.get("mid"), "duration_s": dur_s(r.get("duration")),
                        "plays": r.get("play"), "description": (r.get("description") or "")[:300],
                        "pubdate": r.get("pubdate")})
        page += 1
        time.sleep(1.5)
    return out[:n]


def search_yt(q: str, n: int) -> list[dict]:
    import yt_dlp
    with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True, "no_warnings": True}) as ydl:
        res = ydl.extract_info(f"ytsearch{n}:{q}", download=False)
    return [{"id": e["id"], "url": f"https://www.youtube.com/watch?v={e['id']}", "title": e.get("title"),
             "channel": e.get("channel") or e.get("uploader"), "channel_id": e.get("channel_id"),
             "duration_s": e.get("duration"), "plays": e.get("view_count")}
            for e in res.get("entries", []) if e.get("id")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--region", required=True)
    ap.add_argument("--platform", choices=["bili", "yt"], default="bili")
    ap.add_argument("-n", type=int, default=20)
    a = ap.parse_args()
    v1_ch, v1_vid = v1_sets()
    LOGS.mkdir(parents=True, exist_ok=True)
    fn = search_bili if a.platform == "bili" else search_yt
    for q in a.queries:
        try:
            hits = fn(q, a.n)
        except Exception as e:  # noqa: BLE001
            print(f"# {q}\tERROR {e}")
            continue
        for h in hits:
            h["v1_channel"] = str(h["channel"]) in v1_ch
            h["v1_video"] = h["id"] in v1_vid
        with (LOGS / f"search_{a.platform}.jsonl").open("a") as f:
            f.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "region": a.region,
                                "query": q, "hits": hits}, ensure_ascii=False) + "\n")
        print(f"# {q}")
        for h in hits:
            flags = ",".join(k for k in ("v1_channel", "v1_video") if h[k]) or "-"
            print(f"{a.platform}\t{h['id']}\t{h['duration_s']}\t{h['channel']}\t{h['plays']}\t{flags}\t{h['title']}")
        time.sleep(2)


if __name__ == "__main__":
    main()
