#!/usr/bin/env python3
"""Build the map's public, audio-free data bundle from repository metadata."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.json"

ALIASES = {
    "北京": "北京市", "天津": "天津市", "河北": "河北省", "山西": "山西省",
    "内蒙古": "内蒙古自治区", "辽宁": "辽宁省", "吉林": "吉林省", "黑龙江": "黑龙江省",
    "上海": "上海市", "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省",
    "福建": "福建省", "江西": "江西省", "山东": "山东省", "河南": "河南省",
    "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "广西": "广西壮族自治区",
    "海南": "海南省", "重庆": "重庆市", "四川": "四川省", "贵州": "贵州省",
    "云南": "云南省", "西藏": "西藏自治区", "陕西": "陕西省", "甘肃": "甘肃省",
    "青海": "青海省", "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
    "台湾": "台湾省", "香港": "香港特别行政区", "澳门": "澳门特别行政区",
}

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

rows = read_csv(ROOT / "metadata" / "recordings.csv")
link_rows = read_csv(ROOT / "metadata" / "link_status.csv")
links = {r["item_id"]: r for r in link_rows}
groups = defaultdict(list)
unresolved = []
for r in rows:
    raw = (r.get("province") or "").strip()
    province = ALIASES.get(raw)
    if province:
        groups[province].append(r)
    else:
        unresolved.append({"id": r["item_id"], "label": raw or "未标注", "region": r.get("region_en", "")})

features = []
summaries = []
for province, records in sorted(groups.items()):
    region_counts = Counter(r.get("region_en", "") or "未标注" for r in records)
    features.append({"province": province, "count": len(records)})
    summaries.append({
        "province": province,
        "count": len(records),
        "regions": [{"name": n, "count": c} for n, c in region_counts.most_common()],
        "songs": [{
            "id": r["item_id"], "title": r.get("song_name") or r.get("title") or "Untitled recording",
            "videoTitle": r.get("title", ""), "url": r.get("url", ""),
            "region": r.get("region_en", ""), "regionNative": r.get("region", ""),
            "place": " · ".join(x for x in [r.get("county_or_area", ""), r.get("geo_level", "")] if x),
            "ethnicGroup": r.get("ethnic_group", ""), "genre": r.get("song_genre_native") or r.get("genre", ""),
            "performance": r.get("performance_type", ""),
            "availability": links.get(r["item_id"], {}).get("status", "not checked"),
        } for r in records]
    })

OUT.write_text(json.dumps({"features": features, "provinces": summaries, "unresolvedCount": len(unresolved),
                           "total": len(rows), "unresolvedLabels": dict(Counter(x["label"] for x in unresolved))},
                          ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Wrote {OUT.name}: {len(rows)} recordings, {len(features)} matched province units, {len(unresolved)} unresolved locations")
