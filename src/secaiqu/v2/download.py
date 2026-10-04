"""
Collection v2 central downloader: data/regions_v2/candidates_clean/<region>.json (after audit.py --fix) → data/regions_v2/audio/<region>/<id>.<ext>.

One process for all regions (parallel downloads trigger IP bans). Regions are visited round-robin.
  bili      yt-dlp, native best audio (m4a), Firefox cookies, sleep U(8, 20) s
  yt        yt-dlp as in v1 (src/secaiqu/download_curated.py): Firefox cookies, node JS runtime, sleep U(45, 90) s,
            1 h cooldown on the bot wall. YouTube and Bilibili items are interleaved so YouTube pacing overlaps
            Bilibili work.
  europeana direct media URL via urllib
Re-runnable: items already on disk are skipped. Writes data/regions_v2/manifest.csv (candidate fields + status).

Run (py312): python src/secaiqu/v2/download.py [--regions 湘,粤] [--platforms bili,yt] [--manifest-only]
"""

import argparse
import json
import random
import time
import urllib.request
from pathlib import Path

import pandas as pd
import yt_dlp

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "data" / "regions_v2"
OUT, MANIFEST = V2 / "audio", V2 / "manifest.csv"
CAND = V2 / "candidates_clean"  # audited list (audit.py --fix)
NODE = Path.home() / "miniforge3" / "envs" / "node" / "bin" / "node"
AUDIO_EXTS = {".webm", ".m4a", ".opus", ".mp3", ".ogg", ".mp4", ".wav", ".flac", ".aac"}
SLEEP = {"bili": (8, 20), "yt": (45, 90), "europeana": (3, 8)}


def audio_file(region, iid):
    for p in (OUT / region).glob(f"{iid}.*"):
        if p.suffix in AUDIO_EXTS:
            return p
    return None


def load_candidates(regions=None):
    out = []
    for f in sorted(CAND.glob("*.json")):
        d = json.loads(f.read_text())
        if regions and d["region"] not in regions:
            continue
        for i, c in enumerate(d["candidates"]):
            out.append({"region": d["region"], "rank": i + 1, **c})
    return out


def round_robin(items):
    by = {}
    for c in items:
        by.setdefault(c["region"], []).append(c)
    out, k = [], 0
    while any(by.values()):
        for r in list(by):
            if by[r]:
                out.append(by[r].pop(0))
        k += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default=None)
    ap.add_argument("--platforms", default="bili,yt,europeana")
    ap.add_argument("--browser", default="firefox")
    ap.add_argument("--cooldown", type=float, default=3600)
    ap.add_argument("--max-cooldowns", type=int, default=6)
    ap.add_argument("--manifest-only", action="store_true")
    ap.add_argument("--retry-failed", action="store_true", help="also retry items marked failed in manifest.csv")
    ap.add_argument("--player-client", default=None, help="YouTube player client(s) for 403 retries, e.g. 'default'")
    a = ap.parse_args()
    regions = set(a.regions.split(",")) if a.regions else None
    plats = set(a.platforms.split(","))
    cands = load_candidates(regions)
    prev = pd.read_csv(MANIFEST) if MANIFEST.exists() else pd.DataFrame()
    prev_st = {(r.region, r.id): (r.status, r.error) for r in prev.itertuples()} if len(prev) else {}
    todo = [] if a.manifest_only else round_robin(
        [c for c in cands if c.get("platform") in plats and not audio_file(c["region"], c["id"])
         and (a.retry_failed or prev_st.get((c["region"], c["id"]), ("", ""))[0] != "failed")])
    print(f"{len(cands)} candidates, {len(todo)} to fetch", flush=True)

    base = {"format": "bestaudio/best", "noplaylist": True, "quiet": True, "no_warnings": True, "retries": 3,
            "writeinfojson": True, "noprogress": True, "cookiesfrombrowser": (a.browser,),
            "match_filter": yt_dlp.utils.match_filter_func("duration <= 900")}
    yt_opts = {**base, "js_runtimes": {"node": {"path": str(NODE)}} if NODE.exists() else {}}
    if a.player_client:
        yt_opts["extractor_args"] = {"youtube": {"player_client": a.player_client.split(",")}}
    status, cooldowns, next_ok = {}, 0, {"bili": 0.0, "yt": 0.0, "europeana": 0.0}
    queue = list(todo)
    while queue:
        # pick the first item whose platform is ready (interleave YouTube's long pacing with Bilibili)
        now = time.time()
        idx = next((i for i, c in enumerate(queue) if next_ok[c["platform"]] <= now), None)
        if idx is None:
            time.sleep(max(1.0, min(next_ok[c["platform"]] for c in queue) - now))
            continue
        c = queue.pop(idx)
        d = OUT / c["region"]
        d.mkdir(parents=True, exist_ok=True)
        key = (c["region"], c["id"])
        try:
            if c["platform"] == "europeana":
                ext = Path(c["url"].split("?")[0]).suffix or ".mp3"
                req = urllib.request.Request(c["url"], headers={"User-Agent": "Mozilla/5.0"})
                (d / f"{c['id']}{ext}").write_bytes(urllib.request.urlopen(req, timeout=120).read())
            else:
                opts = yt_opts if c["platform"] == "yt" else base
                with yt_dlp.YoutubeDL({**opts, "outtmpl": str(d / f"{c['id']}.%(ext)s")}) as ydl:
                    ydl.extract_info(c["url"], download=True)
            ok = audio_file(*key) is not None
            status[key] = ("ok", None) if ok else ("failed", "no file (filtered: duration > 900 s?)")
            print(f"[{len(todo) - len(queue)}/{len(todo)}] {status[key][0]:6s} {c['platform']:4s} {c['region']} "
                  f"{c.get('title', '')[:50]}", flush=True)
        except Exception as e:  # noqa: BLE001
            msg = str(e).splitlines()[0][:300]
            if c["platform"] == "yt" and ("not a bot" in msg or "Sign in" in msg):
                cooldowns += 1
                if cooldowns > a.max_cooldowns:
                    print("YouTube bot wall persists — dropping remaining YouTube items this run", flush=True)
                    queue = [q for q in queue if q["platform"] != "yt"]
                else:
                    print(f"YouTube bot wall — pausing YouTube {a.cooldown:.0f}s ({cooldowns})", flush=True)
                    queue.append(c)
                    next_ok["yt"] = time.time() + a.cooldown
                continue
            status[key] = ("failed", msg)
            print(f"[{len(todo) - len(queue)}/{len(todo)}] FAILED {c['platform']} {c['region']} {c['id']} {msg}",
                  flush=True)
        lo, hi = SLEEP[c["platform"]]
        next_ok[c["platform"]] = time.time() + random.uniform(lo, hi)

    rows = []
    for c in load_candidates():
        key = (c["region"], c["id"])
        f = audio_file(*key)
        info_p = OUT / c["region"] / f"{c['id']}.info.json"
        info = json.loads(info_p.read_text()) if (f and info_p.exists()) else {}
        st, err = status.get(key) or (("ok", None) if f else prev_st.get(key, ("pending", None)))
        rows.append({**c, "video_id": c["id"], "audio_path": str(f.relative_to(ROOT)) if f else None, "status": "ok" if f else st,
                     "error": None if f else err, "uploader": info.get("uploader"),
                     "uploader_id": info.get("uploader_id"), "upload_date": info.get("upload_date"),
                     "duration_s_actual": info.get("duration"), "license": info.get("license")})
    pd.DataFrame(rows).to_csv(MANIFEST, index=False)
    df = pd.DataFrame(rows)
    print(df.groupby("region").status.value_counts().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
