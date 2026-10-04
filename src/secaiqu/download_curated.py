"""
Download audio for the curated candidate lists in data/regions_curated/<region>.json.

Second-pass downloader, written after download_audio.py hit YouTube's bot wall
(see docs/transcription.md §1). Differences from the first pass:
  - single-video URLs only (curated, verified to appear in YouTube search)
  - authenticated with browser cookies (--cookies-from-browser, default firefox)
  - 1 request at a time with randomized sleeps, regions visited round-robin so an
    interruption leaves every region partially filled rather than a few full ones
  - a JS runtime (node, for yt-dlp-ejs challenge solving) and the bgutil PO-token
    HTTP provider (third_party/bgutil-ytdlp-pot-provider, `node build/main.js`) if it's running
  - when the bot wall appears (it did after ~85 downloads even with cookies), wait
    --cooldown seconds and resume, up to --max-cooldowns times

Audio: native best stream, no transcoding → data/regions_audio/<region>/<id>.<ext>
Manifest: data/regions_audio/manifest.csv (curation metadata + download metadata/status)

Run: conda activate py312 && python src/secaiqu/download_curated.py [--browser firefox]
"""

import argparse
import json
import random
import time
from pathlib import Path

import pandas as pd
import yt_dlp

ROOT = Path(__file__).resolve().parent.parent.parent
CURATED = ROOT / "data" / "regions_curated"
OUT = ROOT / "data" / "regions_audio"
MANIFEST = OUT / "manifest.csv"
NODE = Path.home() / "miniforge3" / "envs" / "node" / "bin" / "node"
AUDIO_EXTS = {".webm", ".m4a", ".opus", ".mp3", ".ogg", ".mp4", ".wav", ".flac"}


def audio_file(region: str, vid: str) -> Path | None:
    for p in (OUT / region).glob(f"{vid}.*"):
        if p.suffix in AUDIO_EXTS:
            return p
    return None


def load_candidates() -> list[dict]:
    per_region = []
    for path in sorted(CURATED.glob("*.json")):
        data = json.loads(path.read_text())
        per_region.append([{**c, "region": data["region"]}
                           for c in sorted(data["candidates"], key=lambda c: c["rank"])])
    # round-robin across regions by rank
    ordered = []
    for i in range(max(map(len, per_region))):
        ordered += [cands[i] for cands in per_region if i < len(cands)]
    return ordered


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", default="firefox")
    ap.add_argument("--min-sleep", type=float, default=10)
    ap.add_argument("--max-sleep", type=float, default=25)
    ap.add_argument("--cooldown", type=float, default=2400)
    ap.add_argument("--max-cooldowns", type=int, default=15)
    ap.add_argument("--manifest-only", action="store_true", help="just rebuild manifest.csv from disk")
    ap.add_argument("--player-client", default=None,
                    help="yt-dlp YouTube player client(s), e.g. 'tv,web_safari' — for retrying HTTP 403 failures")
    args = ap.parse_args()

    prev = pd.read_csv(MANIFEST) if MANIFEST.exists() else pd.DataFrame()
    prev_rows = {(r.region, r.video_id): r._asdict() for r in prev.itertuples(index=False)} if len(prev) else {}

    cands = load_candidates()
    todo = [] if args.manifest_only else [c for c in cands if not audio_file(c["region"], c["video_id"])]
    print(f"{len(cands)} candidates, {len(cands) - len(todo)} already on disk, {len(todo)} to fetch")

    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "writeinfojson": True,
        "noprogress": True,
        "cookiesfrombrowser": (args.browser,),
        "js_runtimes": {"node": {"path": str(NODE)}} if NODE.exists() else {},
    }
    if args.player_client:
        opts["extractor_args"] = {"youtube": {"player_client": args.player_client.split(",")}}
    status: dict[tuple, dict] = {}
    cooldowns = 0
    n = 0
    while n < len(todo):
        c = todo[n]
        region_dir = OUT / c["region"]
        region_dir.mkdir(parents=True, exist_ok=True)
        try:
            with yt_dlp.YoutubeDL({**opts, "outtmpl": str(region_dir / "%(id)s.%(ext)s")}) as ydl:
                ydl.extract_info(c["url"], download=True)
            status[(c["region"], c["video_id"])] = {"status": "ok", "error": None}
            print(f"[{n + 1}/{len(todo)}] ok     {c['region']} #{c['rank']} {c['title'][:50]}", flush=True)
        except Exception as e:
            msg = str(e).splitlines()[0][:300]
            if "not a bot" in msg or "Sign in" in msg:
                cooldowns += 1
                if cooldowns > args.max_cooldowns:
                    print("Bot wall persists — giving up for now. Rerun later; completed files are kept.")
                    break
                print(f"Bot wall at item {n + 1} — cooling down {args.cooldown:.0f}s "
                      f"({cooldowns}/{args.max_cooldowns}) at {time.strftime('%H:%M')}", flush=True)
                time.sleep(args.cooldown)
                continue  # retry same item
            status[(c["region"], c["video_id"])] = {"status": "failed", "error": msg}
            print(f"[{n + 1}/{len(todo)}] FAILED {c['region']} #{c['rank']} {c['video_id']} {msg}", flush=True)
        n += 1
        time.sleep(random.uniform(args.min_sleep, args.max_sleep))

    # manifest over ALL curated candidates, reflecting what is on disk now
    rows = []
    for c in cands:
        key = (c["region"], c["video_id"])
        f = audio_file(*key)
        info_path = OUT / c["region"] / f"{c['video_id']}.info.json"
        info = json.loads(info_path.read_text()) if (f and info_path.exists()) else {}
        st = status.get(key) or {"status": "ok" if f else prev_rows.get(key, {}).get("status", "pending"),
                                 "error": None if f else prev_rows.get(key, {}).get("error")}
        rows.append({
            **{k: v for k, v in c.items() if k not in ("already_downloaded",)},
            "audio_path": str(f.relative_to(ROOT)) if f else None,
            "status": "ok" if f else st["status"],
            "error": st["error"],
            "yt_title": info.get("title"),
            "uploader": info.get("uploader"),
            "channel_id": info.get("channel_id"),
            "upload_date": info.get("upload_date"),
            "duration_s_actual": info.get("duration"),
            "license": info.get("license"),
            "acodec": info.get("acodec"),
        })
    df = pd.DataFrame(rows)
    df.to_csv(MANIFEST, index=False)
    print("\nPer-region audio on disk:")
    print(df.groupby("region")["status"].value_counts().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
