"""
Singer-name redaction shared by the release tables (rule: personal names only for national heritage bearers,
tier A1; everyone else gets the pseudonymous singer_id).

private_names(public): every singer name the curators recorded in any round (rounds 1-3 manifests, the round-1
re-curation and the Musical Map of China descriptions), minus the public names and minus any name that is a substring of a public name.
redact(text, names, keep): replace each private name in free text with "[singer]", longest first, except names in
`keep` (e.g. the credited composer / lyricist / arranger of that song, whose authorship is a published fact).
Only names written in Chinese characters are matched: short Latin strings match inside ordinary words. Ensembles,
institutions, roles, provinces and two-character names that also occur in song titles are not treated as names.
"""

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [(ROOT / "data" / "regions_curated" / "v1_provenance.csv", "singer"),
           (ROOT / "data" / "rhymoi" / "rhymoi_items.csv", "singers"),  # Musical Map of China description singers
           *((p, "singer") for p in sorted((ROOT / "data").glob("regions_v*/manifest.csv")))]  # rounds ≥ 2
SPLIT = r"[、,，/&和与 ;；]+"
# ensembles, institutions and roles are not personal names (no privacy issue; redacting them loses information)
NOT_PERSON = re.compile(r"团|队|组|会|馆|院|学校|艺术家|传承人|领唱|合唱|演唱|村民|渔民|老人|社|站|中心|协会|乐团|歌舞")
PROVINCES = set("北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 "
                "海南 重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆 台湾".split())


def split_names(v) -> set[str]:
    return {x.strip() for x in re.split(SPLIT, re.sub(r"[（(].*?[)）]", "", str(v))) if x.strip()}


def private_names(public: set[str]) -> list[str]:
    names = set()
    for p, col in SOURCES:
        if p.exists():
            for v in pd.read_csv(p).get(col, pd.Series(dtype=object)).dropna():
                names |= split_names(v)
    # two-character names that are also title words (云朵, 金花 …) cannot be redacted safely by string matching
    titles = " ".join(pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv").song_name.dropna().astype(str))
    out = {x for x in names if len(x) >= 2 and re.fullmatch(r"[一-鿿·]+", x)
           and not any(x in p for p in public) and not NOT_PERSON.search(x) and x not in PROVINCES
           and not (len(x) == 2 and x in titles)}
    return sorted(out, key=len, reverse=True)


def redact(text, names: list[str], keep: set[str] = frozenset()):
    if not isinstance(text, str):
        return text
    for n in names:
        if n not in keep and not any(n in k for k in keep):
            text = text.replace(n, "[singer]")
    return text
