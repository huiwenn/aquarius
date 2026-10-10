"""
Round 3 (pending) downloader: metadata/pending/round3_candidates.csv
  -> data/round3/audio/<region_code>/<id>.<ext>  (+ <id>.info.json)
  -> data/round3/manifest.csv                     (rebuilt from disk)
  -> metadata/pending/round3_candidates.csv       (title, channel, duration... filled in)

Same settings as src/secaiqu/v2/download.py for YouTube: native best audio (no
transcoding), noplaylist, one process, U(45, 90) s between items, 1 h cooldown on
the bot wall. No browser cookies (the user's cookies need the user's OK).
Re-runnable: items already on disk are skipped; the manifest is rebuilt from disk.

Run: python src/secaiqu/round3/download_pending.py [--fill-only]
"""

import argparse
import csv
import json
import random
import shutil
import time
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parents[3]
PENDING = ROOT / "metadata" / "pending" / "round3_candidates.csv"
R3 = ROOT / "data" / "round3"
OUT, MANIFEST = R3 / "audio", R3 / "manifest.csv"
AUDIO_EXTS = {".webm", ".m4a", ".opus", ".mp3", ".ogg", ".mp4", ".wav", ".flac", ".aac"}
SLEEP = (45, 90)
BOT_WALL = "confirm you" + "'re not a bot"


def node_path():
    """The node JS runtime yt-dlp uses for YouTube. Prefer the project env."""
    for p in (Path.home() / "miniforge3" / "envs" / "node" / "bin" / "node",):
        if p.exists():
            return str(p)
    return shutil.which("node")


def audio_file(code, iid):
    for p in (OUT / code).glob(f"{iid}.*"):
        if p.suffix in AUDIO_EXTS:
            return p
    return None


def read_rows():
    with PENDING.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def download(rows):
    node = node_path()
    for n, r in enumerate(rows):
        code, iid = r["region_code"], r["item_id"]
        if audio_file(code, iid):
            continue
        (OUT / code).mkdir(parents=True, exist_ok=True)
        opts = {"format": "bestaudio/best", "noplaylist": True, "writeinfojson": True,
                "outtmpl": str(OUT / code / "%(id)s.%(ext)s"), "quiet": True,
                "no_warnings": True, "retries": 3}
        if node:
            opts["js_runtimes"] = {"node": {"path": node}}
        for attempt in range(2):
            try:
                with yt_dlp.YoutubeDL(opts) as y:
                    y.download([r["url"]])
                print(f"[{n + 1}/{len(rows)}] ok {code}/{iid}", flush=True)
                break
            except Exception as e:  # noqa: BLE001 — record and move on
                msg = str(e)
                print(f"[{n + 1}/{len(rows)}] FAIL {code}/{iid}: {msg[:200]}", flush=True)
                (OUT / code / f"{iid}.error.txt").write_text(msg)
                if BOT_WALL in msg and attempt == 0:
                    print("bot wall: cooling down 1 h", flush=True)
                    time.sleep(3600)
                    continue
                break
        time.sleep(random.uniform(*SLEEP))


def info(code, iid):
    p = OUT / code / f"{iid}.info.json"
    return json.loads(p.read_text()) if p.exists() else {}


def write_manifest(rows):
    R3.mkdir(parents=True, exist_ok=True)
    cols = ["item_id", "region_code", "status", "audio_path", "duration_s", "error"]
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            code, iid = r["region_code"], r["item_id"]
            a = audio_file(code, iid)
            err = OUT / code / f"{iid}.error.txt"
            w.writerow({"item_id": iid, "region_code": code,
                        "status": "ok" if a else "failed",
                        "audio_path": str(a.relative_to(ROOT)) if a else "",
                        "duration_s": info(code, iid).get("duration", ""),
                        "error": "" if a else (err.read_text()[:300] if err.exists() else "")})


def fill_pending(rows):
    """Copy what the platform says (title, channel, date, duration) into the
    tracked list, and record download and transcription status."""
    extra = ["title", "channel", "channel_key", "upload_date", "duration_s",
             "download_status", "transcription_status"]
    cols = list(rows[0].keys())
    cols += [c for c in extra if c not in cols]
    for r in rows:
        meta = info(r["region_code"], r["item_id"])
        if meta:
            r["title"] = meta.get("title", "")
            r["channel"] = meta.get("channel") or meta.get("uploader", "")
            cid = meta.get("channel_id") or ""
            r["channel_key"] = f"youtube:{cid}" if cid else ""
            r["upload_date"] = meta.get("upload_date", "")
            r["duration_s"] = meta.get("duration", "")
        r["download_status"] = "ok" if audio_file(r["region_code"], r["item_id"]) else "failed"
        r["transcription_status"] = "pending"
    with PENDING.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill-only", action="store_true", help="skip downloading")
    a = ap.parse_args()
    rows = read_rows()
    if not a.fill_only:
        download(rows)
    write_manifest(rows)
    fill_pending(rows)
    ok = sum(1 for r in rows if r["download_status"] == "ok")
    print(f"done: {ok}/{len(rows)} downloaded; manifest {MANIFEST.relative_to(ROOT)}", flush=True)
