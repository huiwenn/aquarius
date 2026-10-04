"""
Audit collection v2 candidates (or the downloaded manifest) against the rules in docs/collection_v2.md.

Per region: n, distinct channels, max items per channel, v1-channel / v1-video overlap, provenance tier mix (A+B ≥ 50%),
performance mix (原生态/field ≥ 70%, 民族唱法 ≤ 30%), duration out of [40, 600] s, max recordings per song (≤ 2),
share of song titles not in v1 (≥ 50%), dating flags (composed must be 0; titles listed as composed/modern in the v1
dating table are flagged too). Prints a table and writes data/regions_v2/audit.csv; --fix drops hard-rule violators
into data/regions_v2/candidates_clean/ (downloaded set = ok status only with --manifest).

Run (py312): python src/secaiqu/v2/audit.py [--manifest] [--fix]
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "data" / "regions_v2"


def norm(s):
    return re.sub(r"[\s《》〈〉()（）\[\]【】·・、,，.。!！?？\-—_'\"“”]", "", str(s or "")).lower()


def load(manifest: bool) -> pd.DataFrame:
    if manifest:
        d = pd.read_csv(V2 / "manifest.csv")
        return d[d.status == "ok"].copy()
    rows = []
    for f in sorted((V2 / "candidates").glob("*.json")):
        j = json.loads(f.read_text())
        rows += [{"region": j["region"], **c} for c in j["candidates"]]
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    d = load(a.manifest)
    v1 = pd.read_csv(ROOT / "data" / "regions_transcription" / "dataset_index.csv")
    v1_ch, v1_vid = set(v1.channel.astype(str)), set(v1.video_id.astype(str))
    v1_songs = {r: set(map(norm, g.song_name)) for r, g in v1.groupby("region")}
    dates = pd.read_csv(ROOT / "data" / "regions_curated" / "song_dates" / "all_songs.csv")
    composed = set(map(norm, dates[~dates.song_type.astype(str).str.startswith("traditional")
                                   & dates.song_type.notna()].song_name))

    d["song_n"] = d.song_name.map(norm)
    # channel key: platform channel id when known (several deleted Bilibili accounts all display "账号已注销")
    cid = d["channel_id"] if "channel_id" in d else pd.Series(index=d.index, dtype=object)
    d["ch_key"] = [f"{p}:{i}" if pd.notna(i) and str(i) not in ("", "None") else f"{p}:{c}"
                   for p, i, c in zip(d.platform, cid, d.channel)]
    # v1 labels re-uploaded under another name (e.g. Bilibili "瑞鸣中国音乐地图" = v1's Rhymoi channel)
    alias = d.channel.astype(str).str.contains("瑞鸣|Rhymoi|中国音乐地图", regex=True)
    d["bad_v1_channel"] = d.channel.astype(str).isin(v1_ch) | alias
    d["bad_v1_video"] = d.id.astype(str).isin(v1_vid)
    d["bad_duration"] = ~pd.to_numeric(d.duration_s, errors="coerce").between(40, 600)
    d["bad_composed"] = (d.get("dating_flag", "").astype(str) == "composed") | d.song_n.isin(composed)
    d["song_new"] = [s not in v1_songs.get(r, set()) for r, s in zip(d.region, d.song_n)]
    pt = d.performance_type.astype(str)
    rows = []
    for r, g in d.groupby("region"):
        rows.append({"region": r, "n": len(g), "channels": g.ch_key.nunique(),
                     "max_per_ch": g.ch_key.value_counts().max(),
                     "bili": (g.platform == "bili").sum(), "yt": (g.platform == "yt").sum(),
                     "v1_ch": g.bad_v1_channel.sum(), "v1_vid": g.bad_v1_video.sum(),
                     "tierAB%": round(100 * g.provenance_tier.isin(["A", "B"]).mean()),
                     "tierA": (g.provenance_tier == "A").sum(),
                     "orig%": round(100 * pt[g.index].isin(["原生态", "field"]).mean()),
                     "民族%": round(100 * (pt[g.index] == "民族唱法").mean()),
                     "bad_dur": g.bad_duration.sum(), "composed": g.bad_composed.sum(),
                     "check": (g.get("dating_flag", "").astype(str) == "check").sum(),
                     "max_per_song": g.song_n.value_counts().max(), "new_song%": round(100 * g.song_new.mean())})
    rep = pd.DataFrame(rows)
    print(rep.to_string(index=False))
    rep.to_csv(V2 / ("audit_downloaded.csv" if a.manifest else "audit.csv"), index=False)
    if a.fix:
        hard = d.bad_v1_channel | d.bad_v1_video | d.bad_duration | d.bad_composed
        print(f"dropping {hard.sum()} hard-rule violators")
        out = V2 / "candidates_clean"
        out.mkdir(exist_ok=True)
        keep = d[~hard]
        for r, g in keep.groupby("region"):
            # enforce channel cap ≤ 4 and ≤ 2 per song, in curator order
            g = g[g.groupby("ch_key").cumcount() < 4]
            g = g[g.groupby("song_n").cumcount() < 2]
            cols = [c for c in g.columns if not c.startswith("bad_") and c not in ("song_n", "song_new", "region", "ch_key")]
            (out / f"{r}.json").write_text(json.dumps({"region": r, "candidates": g[cols].to_dict("records")},
                                                      ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
