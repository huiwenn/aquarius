# Collection v2 strategy

Started 2026-10-01. This responds to `docs/critiques.md`. v1 is documented in `docs/transcription.md` §1 and covers 600 YouTube recordings, 40 per 色彩区.

## Goals

v2 adds about 40 recordings per 色彩区, collected under rules that fix v1's weaknesses:

| v1 weakness (critiques.md) | v2 rule |
|---|---|
| One channel supplies 50–83% of minority-region recordings (Rhymoi "Musical Map of China") | **Channel cap:** ≤ 4 recordings per channel per region (10%), and ≥ 10 distinct channels per region |
| Channel leakage between train and test | **No channel used in v1.** v2 is collected from new channels only and serves as a **frozen external test set** (see "Freezing" below) |
| Region labels inferred from the title | **Provenance tiers** recorded per item. At least 50% of items per region must be tier A or B |
| Modern compositions mixed in among "民歌" | **Exclude composed songs** that have a known composer, or are dated after 1949 as compositions (`data/regions_curated/song_dates/all_songs.csv`, song_type ≠ traditional*). New songs are researched by the curator (see "Item rules") |
| Small, YouTube-only, convenience sample | **Second platform:** Bilibili, which is far larger for Chinese folk music. Plus archives (Europeana/CREM) where available |
| 民族唱法 conservatory singers ≠ regional practice | **Performance mix:** ≥ 70% 原生态 / field / local tradition-bearer; ≤ 30% 民族唱法; no choirs, pop or EDM arrangements |
| Same songs everywhere (茉莉花 ×N) | **Repertoire diversity:** ≥ 50% of song titles per region not in v1; at most 2 recordings of any one song per region |

### Provenance tiers
- **A — attested singer.** A named singer whose locality is independently known: a 非遗代表性传承人 (national or provincial list) of a 民歌 project, or a named local singer whose county/village is stated, e.g. "王向荣 (府谷)", "桑植民歌传承人 尚生武". Record the singer and their 非遗 project if any.
- **B — field/locality-attested recording.** A field or village recording with an explicit place (county or township) and occasion, e.g. 采风, 田野录音, 非遗展演 by a county 文化馆, or local TV from that county. The singer may be unnamed.
- **C — title/genre only.** The region is inferred only from the song title or genre ("陕北民歌《赶牲灵》" sung by an unknown person). Allowed, but at most 50% of a region's items.

### Item rules (curation)
- **Duration:** 40 s to 10 min. One song per video: no compilations or 精选集. A multi-song medley is allowed only if a single song dominates and that is noted.
- **Content:** solo or lead voice clearly audible. Light accompaniment is fine, since the pipeline separates vocals. Instrumental-only items are allowed only for genres that are inherently instrumental, and no more than 3 per region.
- **Location:** the singing must be within the region's area (see `src/secaiqu/mapping.py` and the v1 region JSONs). For border areas, label by the singer's locality, not the song's nominal origin.
- **Composed songs:** exclude songs with an attributed composer (e.g. 《山丹丹开花红艳艳》 is a 1971 adaptation; 《浏阳河》 is composed). When unsure, keep the item and set `dating_flag: "check"`.
- **IDs:** take every ID from an actual search result (`src/secaiqu/v2/search.py` logs every query). Never use an ID from memory.

### Freezing
The v2 set is an **external test set**:
- Nobody tunes on it.
- The first evaluation runs models trained on v1 (+ scores) exactly as specified in `region_classification.md` §22.
- That number is reported once, before any v2-informed change.

Later the set can be split in two:
- recordings from v2 channels with ≥ 3 items go to an extension training set;
- the rest stay as test.

## Sources and tools
- `src/secaiqu/v2/search.py --platform bili|yt` searches and logs to `data/regions_v2/logs/search_*.jsonl`. Hits are flagged `v1_channel` / `v1_video`.
  - Bilibili search uses the web API with homepage cookies, which works without login.
  - yt-dlp's `bilisearch` returns HTTP 412, so it is not used.
  - Bilibili download works with yt-dlp (`-f ba`, m4a).
- YouTube: as in v1. Downloads are throttled, Firefox cookies are required, and the bot wall appears after about 85 fast downloads.
- Archives: Europeana API (`wskey=api2demo`), which includes CREM ethnomusicology field recordings (Miao, Tibetan, Kyrgyz…), mostly In Copyright, so research use only.
- 非遗 lists (ihchina.cn) supply inheritor names to search for. Names and localities must be cited by URL.

## Pipeline
1. **Curate:** one subagent per region group writes `data/regions_v2/candidates/<region>.json` (schema below). Target 45–50 candidates per region, so ≥ 40 survive download.
2. **Download:** `src/secaiqu/v2/download.py` saves audio to `data/regions_v2/audio/<region>/<id>.<ext>` and writes `manifest.csv`.
   - Bilibili items are paced 8–20 s apart.
   - YouTube items are paced as in v1.
