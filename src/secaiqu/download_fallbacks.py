"""
Fallback downloader for curated candidates that download_curated.py could not fetch.

For each missing video it tries, in order, and stops at the first success:
  1. yt-dlp + Firefox cookies, player clients one at a time:
     default, mweb, ios, web_embedded, android_vr, tv_simply
  2. yt-dlp without cookies (default client)
  3. Invidious API proxy (several public instances): audio stream fetched through the instance (?local=true)
  4. Piped API (several public instances): audioStreams URL
  5. (--allow-replacement) search YouTube for another upload of the same song
     ("<song_name> <province/genre>") and download the first unused 60–720 s hit
     with method 1. The replacement is appended to data/regions_curated/<region>.json
     with `replaces: <original id>`, so the manifest picks it up.

Every attempt is appended to data/regions_audio/fallback_log.csv (video, method, ok, error).
Run: python src/secaiqu/download_fallbacks.py [--allow-replacement]   (py312 env)
"""

import argparse
import csv
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yt_dlp

ROOT = Path(__file__).resolve().parent.parent.parent
CURATED = ROOT / "data" / "regions_curated"
OUT = ROOT / "data" / "regions_audio"
LOG = OUT / "fallback_log.csv"
NODE = Path.home() / "miniforge3" / "envs" / "node" / "bin" / "node"
AUDIO_EXTS = {".webm", ".m4a", ".opus", ".mp3", ".ogg", ".mp4"}
CLIENTS = [None, "mweb", "ios", "web_embedded", "android_vr", "tv_simply"]
INVIDIOUS = ["https://inv.nadeko.net", "https://yewtu.be", "https://invidious.nerdvpn.de",
             "https://invidious.privacyredirect.com", "https://iv.melmac.space"]
PIPED = ["https://pipedapi.kavin.rocks", "https://pipedapi.adminforge.de", "https://api.piped.private.coffee"]
UA = {"User-Agent": "Mozilla/5.0 (research dataset curation; contact via repo)"}


def have(region: str, vid: str) -> bool:
    return any(p.suffix in AUDIO_EXTS for p in (OUT / region).glob(f"{vid}.*"))


def log(vid: str, region: str, method: str, ok: bool, err: str = "") -> None:
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "region", "video_id", "method", "ok", "error"])
        w.writerow([datetime.now(timezone.utc).isoformat(), region, vid, method, ok, err[:200]])


def ytdlp(url: str, region: str, client: str | None, cookies: bool) -> None:
    opts = {"format": "bestaudio/best", "noplaylist": True, "quiet": True, "no_warnings": True,
            "writeinfojson": True, "noprogress": True, "retries": 2,
            "outtmpl": str(OUT / region / "%(id)s.%(ext)s"),
            "js_runtimes": {"node": {"path": str(NODE)}} if NODE.exists() else {}}
    if cookies:
        opts["cookiesfrombrowser"] = ("firefox",)
    if client:
        opts["extractor_args"] = {"youtube": {"player_client": [client]}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)


