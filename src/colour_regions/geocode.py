"""
Place each recording on the map from its stated place (county_or_area, province) using data/geo/gazetteer.csv.

Matching: county → prefecture → province, finest level wins; a county or prefecture must lie in the stated province
when one is given (names repeat across provinces). Names are matched with and without their administrative suffix
(县/市/区/旗/自治县 …), e.g. "桑植" ↔ "桑植县", "江华" ↔ "江华瑶族自治县".
Adds geo_level (county / prefecture / province / none), geo_name, lon, lat to data/colour_regions/recordings.csv.
Run (py312): python src/colour_regions/geocode.py
"""

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SUFFIX = re.compile(r"(各族自治县|自治县|自治旗|自治州|地区|林区|特区|新区|县|市|区|旗|盟|州)$")
ETHNIC = re.compile(r"(土家族|苗族|瑶族|侗族|彝族|壮族|白族|哈尼族|傣族|藏族|羌族|回族|蒙古族|满族|畲族|仡佬族|布依族|水族|"
                    r"黎族|傈僳族|纳西族|拉祜族|佤族|景颇族|怒族|独龙族|普米族|阿昌族|德昂族|基诺族|哈萨克族|柯尔克孜族|"
                    r"塔吉克族|锡伯族|达斡尔族|鄂伦春族|鄂温克族|裕固族|撒拉族|东乡族|保安族|土族|仫佬族|毛南族|京族|各族)+$")
PROV_SHORT = re.compile(r"(省|市|自治区|壮族自治区|回族自治区|维吾尔自治区|特别行政区)$")


def short(name: str) -> str:
    s = SUFFIX.sub("", name)
    s = ETHNIC.sub("", s)
    return s if len(s) >= 2 else name


def main() -> None:
    g = pd.read_csv(ROOT / "data" / "geo" / "gazetteer.csv")
    g["short"] = g.name.map(short)
    g["prov_short"] = g.province.fillna("").map(lambda p: PROV_SHORT.sub("", p).replace("壮族", "").replace("回族", "")
                                                .replace("维吾尔", ""))
    provs = g[g.level == "province"].assign(prov_short=lambda d: d.name.map(
        lambda p: PROV_SHORT.sub("", p).replace("壮族", "").replace("回族", "").replace("维吾尔", "")))
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv")
    out = []
    for r in rec.itertuples():
        text = f"{r.county_or_area if pd.notna(r.county_or_area) else ''} {r.province if pd.notna(r.province) else ''}"
        prov = next((p for p in provs.itertuples() if p.prov_short and p.prov_short in text), None)
        best = None
        for level in ("county", "prefecture"):
            cand = g[g.level == level]
            if prov is not None:
                cand = cand[cand.province == prov.name]
            area = str(r.county_or_area) if pd.notna(r.county_or_area) else ""  # never search the province name:
            hits = [c for c in cand.itertuples()                                 # "黑龙江" contains "龙江(县)"
                    if (c.name in area or (len(c.short) >= 2 and c.short in area))]
            if hits:
                best = max(hits, key=lambda c: len(c.short))
                break
        if best is None and prov is not None:
            best = prov
            level = "province"
        out.append(dict(geo_level=level if best is not None else "none",
                        geo_name=best.name if best is not None else None,
                        lon=best.lon if best is not None else None, lat=best.lat if best is not None else None))
    o = pd.DataFrame(out, index=rec.index)
    for c in o:
        rec[c] = o[c]
    rec.to_csv(ROOT / "data" / "colour_regions" / "recordings.csv", index=False)
    print(rec.geo_level.value_counts().to_string())
    print(rec.groupby("region_en").geo_level.agg(lambda s: (s == "county").mean()).round(2).to_string())


if __name__ == "__main__":
    main()
