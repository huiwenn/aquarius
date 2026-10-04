import json
from collections import Counter
from pathlib import Path
ROOT = Path("/Users/sophiasun/Desktop/2cool4school/2026/aquarius")
LOG = ROOT/"data/regions_curated/search_log.jsonl"
meta, srcq = {}, {}
for line in LOG.open():
    r = json.loads(line)
    for h in r["hits"]:
        vid = h["video_id"]
        meta.setdefault(vid, h)
        srcq.setdefault((r["region"], vid), r["query"])
        srcq.setdefault(("*", vid), r["query"])

def build(region, rows):
    audio = ROOT/"data/regions_audio"/region
    out, seen = [], set()
    for i, row in enumerate(rows, 1):
        vid, song, eth, area, genre, ptype, note = row
        assert vid not in seen, vid; seen.add(vid)
        info = audio/f"{vid}.info.json"
        dl = info.exists() and any(p.suffix != ".json" for p in audio.glob(f"{vid}.*"))
        if dl:
            d = json.load(info.open())
            title, ch, dur = d.get("title"), d.get("uploader") or d.get("channel"), d.get("duration")
            q = srcq.get((region, vid)) or "(already downloaded from original region youtube_links / playlist pull)"
        else:
            assert vid in meta, f"{region}: {vid} not in search log"
            h = meta[vid]; title, ch, dur = h["title"], h["channel"], h["duration_s"]
            q = srcq.get((region, vid)) or srcq[("*", vid)]
        assert dur is None or 60 <= dur <= 720, (vid, dur)
        out.append({"rank": i, "video_id": vid, "url": f"https://www.youtube.com/watch?v={vid}",
                    "title": title, "channel": ch, "duration_s": int(dur) if dur else None,
                    "song_name": song, "ethnic_group": eth, "province_or_area": area, "genre": genre,
                    "performance_type": ptype, "already_downloaded": dl, "source_query": q, "note": note})
    cnt = Counter(c["song_name"] for c in out)
    assert max(cnt.values()) <= 3, cnt.most_common(3)
    json.dump({"region": region, "curated_on": "2026-09-28", "candidates": out},
              open(ROOT/"data/regions_curated"/f"{region}.json", "w"), ensure_ascii=False, indent=2)
    print(region, len(out), "distinct songs", len(cnt), "downloaded", sum(c["already_downloaded"] for c in out))
