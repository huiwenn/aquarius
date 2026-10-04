# Curation & search

How to go from a taxonomy (regions, genres, ethnic groups) to a ranked, verified list of single-video
candidates, without fabricated links, with provenance.

## Contents
1. Why search-only
2. Taxonomy files
3. The search helper
4. Agent-driven curation: prompt template
5. Ranking and inclusion rules
6. Diversity caps and region assignment
7. What happened in the worked example (numbers, best sources, thin regions)
8. Provenance and reproducibility

---

## 1. Why search-only

The first link list was written up front: ~30 YouTube links per region, 453 in total. At download time:

| Outcome | Count |
|---|---|
| Dead ("Video unavailable", "not available", private, members-only) | ~86 |
| Playlist/channel URLs pulling whole collections | 8 |
| Bot-walled before they could be checked | 190 |

The re-curation later showed that **none of the 60 湘/赣 IDs, and none of the undownloaded 闽台 IDs, appeared in
any live search result.** They were almost certainly fabricated.

The lesson: an ID is only trustworthy if it came from a live search result in this session, and the query is logged.

## 2. Taxonomy files

One JSON per class, e.g. `data/regions/<region>.json`, with:
- `region_name`, `region_name_en`, `type` (han / minority)
- `geography` (provinces, description)
- `history_and_culture`
- `music_characteristics`
- `representative_songs`

The representative songs and genre vocabulary are the raw material for search queries. Invest in these
descriptions: the agents' query quality comes straight from them.

## 3. The search helper

`src/secaiqu/search_candidates.py`:
- Uses yt-dlp's flat `ytsearchN:<query>` extractor. It returns real, currently listed IDs with title,
  channel, duration and view count, and **it keeps working even while video extraction is bot-walled**.
- Appends `{time, region, query, hits}` to `data/regions_curated/search_log.jsonl`. The log is shared
  across agents and append-only.
- Prints `video_id<TAB>duration_s<TAB>channel<TAB>title` for the agent to read, and sleeps 2 s between queries.

```bash
python src/secaiqu/search_candidates.py --region 西北部高原 -n 15 "陕北民歌 信天游 原生态" "山西民歌 左权开花调"
```

The worked example ran ~110 queries per 5-region agent. Batch several queries per call.

## 4. Agent-driven curation: prompt template

Dispatch one agent per 3–5 classes, in parallel. The prompt that worked contained:
- **Role & scope:** "You are curating YouTube recordings for a research dataset of <genre> grouped by <taxonomy>.
  YOUR REGIONS: …"
- **Background:** the original links may be fabricated or dead; video extraction is walled; SEARCH works; do NOT
  download.
- **Tool usage:** the search helper; mostly native-language queries built from representative songs, genre terms,
  provinces and quality words (原生态 / 民歌 / 传统); batch queries.
- **Inputs:** already-downloaded audio with `.info.json`. Tell the agent to check these carefully, because
  playlist pulls contain junk.
- **Goal:** exactly 40 ranked candidates per class (never fewer than 32).
- **Rules:** see §5–6, plus class-specific exclusions (e.g. for minority regions: modern Tibetan/Mongolian/Uyghur
  pop, composed songs such as 天路 and 青藏高原).
- **Output schema:** one JSON per class (see SKILL.md phase 1).
- **Report:** per-class counts, distinct songs, already-downloaded count, where it struggled.

Tell agents to **save their builder scripts in the repo** (e.g. `src/secaiqu/curation/`). In the worked example two
agents shared a scratchpad `build.py` and overwrote each other. One region set's builder was lost, so for those
regions the per-candidate `source_query` and `note` fields are the only provenance.

## 5. Ranking and inclusion rules

Rank order:
1. **Field or tradition-bearer recordings (原生态).** Highest documentary value, and usually shorter and cleaner
   single songs.
2. Well-known conservatory 民族唱法 performances of real folk songs.
3. Traditional instrumental tunes of the region, only if vocal material runs out. Mark them `instrumental`. They
   will need an instrument transcriber later.

