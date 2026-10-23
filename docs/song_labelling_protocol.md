# Song labelling protocol: composer, period of composition, song class, genre

Started 2026-10-08 (author request). This document records how each song in the Colour Regions corpus (rounds 1–3) gets labelled, and how the labels are cross-validated. Research agents follow it.

## Unit and inputs

- **Unit:** a song = (colour region, `song_key`). Recordings of one song share its labels. Songs with a generic title (`generic_title = True`, e.g. "信天游", "山歌") are labelled for genre and class only; composer and date stay empty unless a source identifies the specific song.
- **Input:** `data/colour_regions/song_labels/input_<Region>.csv` (built by `src/colour_regions/song_table.py`). Each row carries:
  - the curator metadata, two example video titles and places;
  - `rhymoi_composer` / `rhymoi_form`: composer or lyricist lines and the form printed in Musical Map of China descriptions;
  - `anthology_matches`: Anthology of Chinese Folk Songs (《中国民间歌曲集成》, 11 volumes) scores with the same normalised title, as `volume#number:inferred_section`;
  - `prior_*`: the round-1 dating (2026-09) where it exists. It is **withheld** for a random 25% of round-1 songs (`blind = True`), so the new labels can be compared with the old ones.

## Output (one file per region)

`data/colour_regions/song_labels/labels_<Region>.csv`, one row per input row, with these columns:

| Column | Values |
|---|---|
| `song_id`, `song_key`, `region`, `song_name` | copied from the input |
| `song_class` | `folk_traditional` (anonymous tradition) · `folk_adapted` (traditional tune with new lyrics or a named arrangement that changed the melody) · `folk_style_composed` (new song in a folk idiom, named author) · `composed` (new song, not folk idiom) · `court` · `religious` · `narrative_quyi` (曲艺/说唱) · `opera` · `instrumental` · `unknown` |
| `genre` | `work_song` 号子 · `mountain_song` 山歌 (信天游, 花儿, 爬山调, 飞歌 …) · `field_song` 田歌/秧田歌 · `ditty` 小调 · `song_and_dance` 灯歌/歌舞曲 (花灯, 采茶, 秧歌, 锅庄, 弦子, 堆谐 …) · `ritual_custom` 风俗/仪式歌 (婚嫁, 哭嫁, 酒歌, 祭祀) · `narrative` 叙事歌 · `children` 儿歌/摇篮曲 · `long_song` 长调 · `short_song` 短调 · `multipart` 多声部 (侗族大歌 …) · `religious` · `other` |
| `genre_native` | the Chinese genre term as attested (e.g. 信天游, 花儿·河州令, 哭嫁歌, 长调) |
| `composer`, `lyricist`, `arranger` | names exactly as a source gives them; empty if none. Never "traditional" here — use `song_class` for that |
| `composition_period` | `traditional_undated` · `ming` · `qing` · `republic` (1912–1949) · `prc_1949_1965` · `prc_1966_1976` · `prc_1977_1999` · `after_2000` · `unknown` |
| `year_best`, `year_kind` | a year and what it dates: `composition` · `adaptation` · `first_publication` · `first_recording` · `collection` (fieldwork collection) · `earliest_attestation` |
| `region_check` | `agree` · `disagree:<region>` (the song is from another colour region; cite a source) · `unsure` |
| `evidence` | one or two sentences: what the sources say |
| `sources` | `|`-separated: URLs, `anthology:<volume>#<number>`, `rhymoi_description`, `prior_dating`, or `knowledge` (no source checked) |
| `confidence` | `high` (≥ 2 independent sources agree, or one authoritative source) · `medium` (one reasonable source, or well-known fact) · `low` (inference from genre, title or knowledge only) |
| `searched` | `True` if a web search was made for this song |

## Rules

