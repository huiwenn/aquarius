"""
Musical Map of China (中国音乐地图 / Rhymoi Music): parse the structured video descriptions into fields.

The series descriptions follow one template, for example
    民间歌曲  体裁：花儿  民族：回族  地区：甘肃临夏
    演唱、冬不拉演奏：吾丽波森·肯吉木
    扬琴：…
so the genre (体裁), ethnic group (民族), stated area (地区), singers (演唱) and accompanying instruments can be read
directly. `parse()` returns these fields; `items()` builds data/rhymoi/rhymoi_items.csv for every series video whose
metadata we hold (round 1 info.json files + data/rhymoi/info/ from rhymoi_fetch.py), with a rule-based colour
region, a tier by stated area, and the semantic flags used in recordings.csv.

Tier rule (author decision 2026-10-04): a named singer with a stated county / village → A2; province or prefecture
only → C; national heritage bearers become A1 through check_inheritors.py, as for every other item.

Run (py312): python src/colour_regions/rhymoi.py
"""

import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "rhymoi"
CHANNEL_ID = "UCN19zbpNCX9lrbKreffuSAQ"

FORMS = ("民间歌曲", "民间歌舞", "民间器乐", "民间音乐", "说唱音乐", "戏曲音乐", "宗教音乐", "宫廷音乐", "文人音乐")
VOICE_ROLE = re.compile(r"演唱|领唱|合唱|伴唱|对唱|独唱|歌手|呼麦|吟唱|说唱")
# ethnic group → colour region for the four minority song areas; Han and other groups go by province (below)
ETHNIC_REGION = {
    **{e: "北方草原文化民歌区" for e in ("蒙古", "达斡尔", "鄂伦春", "鄂温克", "赫哲")},
    **{e: "新疆民歌区" for e in ("维吾尔", "哈萨克", "柯尔克孜", "塔吉克", "锡伯", "乌孜别克", "塔塔尔", "俄罗斯")},
    **{e: "藏族民歌区" for e in ("藏", "门巴", "珞巴")},
    **{e: "西南多民族古老原始文化民歌区" for e in (
        "苗", "侗", "彝", "壮", "白", "哈尼", "傣", "傈僳", "佤", "拉祜", "纳西", "景颇", "布朗", "阿昌", "普米", "怒",
        "独龙", "基诺", "德昂", "布依", "水", "仡佬", "瑶", "土家", "毛南", "仫佬", "京", "羌", "摩梭")},
    # hua'er singers of the Hehuang area are coded Northwest Plateau (docs/thesis_evidence_plan.md B4)
    **{e: "西北部高原" for e in ("回", "土", "撒拉", "东乡", "保安", "裕固")},
}
PROVINCE_REGION = {  # Han items: main region of the province (colour-region boundaries cut provinces: needs_review)
    "山东": "东北部平原", "河北": "东北部平原", "天津": "东北部平原", "北京": "东北部平原", "辽宁": "东北部平原",
    "吉林": "东北部平原", "黑龙江": "东北部平原", "陕西": "西北部高原", "山西": "西北部高原", "甘肃": "西北部高原",
    "宁夏": "西北部高原", "青海": "西北部高原", "安徽": "江淮", "上海": "江浙平原", "浙江": "江浙平原",
    "湖北": "江汉", "湖南": "湘", "江西": "赣", "福建": "闽台", "台湾": "闽台", "广东": "粤", "海南": "粤",
    "四川": "西南高原", "重庆": "西南高原", "贵州": "西南高原", "云南": "西南高原", "内蒙古": "北方草原文化民歌区",
    "新疆": "新疆民歌区", "西藏": "藏族民歌区", "广西": "粤", "河南": "江汉", "江苏": "江淮"}
SPLIT_PROVINCES = {"安徽", "湖南", "湖北", "江苏", "河南", "广西", "陕西", "内蒙古", "四川", "云南", "贵州", "青海", "广东", "福建", "江西"}
HAKKA = re.compile(r"客家|兴国|梅州|梅县|赣南|闽西|长汀|上杭")