3. **Audit:** `src/secaiqu/v2/audit.py` checks the rules above (channel cap, tiers, v1 overlap, duration, composed flags) and prints a per-region report.
4. **Transcribe:** the same pipeline as v1 (`src/transcription/run_all.sh`, GAME ens3 + pp) → `data/regions_v2/transcription/`.
5. **Evaluate once:** v1-trained models are applied to v2 (frozen external test).

## Candidate schema (`data/regions_v2/candidates/<region>.json`)
```json
{"region": "湘", "curated_on": "2026-10-01", "curator": "agent-3",
 "candidates": [{
   "platform": "bili", "id": "BV1…", "url": "https://www.bilibili.com/video/BV1…",
   "title": "…", "channel": "…", "channel_id": 123, "duration_s": 187,
   "song_name": "嘀格调", "province": "湖南", "county_or_area": "桑植", "ethnic_group": "白族",
   "genre": "山歌", "performance_type": "原生态|field|民族唱法|instrumental|other",
   "singer": "尚生武", "singer_inheritor": "国家级: 桑植民歌 (2007)",
   "provenance_tier": "A|B|C", "provenance_evidence": "URL or text explaining the locality claim",
   "song_in_v1": false, "dating_flag": "traditional|check|composed",
   "source_query": "…", "note": "…"}]}
```

## Log
- 2026-10-01 — Probes:
  - Bilibili search API and download work.
  - Europeana has CREM minority field recordings.
  - The MGD page has no audio, only per-province title spreadsheets.
  - Internet Archive is mostly noise.
  - ihchina.cn is slow and needs a browser user agent.
  - See `critiques.md` §3.
- 2026-10-01: curation round 1 used five subagents, one per three-region group.
  - The first launch hit the usage limit after about 600 logged searches. The agents were resumed and finished their lists from the logged hits.
  - Coordinator changes:
    - Dropped the 3 武宁畲族 items from 赣. That community was resettled from 浙江建德 in the 1960s–70s, so the 赣 label would be wrong.
    - `audit.py` now counts channels by platform channel ID, because several deleted Bilibili accounts all display as "账号已注销".
    - `audit.py` treats Bilibili re-uploads of v1's Rhymoi label (瑞鸣中国音乐地图) as v1 channels.
  - **Audited candidate pool: 667 items** in `data/regions_v2/candidates_clean/` (counted below). After audit there are 0 hard-rule violations: no v1 channel or video, all durations 40–600 s, no composed songs, ≤4 per channel, ≤2 per song.

| region | n | channels | tier A+B % | 原生态/field % | new songs % | platform (bili/yt/eur) |
|---|---|---|---|---|---|---|
| 东北部平原 | 45 | 28 | 40 | 87 | 93 | 39/6/0 |
| 北方草原文化民歌区 | 46 | 32 | 50 | 93 | 85 | 40/2/4 |
| 客家特区 | 48 | 38 | 56 | 96 | 100 | 23/25/0 |
| 新疆民歌区 | 50 | 31 | 64 | 94 | 98 | 36/10/4 |
| 江汉 | 42 | 31 | 43 | 83 | 95 | 40/2/0 |
| 江浙平原 | 45 | 27 | 40 | 80 | 89 | 45/0/0 |
| 江淮 | 36 | 21 | 39 | 81 | 86 | 36/0/0 |
| 湘 | 42 | 34 | 50 | 88 | 90 | 42/0/0 |
| 粤 | 46 | 37 | 54 | 96 | 98 | 32/14/0 |
| 藏族民歌区 | 49 | 31 | 55 | 100 | 100 | 39/10/0 |
| 西北部高原 | 50 | 38 | 50 | 100 | 88 | 47/3/0 |
| 西南多民族古老原始文化民歌区 | 50 | 39 | 60 | 100 | 94 | 50/0/0 |
| 西南高原 | 47 | 39 | 57 | 96 | 98 | 45/2/0 |
| 赣 | 25 | 18 | 56 | 72 | 64 | 22/3/0 |
| 闽台 | 46 | 34 | 70 | 100 | 100 | 9/37/0 |

  - **Comparison with v1:** v1 had 8–28 channels per region, and in four regions one channel supplied 50–83% of recordings. v2 has 18–39 channels per region, with at most 4 items (≤ 11%) from any one channel.
  - **Soft rules not met:**
    - Tier A+B is below 50% in 东北部平原, 江浙平原, 江淮 and 江汉 (39–43%). Bilibili titles rarely name the singer's county, and the archival uploaders that do are capped at 4. C items are kept, and results will be reported for both the A+B subset and all items.
    - Counts are thin for 赣 (25: Jiangxi folk singing is scarce online; most hits were 采茶戏, red songs or 刀郎 concerts) and 江淮 (36). Both need a top-up round.
  - **Europeana/CREM items (8):** direct MP3 from archives.crem-cnrs.fr. György Kara's 1959 Hohhot recordings and Sabine Trebinjac's 1988 喀什/莎车 recordings. In Copyright, research use only.
  - **Follow-ups after download:** curators flagged items that may contain narration (非遗 promos, news clips, documentaries) in `note`. Screen them with the critic's stem-dominance / vocal-activity check before transcription.
  - Download started with `download.py` → `data/regions_v2/logs/download_2.log`.