1. **Never invent a name or a year.** A composer, lyricist, arranger or year must come from a source you read in this task, from the Musical Map of China description, or from the prior dating with its URL. Knowledge alone may set `song_class`, `genre` and `composition_period` at `low` (or `medium` for very well-known facts, e.g. 《浏阳河》 composed 1951 by 唐璧光), and must say `knowledge` in `sources`.
2. **Folk songs have no composer.** A traditional song collected by someone keeps `composer` empty; the collector goes in `evidence`, and the collection year in `year_best` with `year_kind = collection`. A song "整理" or "改编" by a named person is `folk_adapted`, with that person as `arranger` (or `lyricist` for new words).
3. **Composer lines in the Musical Map of China description** (`rhymoi_composer`) are evidence of a named author. Check them: some name the composer of a well-known modern song; others credit an arranger of a traditional tune.
4. **Anthology evidence.** A title match in the same province is evidence that the song was collected as a folk song (the volumes were compiled 1979–2000s). A match in another province is weak evidence (titles recur). The inferred section is a weak genre hint (it comes from title words and volume order).
5. **Searching.** Search in Chinese first (`"<song title>" 民歌 作曲` / `"<title>" 由来` / `"<title>" 创作`), then English. Prefer: 中国民间歌曲集成 entries, ihchina.cn, government culture sites, encyclopaedias (百度百科 / 维基百科), academic articles, record labels. Spend the search budget where it changes a label: songs that may be composed or adapted, famous titles with a documented history, and `curator_dating_flag = check` items. Do not search every generic-title song.
6. **Region check.** Flag `disagree` only with a source (e.g. the song is a 陕北民歌 recorded in another region).
7. **Write as you go.** Append rows to the output file every ~20 songs, so that work survives an interruption. At the end, every input row has an output row.
8. Do not use any browser session or cookies, and do not try paywalled databases (CNKI).

## Cross-validation (after labelling; `src/colour_regions/song_labels_check.py`)

- **Blind round-1 subset:** agreement of `song_class` (traditional vs adapted vs composed) and of composer names with the withheld round-1 dating.
- **Anthology:** share of songs labelled `folk_traditional`/`folk_adapted` among songs with a same-province Anthology match; agreement of `genre` with the inferred Anthology section.
- **Musical Map of China descriptions:** every item whose description names a composer must not be labelled `folk_traditional` without an explanation.
- **Curator flags:** items the curators marked `composed` must not be labelled `folk_traditional` without an explanation.
- Disagreements are listed for review in `data/colour_regions/song_labels/review.csv`.

## Run 1 results (2026-10-08)

- **Agents:** five research agents (Sonnet), each covering 3–4 regions, each run in two passes.
  - The second pass was cut short: the session's web-search quota (200 searches) ran out after about 125 agent searches (14 + 24 + 22 + 37 + 28), so it fell back to direct page fetches (zh.wikipedia, ihchina, news sites).
  - Baidu Baike returns 403 to fetches.
- **Coverage:** 1,469 songs; every recording in rounds 1–3 carries labels. 142 songs had a web search.
- **Confidence:** 46 high, 121 medium, 1,302 low. Most low rows are anonymous traditional songs whose class rests on the curator flag, the genre and the title.
- **Classes:** `folk_traditional` 1,283, `folk_adapted` 63, `narrative_quyi` 40, `unknown` 39, `folk_style_composed` 22, `religious` 11, `court` 7, `composed` 2, `opera` 1, `instrumental` 1.
- **Cross-validation:**
  - Blind round-1 subset: class agreement 0.94 (100 songs); named-author agreement 9/10.
  - Anthology same-province matches: 0.90 labelled folk (40 songs).
  - Genre vs the inferred Anthology section: 0.71 (113 songs; weak check).
  - Description composer lines: no conflicts.
  - Curator "composed" flags labelled `folk_traditional`: 3 (月光光, 落雨大, 送郎), all adjudicated.
- **Review:** 13 rows, all adjudicated in `song_labels/adjudication.csv`. One override: 凤阳花鼓 → `folk_traditional`.
- **Region:** 9 兴国山歌 / 苏区 songs are labelled `disagree:Hakka` (Xingguo is a Hakka county). They stay in Gan pending an author decision. 29 are `unsure`.
- **Open:**
  - Raise the low-confidence share with a further search budget. The priorities are the 39 `unknown` songs, the 囊玛 court question, 弦子/锅庄 authorship and collection years from 集成/非遗 pages.
  - Decide whether core should exclude the 7 core recordings labelled `folk_style_composed` (6 at medium or high: 三十里铺, 摇篮曲 ×2, 嘱姑九点半, 细妹恁靓, 革东飞歌).

## Independent verification (2026-10-10)

- **What was checked:** an independent agent checked all 1,469 rows mechanically, all 167 high- or medium-confidence rows against their cited pages (20 page fetches), and every row's region. It also spot-checked 40 random low-confidence folk rows. Output: `song_labels/verification.csv` (192 findings).
- **Result:** no hard factual error; 1 mechanical error; 10 likely errors; the rest minor or notes.
- **Corrections:** all accepted, as field-level overrides in `adjudication.csv` (29 field changes). The main ones:
  - 洪湖水浪打浪 → 词曲 张敬安、欧阳谦叔;
  - 刘海砍樵 → `opera` (花鼓戏 excerpt);
  - 赶马调: 黄虹 was the singer, so no arranger;
  - 鸡公仔: no composer;
  - 一只鸟仔哮啾啾: the 1943 吕泉生 arrangement moved to evidence;
  - 金珠尔玛 → `narrative`;
  - several confidences lowered where the credit had a single unconfirmed source.