def fetch_stream(url: str, dst: Path) -> None:
    with requests.get(url, headers=UA, stream=True, timeout=60) as r:
        r.raise_for_status()
        tmp = dst.with_suffix(dst.suffix + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    if tmp.stat().st_size < 50_000:
        tmp.unlink()
        raise RuntimeError("stream too small")
    tmp.rename(dst)


def invidious(vid: str, region: str) -> str:
    for base in INVIDIOUS:
        try:
            meta = requests.get(f"{base}/api/v1/videos/{vid}", headers=UA, timeout=20).json()
            audio = [f for f in meta.get("adaptiveFormats", []) if f.get("type", "").startswith("audio/")]
            if not audio:
                continue
            best = max(audio, key=lambda f: int(f.get("bitrate", 0)))
            ext = "m4a" if "mp4" in best["type"] else "webm"
            url = best["url"]
            if "/latest_version" not in url:  # proxy through the instance, not googlevideo directly
                url = f"{base}/latest_version?id={vid}&itag={best['itag']}&local=true"
            fetch_stream(url, OUT / region / f"{vid}.{ext}")
            (OUT / region / f"{vid}.info.json").write_text(json.dumps(
                {"id": vid, "title": meta.get("title"), "uploader": meta.get("author"),
                 "duration": meta.get("lengthSeconds"), "source": f"invidious:{base}"}, ensure_ascii=False))
            return base
        except Exception:
            continue
    raise RuntimeError("all invidious instances failed")


def piped(vid: str, region: str) -> str:
    for base in PIPED:
        try:
            meta = requests.get(f"{base}/streams/{vid}", headers=UA, timeout=20).json()
            audio = meta.get("audioStreams") or []
            if not audio:
                continue
            best = max(audio, key=lambda s: s.get("bitrate", 0))
            ext = "m4a" if "mp4" in best.get("mimeType", "") else "webm"
            fetch_stream(best["url"], OUT / region / f"{vid}.{ext}")
            (OUT / region / f"{vid}.info.json").write_text(json.dumps(
                {"id": vid, "title": meta.get("title"), "uploader": meta.get("uploader"),
                 "duration": meta.get("duration"), "source": f"piped:{base}"}, ensure_ascii=False))
            return base
        except Exception:
            continue
    raise RuntimeError("all piped instances failed")


def try_all(vid: str, region: str) -> str | None:
    url = f"https://www.youtube.com/watch?v={vid}"
    for client in CLIENTS:
        m = f"yt-dlp cookies client={client or 'default'}"
        try:
            ytdlp(url, region, client, cookies=True)
            if have(region, vid):
                log(vid, region, m, True)
                return m
        except Exception as e:
            log(vid, region, m, False, str(e).splitlines()[0])
        time.sleep(random.uniform(3, 8))
    for m, fn in [("yt-dlp no-cookies", lambda: ytdlp(url, region, None, cookies=False)),
                  ("invidious", lambda: invidious(vid, region)),
                  ("piped", lambda: piped(vid, region))]:
        try:
            detail = fn()
            if have(region, vid):
                log(vid, region, f"{m} {detail or ''}".strip(), True)
                return m
        except Exception as e:
            log(vid, region, m, False, str(e).splitlines()[0])
    return None


def replacement(cand: dict, region: str, used: set[str]) -> dict | None:
    query = f"{cand['song_name']} {cand.get('province_or_area') or cand.get('ethnic_group') or ''} 民歌".strip()
    with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True, "no_warnings": True}) as ydl:
        hits = ydl.extract_info(f"ytsearch10:{query}", download=False).get("entries", [])
    for h in hits:
        d = h.get("duration") or 0
        if not h.get("id") or h["id"] in used or not 60 <= d <= 720:
            continue
        try:
            ytdlp(f"https://www.youtube.com/watch?v={h['id']}", region, None, cookies=True)
        except Exception as e:
            log(h["id"], region, "replacement download", False, str(e).splitlines()[0])
            continue
        if have(region, h["id"]):
            log(h["id"], region, f"replacement for {cand['video_id']} (query: {query})", True)
            return {**cand, "video_id": h["id"], "url": f"https://www.youtube.com/watch?v={h['id']}",
                    "title": h.get("title"), "channel": h.get("channel") or h.get("uploader"),
                    "duration_s": d, "source_query": query, "replaces": cand["video_id"],
                    "already_downloaded": False,
                    "note": f"replacement for unreachable {cand['video_id']}; needs listening check"}
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-replacement", action="store_true")
    args = ap.parse_args()
    summary = {}
    for path in sorted(CURATED.glob("*.json")):
        data = json.loads(path.read_text())
        region = data["region"]
        used = {c["video_id"] for c in data["candidates"]}
        replaced = {c.get("replaces") for c in data["candidates"] if c.get("replaces")}
        added = []
        for c in data["candidates"]:
            vid = c["video_id"]
            if have(region, vid) or vid in replaced or c.get("replaces"):
                continue
            method = try_all(vid, region)
            print(f"{region} #{c['rank']} {vid}: {method or 'FAILED all methods'}", flush=True)
            if method:
                summary[method] = summary.get(method, 0) + 1
                continue
            if args.allow_replacement:
                rep = replacement(c, region, used)
                if rep:
                    used.add(rep["video_id"])
                    added.append(rep)
                    summary["replacement"] = summary.get("replacement", 0) + 1
                    print(f"   → replaced by {rep['video_id']} {rep['title'][:50]}", flush=True)
                    continue
            summary["unrecovered"] = summary.get("unrecovered", 0) + 1
        if added:
            data["candidates"] += added
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print("\nSummary:", summary)


if __name__ == "__main__":
    main()
