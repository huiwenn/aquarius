"""Write per-region song-dating CSVs from hand-researched records.

Usage: python -m src.secaiqu.dating.build
Reads data/regions_transcription/dataset_index.csv and research.json (same dir);
songs without a research record get a conservative default (traditional/low, all dates NA).
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
REGIONS = ["西南高原", "西南多民族古老原始文化民歌区", "藏族民歌区", "新疆民歌区", "北方草原文化民歌区"]
COLS = ["song_name", "region", "ethnic_group", "song_type", "origin_period",
        "earliest_attestation_year", "attestation_source", "composer_or_adapter",
        "composition_or_adaptation_year", "evidence_urls", "confidence", "notes"]

# Genre-level context appended to default rows (never used as a song date).
GENRE_CONTEXT = {
    "侗族大歌": ("Genre context: 侗族大歌 UNESCO 2009; Ming 邝露《赤雅》 describes Dong singing.",
               "https://www.ihchina.cn/project_details/20091.html"),
    "飞歌": ("Genre context: 苗族飞歌 (雷山) national ICH 2008.",
             "https://www.guizhou.gov.cn/ztzl/wzgz/yzgz_5967100/mlfy/202410/t20241015_85942293.html"),
    "长调": ("Genre context: Mongolian long song UNESCO 2005; 13th-c. literary references are genre-level.",
             "https://www.ihchina.cn/project_details/12410/"),
    "堆谐": ("Genre context: 堆谐 Sakya-period origin is legend; 拉孜堆谐 national ICH 2008.",
             "https://wlt.xizang.gov.cn/xccx/lytg/201912/t20191211_125891.html"),
    "囊玛": ("Genre context: 囊玛, Lhasa court/indoor song-dance.",
             "http://paper.people.com.cn/rmrbhwb/html/2016-11/05/content_1724472.htm"),
}
KEYMAP = {"t": "song_type", "op": "origin_period", "ey": "earliest_attestation_year",
          "src": "attestation_source", "ca": "composer_or_adapter",
          "cy": "composition_or_adaptation_year", "urls": "evidence_urls",
          "c": "confidence", "n": "notes"}


def default_row(g: pd.DataFrame) -> dict:
    note = "No song-specific dating found; classed traditional from source labelling"
    note += " (Rhymoi 中国音乐地图 tradition-bearer recording)." if g.note.astype(str).str.contains("Rhymoi").any() else "."
    url = g.url.iloc[0]
    for key, (ctx, curl) in GENRE_CONTEXT.items():
        if key in str(g.genre.iloc[0]):
            note += " " + ctx
            url = f"{curl}; {url}"
    return dict(song_type="traditional", origin_period="NA", earliest_attestation_year="NA",
                attestation_source="NA", composer_or_adapter="NA",
                composition_or_adaptation_year="NA", evidence_urls=url,
                confidence="low", notes=note)


def main():
    idx = pd.read_csv(ROOT / "data/regions_transcription/dataset_index.csv")
    research = json.loads((Path(__file__).parent / "research.json").read_text())
    out_dir = ROOT / "data/regions_curated/song_dates"
    out_dir.mkdir(parents=True, exist_ok=True)
    for region in REGIONS:
        rows = []
        for song, g in idx[idx.region == region].groupby("song_name", sort=False):
            rec = research.get(song)
            row = {KEYMAP[k]: v for k, v in rec.items()} if rec else default_row(g)
            row.update(song_name=song, region=region,
                       ethnic_group=g.ethnic_group.dropna().iloc[0] if g.ethnic_group.notna().any() else "NA")
            rows.append(row)
        df = pd.DataFrame(rows)[COLS].fillna("NA").replace("", "NA")
        df.to_csv(out_dir / f"{region}.csv", index=False)
        print(region, len(df), df.song_type.value_counts().to_dict(),
              f"attested={(df.earliest_attestation_year != 'NA').mean():.0%}")


if __name__ == "__main__":
    main()