- **Rules fixed by this review:**
  - A theatre excerpt is `opera`; a song composed for an opera keeps its song class.
  - A collection year does not set the period of a traditional song (`traditional_undated`).
  - An adapted song with no adaptation date has period `unknown`.
- **Region placements documented in `regions.py`:** southern Anhui → Jiangsu–Zhejiang Plain; Chaoshan → Min–Tai; Hakka enclaves (Liuyang, Taiwan) → Hakka.
- **Known issue:** 沂蒙山小调, 康定情歌, 五指山歌 and 请茶歌 have per-recording `#` keys (the generic-title rule reads "place + 小调/山歌/歌" as a genre). Their labels are identical across rows. Merging the keys needs a key-alias map, so that the song ids stay stable.
- **Not verifiable without search:** Baike-only claims (鸿雁, 玛依拉, 蓝色的阔克河, 槐花几时开, 回娘家), 对鸟, and the years of 幸福歌 and 苏州好风光.

## Rules added 2026-10-14

- **秧歌 vs 插秧歌:** 秧歌 (the northern yangge song-and-dance form, incl. 秧歌调) is `song_and_dance`. Songs sung while transplanting or weeding rice (插秧歌, 栽秧歌, 薅秧歌, 秧田歌, 秧号子) are `field_song` (秧号子 may be `work_song` when it is a call-and-response labour chant).
- **二人转:** 小帽 (short songs) are `ditty`; 正戏 (staged plays) are `opera`.
- **Genre `religious` implies song class `religious`.**
- **`song_label_check` values:**
  - `verified`: checked against a source by an independent reviewer;
  - `reviewed`: a second reviewer found the label consistent with all the evidence, but read no source;
  - `corrected`: changed after review;
  - `disputed`: a reviewer raised an issue that needs the author's decision (listed in `song_labels/disputed.csv`);
  - `unchecked`.

## Second review of all unchecked labels (2026-10-14)

- **Scope:** four agents reviewed all 1,298 unchecked songs, writing `song_labels/review2_*.csv`.
  - Web search mostly returned nothing (about 40 searches, a few fetches), so 1,203 songs were confirmed for consistency only and 1 against a source.
  - 100 issues were raised.
- **Adjudication** (`adjudication.csv`, reasons start "Review2 2026-10-14"):
  - 51 field overrides on 44 songs: protocol rules, wrong place in `genre_native`, 南音/榆林小曲/胡琴书 → `narrative_quyi`, credits from an example title (望郎归), unsourced years removed, Gannan Hakka-titled songs → `region_check disagree:Hakka`;
  - 20 low-confidence proposals kept unchanged;
  - 34 questions for the author in `disputed.csv`: stage-series titles that sound modern, 番薯情, 一根竹竿容易弯, 阿克班玛, Mongolian-state songs, the 咸水歌 genre rule, Haixi Mongol 花儿 vs 长调, red-era texts.
- **Result (songs):** reviewed 1,221, verified 154, corrected 60, disputed 34, unchecked 0.

## Author review (2026-10-23)

- **Disputed songs:** the author listened to all 34 on the review page (https://claude.ai/artifact/LQgfcNr9y8sdnYY4huHzgL).
  - 31 labels kept, now `verified`;
  - 乌布西奔妈妈 → `folk_traditional`;
  - 阿克班玛: authors unknown, composer and lyricist cleared;
  - 哭嫁 (GAN-1356) moved to Hakka (`region_overrides.csv`).
  - Recorded in `adjudication.csv` with reasons starting "Author 2026-10-23".
- **Curation spot check** (60 random recordings, 4 per region):
  - region 60/60 (95% CI 94–100%);
  - tier 59/60 (91–100%);
  - traditional 60/60;
  - song labels 60/60.
  - The one tier correction is a CCTV broadcast, tier C → B (`data/regions_curated/tier_overrides.csv`).
  - Answers: `data/annotation/spotcheck_results_2026-10-23.csv`.
- **`song_label_check = verified`** now also covers labels the author kept after listening.