KEY = re.compile(r"(体裁|民族|地区|语言|汉语歌词编译|歌词编译|歌词翻译)\s*[：:]")


def header_fields(head: str) -> dict:
    """Split '民间歌曲  体裁：堆谐 民族：藏族 地区：西藏拉萨' at the known keys."""
    ms = list(KEY.finditer(head))
    out = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(head)
        out[m.group(1)] = head[m.end():end].strip(" ，,。　") or None
    return out


def parse(desc: str, title: str = "") -> dict:
    zh = "\n".join(l for l in (desc or "").splitlines() if re.search(r"[一-鿿]", l)
                   and not re.search(r"订阅|rhymoi|Rhymoi|版权|All Rights|#", l))
    head = next((l for l in zh.splitlines() if KEY.search(l)), "")
    form = next((f for f in FORMS if f in head), None)
    hf = header_fields(head)
    singers, instruments, roles = [], [], []
    for line in zh.splitlines():
        m = re.match(r"^\s*([^：:]{1,30})[：:]\s*(.+)$", line)
        if not m or line == head or KEY.search(line):
            continue
        role, names = m.group(1), [n.strip() for n in re.split(r"[、，,；;/ ]+", m.group(2)) if n.strip()]
        parts = [p for p in re.split(r"[、，,及和与]", role) if p]
        roles.append(role)
        if VOICE_ROLE.search(role):
            singers += names
        for p in parts:
            if not VOICE_ROLE.search(p) and not re.search(r"歌词|编译|翻译|记谱|整理|作词|作曲|编曲|录音|制作|监制|摄", p):
                instruments.append(re.sub(r"演奏|伴奏$", "", p))
    area = hf.get("地区")
    return dict(form=form, genre_native=hf.get("体裁"), ethnic_native=hf.get("民族"), area=area,
                singers="、".join(dict.fromkeys(singers)) or None, n_singers=len(dict.fromkeys(singers)),
                instruments="、".join(dict.fromkeys(i for i in instruments if i)) or None,
                roles="|".join(roles) or None)


def area_level(area: str | None, gaz: pd.DataFrame) -> tuple[str | None, str | None, str]:
    """(province, county_or_area, level) for a stated area such as '福建龙岩永定' or '西藏日喀则、林芝等地区'.
    level: county (exactly one place, matched to a county of that province), prefecture, multi (several places),
    province, or none. Matching follows geocode.py: gazetteer names with their suffix removed, contained in the text."""
    if not area:
        return None, None, "none"
    a = re.sub(r"等地区?|一带|地区$", "", area)
    prov = next((p for p in PROVINCE_REGION if a.startswith(p)), None) or \
        next((p for p in PROVINCE_REGION if p in a), None)
    rest = re.sub(r"^(省|市|自治区)", "", a[len(prov):] if prov and a.startswith(prov) else a).strip()
    if not rest:
        return prov, None, "province" if prov else "none"
    if re.search(r"[、，,/和及 ]", rest):
        return prov, rest, "multi"
    g = gaz if prov is None else gaz[gaz.province.fillna("").str.startswith(prov)]
    if rest in set(g.loc[g.level == "prefecture", "short"]):  # "湖南岳阳" = the city, not 岳阳县
        return prov, rest, "prefecture"
    for level in ("county", "prefecture"):
        if any(len(s) >= 2 and s in rest for s in g.loc[g.level == level, "short"]):
            return prov, rest, level
    return prov, rest, "area"


