"""
County-level gazetteer of China (name, adcode, province, prefecture, centroid) for placing recordings on a map.

Source: DataV.GeoAtlas boundary files (https://geo.datav.aliyun.com/areas_v3/bound/<adcode>_full.json), walked
province → prefecture → county; only names and centroids are kept. Requests are paced and cached.
Output: data/geo/gazetteer.csv (level ∈ province, prefecture, county)
Run (py312): python src/colour_regions/geo_gazetteer.py
"""

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "data" / "geo"
CACHE = GEO / "datav_cache"
URL = "https://geo.datav.aliyun.com/areas_v3/bound/{}_full.json"


def fetch(adcode) -> dict | None:
    f = CACHE / f"{adcode}.json"
    if not f.exists():
        try:
            with urllib.request.urlopen(URL.format(adcode), timeout=30) as r:
                f.write_bytes(r.read())
        except Exception:
            return None
        time.sleep(0.3)
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return None


def rows(g: dict, level: str, province: str, prefecture: str) -> list[dict]:
    out = []
    for ft in g["features"]:
        p = ft["properties"]
        if not p.get("name"):
            continue
        c = p.get("centroid") or p.get("center")
        out.append(dict(level=level, adcode=p["adcode"], name=p["name"], province=province, prefecture=prefecture,
                        lon=c[0], lat=c[1], children=p.get("childrenNum", 0)))
    return out


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    top = fetch(100000)
    out = rows(top, "province", "", "")
    for prov in [r for r in out if r["level"] == "province"]:
        g = fetch(prov["adcode"])
        if not g:
            continue
        sub = rows(g, "prefecture", prov["name"], "")
        out += sub
        for pref in sub:
            if pref["children"]:
                h = fetch(pref["adcode"])
                if h:
                    out += rows(h, "county", prov["name"], pref["name"])
        print(prov["name"], len(out), flush=True)
    pd.DataFrame(out).to_csv(GEO / "gazetteer.csv", index=False)


if __name__ == "__main__":
    main()
