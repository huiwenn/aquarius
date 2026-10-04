"""
Download audio for every YouTube link collected in data/regions/<色彩区>.json.

Audio is saved in its native best-quality stream (no transcoding) to
data/regions_audio/<色彩区>/<video_id>.<ext>, and a manifest with per-item
metadata and download status is written to data/regions_audio/manifest.csv.

Re-running is safe: files already on disk are not re-downloaded.

Run: conda activate py312 && python src/secaiqu/download_audio.py [--workers 4]
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import yt_dlp

ROOT = Path(__file__).resolve().parent.parent.parent
REGIONS_DIR = ROOT / "data" / "regions"
OUT_DIR = ROOT / "data" / "regions_audio"
MANIFEST = OUT_DIR / "manifest.csv"


def collect_links() -> list[dict]:
    items = []
    for path in sorted(REGIONS_DIR.glob("*.json")):
        region = json.loads(path.read_text())
        for link in region["youtube_links"]:
            items.append({
                "region": region["region_name"],
                "region_en": region["region_name_en"],
                "region_type": region["type"],
                "link_title": link["title"],
                "link_description": link.get("description", ""),
                "url": link["url"],
            })
    return items


def download(item: dict) -> dict:
    region_dir = OUT_DIR / item["region"]
    region_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(region_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 5,
        "writeinfojson": True,
        "noprogress": True,
    }
    row = dict(item)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(item["url"], download=True)
        files = [p for p in region_dir.glob(f"{info['id']}.*") if not p.name.endswith(".info.json")]
        row.update({
            "video_id": info["id"],
            "yt_title": info.get("title"),
            "uploader": info.get("uploader"),
            "channel_id": info.get("channel_id"),
            "upload_date": info.get("upload_date"),
            "duration_s": info.get("duration"),
            "license": info.get("license"),
            "audio_codec": info.get("acodec"),
            "audio_path": str(files[0].relative_to(ROOT)) if files else None,
            "status": "ok" if files else "missing_file",
            "error": None,
        })
    except Exception as e:  # unavailable, private, region-locked, etc.
        row.update({"status": "failed", "error": str(e).splitlines()[0][:300]})
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = collect_links()
    print(f"{len(items)} links across {len({i['region'] for i in items})} regions")

    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(download, it) for it in items]
        for n, fut in enumerate(as_completed(futures), 1):
            row = fut.result()
            rows.append(row)
            print(f"[{n}/{len(items)}] {row['status']:7s} {row['region']} {row['url']}"
                  + (f"  ({row['error']})" if row["error"] else ""), flush=True)

    df = pd.DataFrame(rows).sort_values(["region", "url"])
    df.to_csv(MANIFEST, index=False)

    print("\nPer-region results:")
    print(df.pivot_table(index="region", columns="status", values="url",
                         aggfunc="count", fill_value=0).to_string())
    dupes = df[df["video_id"].notna()].duplicated("video_id", keep=False).sum()
    if dupes:
        print(f"\nNote: {dupes} rows share a video_id with another row (same video listed twice).")
    failed = (df["status"] != "ok").sum()
    print(f"\nDone: {len(df) - failed} ok, {failed} not ok. Manifest: {MANIFEST.relative_to(ROOT)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