def region_of(ethnic: str | None, prov: str | None, text: str) -> tuple[str | None, str, bool]:
    """(colour region, rule, needs_review)."""
    eth = [e.strip() for e in re.split(r"[、/，, ]", ethnic or "") if e.strip()]
    # "彝族撒尼人" → 彝, "哈尼族爱伲人" → 哈尼: the longest group name the stated text starts with
    eth = [max((k for k in list(ETHNIC_REGION) + ["汉"] if e.startswith(k)), key=len, default=e.removesuffix("族"))
           for e in eth]
    for e in eth:
        if e in ETHNIC_REGION:
            r = ETHNIC_REGION[e]
            if e in ("回", "土", "撒拉", "东乡", "保安", "裕固") and prov == "新疆":
                return "新疆民歌区", f"ethnic:{e}+province", True
            # minority groups living inside Han regions (e.g. 湘西 Miao/Tujia) are a curator decision
            return r, f"ethnic:{e}", len(eth) > 1 or (r == "西南多民族古老原始文化民歌区" and prov in ("湖南", "湖北"))
    if HAKKA.search(text):
        return "客家特区", "hakka", False
    if eth and eth[0] not in ("汉", ""):
        return None, f"ethnic:{eth[0]}:unmapped", True
    if prov in PROVINCE_REGION:
        return PROVINCE_REGION[prov], "province", prov in SPLIT_PROVINCES
    return None, "none", True


def semantic_flags(p: dict, series: bool) -> str:
    """Semicolon list of semantic features (see metadata/README.md, column `feature_flags`)."""
    f = []
    if series:
        f.append("series:musical_map_of_china")
    if p.get("instruments"):
        f.append("accompanied")
        f += [f"instrument:{i}" for i in p["instruments"].split("、")]
    elif p.get("roles"):
        f.append("unaccompanied")
    if (p.get("n_singers") or 0) >= 2:
        f.append("multiple_singers")
    if p.get("form") == "民间歌舞":
        f.append("song_and_dance")
    return ";".join(f) or ""


def items() -> pd.DataFrame:
    sys.path.insert(0, str(ROOT / "src"))
    from colour_regions.geocode import short
    gaz = pd.read_csv(ROOT / "data" / "geo" / "gazetteer.csv")
    gaz["short"] = gaz.name.map(short)
    files = glob.glob(str(ROOT / "data" / "regions_audio" / "*" / "*.info.json")) + glob.glob(str(D / "info" / "*.json"))
    rows = []
    for f in files:
        j = json.load(open(f))
        if j.get("channel_id") != CHANNEL_ID:
            continue
        p = parse(j.get("description") or "", j.get("title") or "")
        prov, county, lvl = area_level(p["area"], gaz)
        reg, rule, review = region_of(p["ethnic_native"], prov, (j.get("title") or "") + (p["genre_native"] or ""))
        sung = bool(p["singers"]) or p["form"] in ("民间歌曲", "民间歌舞")
        rows.append(dict(item_id=j["id"], title=j.get("title"), duration_s=j.get("duration"),
                         upload_date=j.get("upload_date"), in_round1="regions_audio" in f, **p,
                         province=prov, county_or_area=county, area_level=lvl, region=reg, region_rule=rule,
                         needs_review=review, sung=sung,
                         tier=("A2" if p["singers"] and lvl == "county" else "C"),
                         feature_flags=semantic_flags(p, True)))
    d = pd.DataFrame(rows).drop_duplicates("item_id")
    d["eligible"] = d.sung & d.form.isin(["民间歌曲", "民间歌舞"]).fillna(False) & d.duration_s.between(40, 600) \
        & d.region.notna()
    return d


def main() -> None:
    d = items()
    D.mkdir(parents=True, exist_ok=True)
    d.to_csv(D / "rhymoi_items.csv", index=False)
    print(len(d), "series videos with metadata;", int(d.in_round1.sum()), "in round 1;",
          int(d.eligible.sum()), "eligible sung folk items")
    print(d.groupby(["in_round1", "tier"]).size().to_string())
    print(d[d.eligible].groupby("region").agg(n=("item_id", "size"), new=("in_round1", lambda s: (~s).sum()),
                                              review=("needs_review", "sum")).to_string())


if __name__ == "__main__":
    main()