- 2026-10-01 — **Curation round 2** for the thin regions, run by two subagents. The audited pool is now **698**. After audit there are still 0 hard-rule violations.

| region | round 1 | round 2 | total | channels | A+B % | 原生态/field % |
|---|---|---|---|---|---|---|
| 江淮 | 36 | +12 | 48 | 32 | 40 | 75 |
| 江汉 | 42 | +5 | 47 | 35 | 47 | 83 |
| 湘 | 42 | +6 | 48 | 40 | 52 | 88 |
| 赣 | 25 | +8 | 33 | 26 | 45 | 67 |

  - **赣 has hit the limit of platform search.**
    - About 43 county, genre and archive queries mostly returned noise.
    - The national 兴国山歌 / 九江山歌 inheritors (徐盛久, 王善良, 郭德京, 韦桂花) have no performance videos on Bilibili.
    - The archival uploaders who post songbook recordings for other provinces (雷雨wsl, 倒霉的K) have no Jiangxi material.
  - **The 4-per-channel cap is blocking good material.**
    - 赣鄱声像档案馆, the Jiangxi audiovisual archive, has at least 3 more field items held back by the cap (BV1g44y1c7DC 武宁民歌, BV1ZQ4y1H7rG 铜鼓客家山歌, BV16w411P7f5 萍乡《铜钱歌》).
    - In 江淮, A+B stays low because the archival uploaders (雷雨wsl, 思的虔诚, 三十一曲) are capped.
    - Open decision: allow up to 6 per channel for institutional archive channels.
  - **Inheritor checks:** ihchina lookups timed out in round 2, so the round-2 tier-A claims rest on the video title or description.
  - **Download:** round-2 items are queued in `logs/download_3.log`, which starts after `download_2` finishes.
- 2026-10-01/02 — **Download complete: 697 of 698** (2.4 GB) in `data/regions_v2/audio/`, manifest `data/regions_v2/manifest.csv`, audit `data/regions_v2/audit_downloaded.csv`.
  - Runs: run 2 got 659 of 667. Run 3 got all 31 round-2 items. Run 4 (`--retry-failed --player-client default`) recovered 7 of 8: all six YouTube 403s and one Bilibili read timeout.
  - Still missing: BV1hM4y1V7sd (西南高原), where the Bilibili stream was truncated 3 times.
  - No YouTube bot wall was hit in about 100 YouTube downloads interleaved with Bilibili.
  - Per region: 33 (赣) to 50 downloaded.
  - Next steps: speech screen → transcription (`AQ_MANIFEST` / `AQ_TRANS`, see `docs/worklog.md`) → one frozen external evaluation.
- 2026-10-02 — **Speech screen** (`src/secaiqu/v2/speech_screen.py`, AudioSet AST, 10 s windows of the full mix).
  - **Calibration on synthetic speech:** macOS TTS read a 45 s Mandarin news-style paragraph. Three voices produced audio: Tingting (zh_CN), Meijia (zh_TW) and Sinji (zh_HK, Cantonese). The other seven listed voices gave empty files.
    - Every window of the three real clips was labelled speech (13 windows). Speech share was 1.0.
  - **Round 1 vs round 2:** speech share ≥ 0.3 in 2% of round 1 and 15% of round 2 (119 recordings).
  - **False positives:** many high scores are unaccompanied traditional singing, for example the 93-year-old Hakka singer (BV1HL411w79X), 咸水歌, 褒歌, 童谣 and 号子. AudioSet "Singing" does not cover this repertoire well.
  - **Earlier attempt:** a pitch-plateau heuristic failed the same way, on recitative genres (太和清音, 木鱼歌).
  - **Decision (two-signal rule):** an item leaves the core subset only if speech share ≥ 0.3 AND its title or curator note marks it as documentary, news, interview or heritage film. 24 items meet both conditions.
    - The threshold and the rule were set after looking at the score distribution. They were not tuned against labelled data.
