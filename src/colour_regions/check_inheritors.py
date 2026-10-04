"""
Check named singers against the national list of representative heritage bearers (国家级非物质文化遗产代表性传承人,
https://www.ihchina.cn/art/representative.html). Splits provenance tier A into
  A1  singer found on the national list, with a province that matches the recording
  A2  named singer whose place is stated by the uploader only (incl. provincial-level bearers, not on this list)
The national list does not cover provincial or county lists, so A2 is not "wrong", only less independently attested.

Input : data/colour_regions/recordings.csv (needs the internal singer names: rebuilt from the curation files)
Output: data/regions_curated/ihchina_check.csv (one row per queried name; cached, resumable)
Run (py312): python src/colour_regions/check_inheritors.py
"""

import json
import re
import subprocess
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "regions_curated" / "ihchina_check.csv"
URL = "https://www.ihchina.cn/art/representative.html?keywords={}"


def names() -> pd.DataFrame:
    """Singers of tier-A items or with heritage status, from the curation files (names are not in the release)."""
    v1 = pd.read_csv(ROOT / "data" / "regions_curated" / "v1_provenance.csv").rename(columns={"video_id": "item_id"})
    v2 = pd.read_csv(ROOT / "data" / "regions_v2" / "manifest.csv").rename(columns={"id": "item_id"})
    d = pd.concat([v1[["item_id", "singer", "singer_inheritor", "provenance_tier", "province"]],
                   v2[["item_id", "singer", "singer_inheritor", "provenance_tier", "province"]]])
    d = d[(d.provenance_tier == "A") | d.singer_inheritor.notna()]
    rows = []
    for r in d.itertuples():
        for n in re.split(r"[、,，/&和与 ]+", str(r.singer)):
            n = re.sub(r"[（(].*?[)）]|演唱|领唱", "", n).strip()
            if 2 <= len(n) <= 5 and re.fullmatch(r"[一-鿿·]+", n):
                rows.append(dict(item_id=r.item_id, name=n, province=r.province))
    return pd.DataFrame(rows)


def query(name: str) -> list[dict]:
    out = subprocess.run(["curl", "-s", "-m", "40", "-A", "Mozilla/5.0", URL.format(name)],
                         capture_output=True, text=True).stdout
    try:
        return json.loads(out).get("list") or []
    except json.JSONDecodeError:
        return [{"error": out[:80]}]


def main() -> None:
    todo = names()
    done = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=["name"])
    rows = done.to_dict("records")
    for name in sorted(set(todo.name) - set(done.name)):
        hits = query(name)
        exact = [h for h in hits if h.get("title") == name]
        rows.append(dict(name=name, n_hits=len(hits), n_exact=len(exact), error="error" in (hits[0] if hits else {}),
                         ih_projects="; ".join(f"{h.get('project')} ({h.get('province')}, {h.get('rx_time')})"
                                               for h in exact),
                         ih_provinces="; ".join(str(h.get("province")) for h in exact)))
        pd.DataFrame(rows).to_csv(OUT, index=False)
        time.sleep(1.5)
    res = pd.DataFrame(rows)
    m = todo.merge(res, on="name", how="left")
    m["match"] = [isinstance(p, str) and isinstance(q, str) and q[:2] in p
                  for p, q in zip(m.ih_provinces, m.province)]
    m.groupby("item_id").match.any().rename("on_national_list").to_csv(
        ROOT / "data" / "regions_curated" / "ihchina_items.csv")
    print(f"names {len(res)}, exact hits {int((res.n_exact > 0).sum())}, errors {int(res.error.sum())}; "
          f"items verified {int(m.groupby('item_id').match.any().sum())} of {m.item_id.nunique()}")


if __name__ == "__main__":
    main()