Exclude:
- pop/rock/EDM/DJ remixes, 广场舞 versions, karaoke/伴奏-only tracks, tutorials, lessons, interviews, news clips
- shorts (<60 s)
- compilations, medleys and full concerts (>12 min); for 木卡姆, allow a single movement ≤12 min
- newly composed songs in folk style (天路, 青藏高原, 太湖美, 乌苏里船歌, 谁不说俺家乡好, 采茶舞曲,
  月光下的凤尾竹, 卓玛, 小背篓, 客家本色 …)
- opera and drama arias (粤剧, 花鼓戏, 采茶戏, 黄梅戏 films), unless needed to reach the count; then label the genre
- songs clearly belonging to another class

Allowed exceptions: canonical "representative songs" that are composed or opera-derived (浏阳河, 十送红军,
望春风, 雨夜花, 洪湖水浪打浪). Keep them, flagged in `genre`/`note`, ranked low.

## 6. Diversity caps and region assignment

- At most 3 recordings of the same song per class, and ideally ≥20 distinct songs.
- Cover sub-areas and ethnic groups within the class, not just the most famous songs.
- Assign a song that straddles classes by the specific variant's origin:
  - 拔根芦柴花, 杨柳青 and 扬州 茉莉花 → 江淮
  - 江苏茉莉花 → 江浙
  - 浏阳 Hakka songs → 客家, not 湘
  - 康定情歌 → Han 西南高原, not 藏族
  - the 川江号子 by a northern singer → 西南
- Flag cross-border material (e.g. Mongolian long songs recorded in Mongolia).

## 7. The worked example

Final curation: 15 regions × 40 candidates. Distinct songs per region ranged from 25 (东北部平原) to 40
(西南多民族, 藏族).

**Best sources:**
- **中国音乐地图 / Musical Map of China (Rhymoi / 瑞鸣音乐):** short (1–5 min), single-song recordings of local
  tradition-bearers for almost every region and ethnic group (苗, 侗, 彝, 哈尼, 壮, 傈僳, 纳西, 佤, 白, central
  Tibet/Amdo, Uyghur, Kazakh, Tajik, Mongolian long and short songs, 客家, Fujian 号子/南音). The single most
  valuable channel.
- **dbadagna:** field recordings (荣成渔民号子, 聊斋俚曲, 凤阳花鼓, 芦墟山歌, 宁波小调, 海州五大宫调, 榆林小曲,
  啰啰咚, 利川小曲 …).
- **CCTV 民歌大会 / 原声天籁 / 民歌中国:** tradition-bearers and stage singers; clean audio, sometimes an orchestra.
- **Individual tradition-bearers:** 陈达 and 朱丁顺 (恒春民谣), 王瑞如 (邵伯秧号子), 朱仲禄 (花儿), 古堂財 (美濃山歌),
  许娸雯's 沔阳 singers, 客网's elderly 兴宁 singers, 黄玉英 (赣南民歌 album).

**Thin regions and how they were filled:**
- **江淮:** Rhymoi + dbadagna + 扬剧小调 and 门歌. Several narrative-singing items (太和清音, 淮北大鼓) ranked low.
  Searches for 慢赶牛, 淮河号子 and 茅山号子 returned nothing usable.
- **粤:** results were flooded by 广东音乐 instrumentals, 粤语 pop and 粤剧. Filled with 咸水歌/疍家, 儋州调声,
  崖州/海南 songs, 台山卖鸡调, 木鱼歌 and 汕尾渔歌. Some unlabelled 咸水歌 tracks are named "咸水歌（中山，曲目未标）".
- **赣:** relies heavily on one singer's album. Few true 原生态 recordings (5 of 40 in the final index).
- **西南高原:** few Han field recordings online. Mostly 民族唱法 plus historical 黄虹/蔡绍序 recordings.
- **藏族:** of 92 playlist-pulled files, 1 was kept. Rhymoi Tibetan recordings filled the rest.

## 8. Provenance and reproducibility

Keep:
- `search_log.jsonl`: every query and every hit
- `source_query` and `note` on each candidate
- the builder scripts
- `.info.json` per download: uploader, channel_id, upload_date, license, duration

These are what let a paper describe exactly how the corpus was assembled, and let someone rebuild it from URLs
when the audio itself can't be redistributed.
