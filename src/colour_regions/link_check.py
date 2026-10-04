"""
Check that every source link still works, without downloading: YouTube oEmbed, the Bilibili video-info API, and an
HTTP HEAD request for archive items. Paced (~1 request/s). Appends a dated column set to
data/colour_regions/link_status.csv (item_id, platform, checked_on, available, http_or_code).
Run (py312): python src/colour_regions/link_check.py
"""

import datetime as dt
import json
import subprocess
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "colour_regions" / "link_status.csv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def curl(url: str, head: bool = False) -> tuple[int, str]:
    cmd = ["curl", "-s", "-m", "30", "-A", UA, "-o", "-", "-w", "\n%{http_code}"] + (["-I"] if head else []) + [url]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    body, _, code = out.rpartition("\n")
    return int(code or 0), body


_ydl = None


def ydl():
    global _ydl
    if _ydl is None:
        import yt_dlp
        _ydl = yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True,
                                 "cookiesfrombrowser": ("firefox",)})
    return _ydl


_bili = None


def bili():
    global _bili
    if _bili is None:
        _bili = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        _bili.addheaders = [("User-Agent", UA), ("Referer", "https://www.bilibili.com/")]
        _bili.open("https://www.bilibili.com/", timeout=30).read()
    return _bili


def check(platform: str, item: str, url: str) -> tuple[bool, str]:
    if platform == "youtube":
        code, _ = curl("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe=""))
        return code == 200, str(code)
    if platform == "bilibili":  # the web API needs signed requests; yt-dlp metadata extraction (no download) works
        try:
            info = ydl().extract_info(url, download=False, process=False)
            return bool(info and info.get("id")), "ok"
        except Exception as e:
            return False, str(e).split(":")[-1].strip()[:60]
    code, _ = curl(url, head=True)
    return code in (200, 301, 302), str(code)


def main() -> None:
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    today = dt.date.today().isoformat()
    rows = []
    for i, r in enumerate(rec.itertuples(), 1):
        ok, why = check(r.platform, r.item_id, r.url)
        rows.append(dict(item_id=r.item_id, platform=r.platform, checked_on=today, available=ok, status=why))
        time.sleep(1.0)
        if i % 100 == 0:
            print(i, flush=True)
    new = pd.DataFrame(rows)
    old = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame()
    pd.concat([old, new]).to_csv(OUT, index=False)
    print(new.groupby("platform").available.agg(["sum", "size"]).to_string())


if __name__ == "__main__":
    main()
