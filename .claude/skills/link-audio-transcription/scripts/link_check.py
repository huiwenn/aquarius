"""Check that every link in a manifest still works, without downloading.
YouTube: oEmbed. Bilibili: yt-dlp metadata extraction with browser cookies (the web API needs signed requests).
Other: HTTP HEAD. Appends dated rows to the output CSV.
Usage: python link_check.py manifest.csv link_status.csv [--browser firefox] [--pause 1.0]
manifest.csv needs columns: item_id, platform (youtube|bilibili|other), url"""
import argparse, datetime as dt, subprocess, time, urllib.parse
from pathlib import Path
import pandas as pd


def curl_code(url, head=False):
    cmd = ["curl", "-s", "-m", "30", "-A", "Mozilla/5.0", "-o", "/dev/null", "-w", "%{http_code}"] + (["-I"] if head else []) + [url]
    return int(subprocess.run(cmd, capture_output=True, text=True).stdout or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest"); ap.add_argument("out")
    ap.add_argument("--browser", default="firefox"); ap.add_argument("--pause", type=float, default=1.0)
    a = ap.parse_args()
    ydl = None
    rows, today = [], dt.date.today().isoformat()
    for r in pd.read_csv(a.manifest).itertuples():
        if r.platform == "youtube":
            code = curl_code("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(r.url, safe=""))
            ok, why = code == 200, str(code)
        elif r.platform == "bilibili":
            if ydl is None:
                import yt_dlp
                ydl = yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True,
                                        "cookiesfrombrowser": (a.browser,)})
            try:
                info = ydl.extract_info(r.url, download=False, process=False); ok, why = bool(info and info.get("id")), "ok"
            except Exception as e:
                ok, why = False, str(e)[-60:]
        else:
            code = curl_code(r.url, head=True); ok, why = code in (200, 301, 302), str(code)
        rows.append(dict(item_id=r.item_id, platform=r.platform, checked_on=today, available=ok, status=why))
        time.sleep(a.pause)
    new = pd.DataFrame(rows)
    old = pd.read_csv(a.out) if Path(a.out).exists() else pd.DataFrame()
    pd.concat([old, new]).to_csv(a.out, index=False)
    print(new.groupby("platform").available.agg(["sum", "size"]).to_string())


if __name__ == "__main__":
    main()
