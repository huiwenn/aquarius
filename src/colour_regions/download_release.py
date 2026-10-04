"""
Download the audio of the Colour Regions recordings from their sources and verify each file against the release.

For every row of recordings.csv: yt-dlp fetches the native audio stream (no transcoding), then the file is checked
  1. duration within ±2 s of `duration_s`
  2. Chromaprint fingerprint of the first 120 s (fpcalc) close to the released one (fingerprints.csv):
     bit error rate ≤ 0.25 over the aligned 32-bit sub-fingerprints
A file that fails a check is kept but listed as `mismatch` in download_report.csv, so users know which derived data
may not correspond to their copy. Paced to respect the platforms (YouTube 45–90 s, Bilibili 8–20 s between items).

Usage:  python download_release.py --release DIR --out AUDIO_DIR [--platforms youtube,bilibili] [--core-only]
Needs: yt-dlp, ffmpeg, fpcalc (Chromaprint); for YouTube, browser cookies (--cookies-from-browser firefox).
"""

import argparse
import json
import random
import subprocess
import time
from pathlib import Path

import pandas as pd

PAUSE = {"youtube": (45, 90), "bilibili": (8, 20), "europeana": (2, 5)}


def raw_fingerprint(path: Path) -> list[int]:
    out = subprocess.run(["fpcalc", "-raw", "-json", "-length", "120", str(path)], capture_output=True, text=True)
    try:
        return json.loads(out.stdout)["fingerprint"]
    except (json.JSONDecodeError, KeyError):
        return []


def ber(a: list[int], b: list[int]) -> float:
    """Best bit error rate over small offsets (±20 frames)."""
    best = 1.0
    for off in range(-20, 21):
        pairs = [(a[i], b[i + off]) for i in range(len(a)) if 0 <= i + off < len(b)]
        if len(pairs) < 50:
            continue
        bits = sum(bin((x ^ y) & 0xFFFFFFFF).count("1") for x, y in pairs)
        best = min(best, bits / (32 * len(pairs)))
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--platforms", default="youtube,bilibili,europeana")
    ap.add_argument("--core-only", action="store_true")
    ap.add_argument("--cookies-from-browser", default="firefox")
    a = ap.parse_args()
    rec = pd.read_csv(a.release / "recordings.csv")
    fps = pd.read_csv(a.release / "fingerprints_raw.csv").set_index("item_id") \
        if (a.release / "fingerprints_raw.csv").exists() else None
    rec = rec[rec.platform.isin(a.platforms.split(","))]
    if a.core_only:
        rec = rec[rec.core]
    report = []
    for r in rec.itertuples():
        d = a.out / r.region
        d.mkdir(parents=True, exist_ok=True)
        have = list(d.glob(f"{r.item_id}.*"))
        if not have:
            cmd = ["yt-dlp", "-f", "ba/b", "--no-playlist", "-o", str(d / f"{r.item_id}.%(ext)s")]
            if r.platform != "europeana":
                cmd += ["--cookies-from-browser", a.cookies_from_browser]
            ok = subprocess.run(cmd + [r.url]).returncode == 0
            time.sleep(random.uniform(*PAUSE.get(r.platform, (5, 10))))
            have = list(d.glob(f"{r.item_id}.*"))
            if not ok or not have:
                report.append(dict(item_id=r.item_id, status="unavailable"))
                continue
        f = have[0]
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(f)], capture_output=True, text=True).stdout or "nan")
        status = "ok" if abs(dur - r.duration_s) <= 2 else "mismatch (duration)"
        if status == "ok" and fps is not None and r.item_id in fps.index:
            e = ber(raw_fingerprint(f), json.loads(fps.loc[r.item_id, "fingerprint_raw"]))
            status = "ok" if e <= 0.25 else f"mismatch (fingerprint BER {e:.2f})"
        report.append(dict(item_id=r.item_id, status=status, file=str(f), duration_s=dur))
    pd.DataFrame(report).to_csv(a.out / "download_report.csv", index=False)
    print(pd.DataFrame(report).status.value_counts().to_string())


if __name__ == "__main__":
    main()
