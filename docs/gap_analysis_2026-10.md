# Gap analysis of the Colour Regions dataset (2026-10-18)

Reviewer-style analysis of the dataset as it is on 2026-10-18, for the TISMIR special collection "Open Music Data for Music Processing Research". Every number below was computed from the files named in each section. Nothing in the repo was changed except this new file.

**Sources read:** `README.md`, `CLAUDE.md`, `docs/worklog.md` (sessions 2026-10-02 to 2026-10-14), `docs/critiques.md`, `docs/song_labelling_protocol.md`, `docs/thesis_evidence_plan.md`, `metadata/README.md`, `docs/hf_dataset_card.md`, `src/colour_regions/regions.py`, the paper in `../color-regions-paper/sections/*.tex` and `generated/numbers.tex`.
**Data:** `data/colour_regions/recordings.csv` (1,655 rows, 63 columns), `metadata/recordings.csv` (50 columns), `metadata/song_labels.csv` (1,469 songs), `song_labels/disputed.csv` (34), `anthology_overlap.csv` (249 pairs), `data/transcription/audit/anthology_distance_summary.md`, `metadata/link_status.csv`, `fingerprints.csv`, `scores.csv` (10,830), `data/hf_release/data/recordings.parquet`, `data/contrast/candidates_clean/*.json`, `spotcheck_curation_sample.csv`, `data/annotation/free_rhythm_candidates.csv`. `check_release.py` prints OK.

---

## Summary: top 10 issues, ranked by severity

| # | Issue | Key number | Fix (effort) |
|---|---|---|---|
| 1 | **The paper describes a different dataset.** Text says two rounds; Round 3, song labels, subsets and the Anthology overlap are absent; hand-typed numbers are stale; a stray draft line is in §6. | "two rounds" in abstract, intro, §3, §4; channel share typed as 37%/33% (now 52.5%/64.3%); "h hioiii this paragraph…" in `06_description.tex` | Rewrite §4/§6/§7/§9 for 3 rounds; move every number to macros (2–3 days, writing) |
| 2 | **No human validation of any label yet.** The 60-item curation spot-check and the 150-note gold set are unrated; the free-rhythm coding is empty. All label QA is agent-on-agent. | spot-check CSV: 0/60 filled; free-rhythm: 0/112 coded; song labels: 1,221/1,469 (83%) "reviewed" with no source read | Do the 60-item check (1 day, human) and the gold set (½ day) |
| 3 | **One channel is a third of the corpus and most of the minority regions.** Musical Map of China (Rhymoi) = 539 recordings (32.6%); largest `group_id` = 648 (39%), holding 60.5% of all minority-region recordings. | Series share: SW Multi-ethnic 64.3%, NW Plateau 63.4%, Tibetan 52.5%, Steppe 50.8%, Xinjiang 45.7% | Report all results with/without series; add a series-free baseline table (1 day, data) |
| 4 | **Region labels are weakly attested.** 64.3% of recordings are tier C (title/genre only); 62.4% of core. A/B share ranges 22.7% (Northeast Plain) to 47.1% (Hakka). | 1,064 tier C; A1 only 34 (2.1%) | State tier-stratified numbers everywhere; push Round 3 A2 upgrades; finish the spot-check (see #2) |
| 5 | **Song labels mostly rest on no source.** 89.0% low confidence; 1,041/1,469 songs (70.9%) cite `knowledge` only; only 142 songs had a web search. | high 44, medium 117, low 1,308 | Present song labels as "provisional, agent-generated"; budget searches for the 177 famous/adapted titles (2–3 days, labelling) |
| 6 | **Release-file inconsistencies that a reviewer can find in minutes.** `core`≠`subset` for 24 rows; `metadata/README.md` says 1,297 recordings and rounds 1–2; `fold` is in git `metadata/` though the author decided not to release it; song_labels keeps 兴国山歌 in 赣 while 13 recordings moved to Hakka. | 24 speech-excluded rows have `subset=core`, `core=False` | Fix `build_release.py`/`export_metadata.py`; extend `check_release.py` (½ day, data) |
| 7 | **Recording condition is confounded with region via the series.** Series items have median vocal-to-accompaniment 34.0 dB vs 3.2 dB elsewhere, and 99% are labelled 原生态. | Round 3 median `vocal_db` 37.5 dB vs 3.2/5.1 dB in Rounds 1/2 | Add `recording_context` (studio series / broadcast / field / user) column; covariate-controlled baseline (1–2 days) |
| 8 | **Rights and privacy promises are not met by the build.** HF release ships MIDI/MusicXML/F0 for all 8 CREM items while the paper promises links only "until the archive gives permission". `singer_inheritor` exposes names (操明花, 艾赛提·莫合塔尔, 艾买提·苏批, 曹光裕) on A2 rows whose `singer` is withheld, and co-singers on A1 rows. | 8 CREM items × 6 derived files; 4 names on A2 rows | Drop CREM derived files or get permission; redact `singer_inheritor` (½ day, data) |
| 9 | **The score side does not match the audio side.** Scores cover 14 of 15 regions; Hakka has 0 scores; Tibetan 6, Xinjiang 22, SW Multi-ethnic 24 of 10,830. The Anthology overlap covers 98 recordings in 8 regions; 7 regions have none. | 3 regions hold 7,349 scores (68%) | Say so in the abstract and table; drop "scores mapped to the same regions" claims for minority regions (writing, ½ day) |
| 10 | **Genre and geography gaps against the musicology.** `other` genre = 52% of Yue and 45% of Xinjiang; `multipart` only in SW Multi-ethnic (29) and Xiang (2); 0 Taiwan Indigenous (高山) items though 58/91 Min–Tai items are from Taiwan; NW Plateau is 36% Gansu, 16% Shaanxi. | 161 `other` recordings | Resolve 咸水歌 and muqam genre rules (disputed YUE-0716); add a coverage-gap table to §9 (1 day) |

Also notable, but lower: 9 dead links after 2 weeks, all Round 3 and all core (§6); the contrast set re-uploads commercial pop (60/90 古风 titles are "Hi-Res/修复/MV" reposts) (§7); 90.6% of songs are singletons, so tune-family claims have little material (§3).

---

## Status of the earlier critiques (`docs/critiques.md` §4, dated 2026-10-02)

| Critique | Status on 2026-10-02 | Status now | Evidence |
|---|---|---|---|
| Small, convenience sample | Addressed; bias disclosed | **Partly fixed, partly worse.** Corpus grew to 1,655 (88.3 h), but Round 3 is one channel | 539/1,655 from one channel |
| Channel concentration | Residual 37%/33% reported | **Reopened, worse.** Author lifted the cap for the series (2026-10-04) | Series share per region up to 64.3% (SW Multi-ethnic); largest group 648 |
| Labels assigned, not observed | Partly; human check pending | **Still open.** Spot-check unrated (0/60) | `spotcheck_curation_sample.csv` empty |
| Taxonomy contested | Addressed | Addressed; province, county, ethnic group released | `geo_level` county for 730 (44%) |
| Modern compositions mixed in | Addressed | **Improved.** Song labels + `folk_style_composed` subset (31) | But 70.9% of song labels cite knowledge only |
| Pipeline-induced signal | Designed; pending | **Still open, and a new form:** studio series vs field audio differ by ~31 dB `vocal_db` | §5 |
| Researcher degrees of freedom / held-out set | Designed; pending | Partly done (Round 1 → Round 2 test reported). Round 3 not in any reported experiment | Paper §8 uses 1,184 core recordings |
| Small effects | Addressed in design | Unchanged | — |
| Score corpora confounded with collections | Disclosed | Unchanged; plus Hakka has 0 scores | §5 |
| Transductive tricks, toy resynthesis, homogenization | Removed | Removed | — |
| Transcription accuracy unmeasured | Pending human work | **Still open.** Anthology-distance check added (exploratory, 98 recordings) | `anthology_distance_summary.md` |
| Correlation stories | Designed | Unchanged (no results yet) | — |
| **New:** paper out of date with data | — | **New, severe** | §6 |
| **New:** release-file inconsistencies | — | **New** | §6 |
| **New:** contrast set rights | — | **New** | §7 |

---

## 1. Coverage and balance

### 1.1 Per region (all 1,655 recordings)

| Region | Type | n | core (`subset`) | hours | songs | channels | singer ids | no singer | top-channel share | series share | R1/R2/R3 | provinces |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Northwest Plateau | Han | 202 | 199 | 9.34 | 190 | 53 | 101 | 7.9% | 63.4% | 63.4% | 40/50/112 | 11 |
| Southwest Multi-ethnic | min. | 168 | 165 | 8.21 | 163 | 47 | 65 | 24.4% | 64.3% | 64.3% | 40/50/78 | 6 |
| Northern Steppe | min. | 132 | 123 | 7.29 | 116 | 48 | 58 | 18.2% | 50.8% | 50.8% | 40/46/46 | 9 |
| Xinjiang | min. | 129 | 118 | 7.88 | 123 | 47 | 51 | 33.3% | 45.7% | 45.7% | 40/50/39 | 1 |
| Tibetan | min. | 118 | 116 | 6.16 | 115 | 39 | 39 | 35.6% | 52.5% | 52.5% | 40/49/29 | 6 |
| Hakka | Han | 104 | 99 | 5.63 | 87 | 69 | 52 | 33.7% | 13.5% | 13.5% | 45/56/3 | 7 |
| Xiang | Han | 103 | 97 | 5.31 | 93 | 59 | 39 | 40.8% | 32.0% | 32.0% | 40/48/15 | 1 |
| Jiangsu–Zhejiang Plain | Han | 99 | 97 | 4.60 | 83 | 45 | 49 | 37.4% | 26.3% | 26.3% | 40/45/14 | 4 |
| Northeast Plain | Han | 97 | 88 | 5.55 | 80 | 56 | 59 | 26.8% | 12.4% | 12.4% | 40/45/12 | 9 |
| Jiang–Huai | Han | 93 | 88 | 5.56 | 73 | 47 | 43 | 30.1% | 19.4% | 19.4% | 40/48/5 | 2 |
| Min–Tai | Han | 91 | 84 | 5.24 | 75 | 58 | 31 | 49.5% | 12.1% | 12.1% | 40/46/5 | 3 |
| Jiang–Han | Han | 87 | 80 | 4.76 | 68 | 59 | 25 | 65.5% | 9.2% | 9.2% | 40/47/0 | 2 |
| Southwest Plateau | Han | 86 | 78 | 4.75 | 74 | 64 | 36 | 44.2% | 4.7% | 1.2% | 40/46/0 | 6 |
| Yue | Han | 86 | 78 | 4.98 | 78 | 65 | 30 | 65.1% | 7.0% | 0.0% | 40/46/0 | 5 |
| Gan | Han | 60 | 51 | 3.05 | 49 | 39 | 20 | 46.7% | 25.0% | 25.0% | 35/25/0 | 1 |
| **Total** | | **1,655** | **1,561** | **88.3** | **1,441 keys** | **681** | **680** | 33.7% | — | 32.6% | 600/697/358 | — |

Findings:
- **Imbalance is 3.4:1** (Northwest Plateau 202 vs Gan 60). Round 3 caused it: it added 112 to the Northwest Plateau and 0 to Gan, Jiang–Han, Southwest Plateau and Yue.
- **The top channel is the series in 13 of 15 regions.** Without the series, no region has a channel above 10%, except Gan (25%). So the Round 2 cap worked; Round 3 undid it.
- **Han vs minority:** 1,108 Han (58.8 h) vs 547 minority (29.5 h). The series supplies 54.1% of minority recordings but 21.9% of Han recordings.
- **Singers:** 558 recordings (33.7%) have no `singer_id`. In Jiang–Han and Yue, 65% have none. Singer-disjoint evaluation is therefore weak there.
- **Gan is thin and shrinking.** 60 recordings, 51 core, 20 singer ids. 13 recordings already moved to Hakka; 2 more Gan recordings carry `region_check = disagree:Hakka`.

### 1.2 Provinces vs the region definitions (`regions.py`)

| Region | Defined areas | Stated provinces (counts) | Gap |
|---|---|---|---|
| Northeast Plain | Shandong, Hebei, Tianjin, Beijing, Liaoning, Jilin, Heilongjiang | 山东 27, 东北 26, 河北 17, 吉林 7, 辽宁 7, 黑龙江 5, 天津 3, 北京 1, none 3 | 26 say only "东北"; Beijing 1 |
| Northwest Plateau | Shaanxi, Shanxi, Gansu, Ningxia, Qinghai (east) | 甘肃 73, 青海 36, 陕西 32, 宁夏 27, 山西 22 | Gansu/Qinghai 花儿 dominate; Shaanxi (信天游) only 16% |
| Jiang–Han | Hubei, southern Henan | 湖北 80, 河南 7 | Henan thin |
| Min–Tai | Fujian, Taiwan, Chaoshan | 台湾 58, 福建 29, 广东 4 | **Taiwan 64%**; Fujian 32%; 0 Indigenous (高山) items |
| Hakka | Guangdong, Fujian, Jiangxi Hakka; enclaves | 台湾 36, 广东 29, 江西 15, 福建 15, 湖南 5 | Taiwan 35% |
| Yue | Guangdong, Hainan, SE Guangxi | 广东 51, 海南 19, 香港 12, 广西 3, 澳门 1 | Guangxi thin |
| Southwest Plateau | Sichuan, Chongqing, Guizhou, Yunnan (Han) | 四川 28, 重庆 23, 云南 23, 贵州 10 | Guizhou thin |
| Northern Steppe | Inner Mongolia + northern minorities | 内蒙古 106, 黑龙江 8, … 蒙古国/蒙古 3 | 3 items from Mongolia (2 excluded, 1 core) |
| Tibetan | Tibet, Qinghai, W Sichuan, Gansu | 西藏 43, 四川 36, 青海 23, 甘肃 7, none 6 | Balanced |
| SW Multi-ethnic | Yunnan, Guizhou, Guangxi, W Hunan | 云南 70, 广西 48, 贵州 26, 四川 21, 湖南 1 | W Hunan (Miao/Tujia) only 1; those went to Xiang |

### 1.3 Geocoding

`geo_level`: county 730 (44.1%), prefecture 376 (22.7%), province 506 (30.6%), none 43 (2.6%). The worst regions: Min–Tai 14.3% at county level, Xinjiang 20.9%, Gan 23.3%, Northeast Plain 23.7% (and 29 of its 97 have no usable place, mostly "东北"). Any map or distance analysis in these regions rests on province centroids.

### 1.4 Rounds

| Round | n | hours | channels | tier C | Bilibili | 原生态 | 民族唱法 |
|---|---|---|---|---|---|---|---|
| 1 (YouTube) | 600 | 32.6 | 219 | 81.8% | 0% | 51.0% | 34.7% |
| 2 (Bili, capped) | 697 | 38.7 | 462 | 47.8% | 81.9% | 72.9% | 3.7% |
| 3 (series) | 358 | 17.1 | 1 | 67.0% | 0% | 100% | 0% |

181 Round 1 recordings are also series items, so the series total is 539.

---

## 2. Label validity

### 2.1 Provenance tiers per region

| Region | A1 | A2 | B | C | tier C share |
|---|---|---|---|---|---|
| Northeast Plain | 0 | 6 | 16 | 75 | 77.3% |
| Gan | 0 | 0 | 14 | 46 | 76.7% |
| Xinjiang | 1 | 7 | 24 | 97 | 75.2% |
| Northern Steppe | 5 | 19 | 12 | 96 | 72.7% |
| Jiang–Han | 1 | 3 | 21 | 62 | 71.3% |
| Southwest Plateau | 2 | 11 | 17 | 56 | 65.1% |
| Jiang–Huai | 3 | 19 | 12 | 59 | 63.4% |
| Tibetan | 5 | 17 | 23 | 73 | 61.9% |
| SW Multi-ethnic | 1 | 37 | 28 | 102 | 60.7% |
| Jiangsu–Zhejiang Plain | 4 | 22 | 13 | 60 | 60.6% |
| Northwest Plateau | 6 | 63 | 11 | 122 | 60.4% |
| Xiang | 2 | 21 | 19 | 61 | 59.2% |
| Yue | 0 | 13 | 23 | 50 | 58.1% |
| Min–Tai | 0 | 18 | 23 | 50 | 54.9% |
| Hakka | 4 | 23 | 22 | 55 | 52.9% |
| **All** | **34** | **279** | **278** | **1,064** | **64.3%** |

- The Round 2 target (≥ 50% A or B per region) is met by **no** region in the merged corpus. Best is Hakka at 47.1%.
- The paper (§6) types "24% (Northeast Plain) to 48% (Min–Tai)". The data now give 22.7% (Northeast Plain) to 47.1% (Hakka). This number is hand-typed and stale.
- 68.5% of series items are tier C: the descriptions give a province or prefecture only.
- Tier B has 0 series items and 252 of its 278 items from Round 2.

### 2.2 Song labels (`metadata/song_labels.csv`, 1,469 songs)

| Measure | Value |
|---|---|
| Confidence high / medium / low | 44 / 117 / 1,308 (**89.0% low**) |
| `song_label_check` reviewed / verified / corrected / disputed | 1,221 / 154 / 60 / 34 |
| Songs whose only source is `knowledge` | **1,041 (70.9%)** |
| Songs with any external source (URL, Anthology, series description, prior dating) | 428 (29.1%) |
| …with a URL | 167; Anthology 78; series description 135; prior dating 155 |
| Songs with a web search | 142 (9.7%) |
| `region_check` agree / unsure / disagree:Hakka | 1,429 / 29 / 11 |

At recording level: low confidence ranges from 67% (Gan) to 99% (Tibetan) and 96% (SW Multi-ethnic). Verified recordings: Tibetan 1, Hakka 6, SW Multi-ethnic 8. **The minority regions have the least-checked song labels.**

"Reviewed" means a second agent found the label consistent, but read no source (protocol, 2026-10-14). A reviewer will read 83% "reviewed" as agent consensus, not validation.

### 2.3 The 34 disputed songs (`disputed.csv`)

| Question type | Songs | Regions |
|---|---|---|
| Stage-series title "sounds modern", no source | 13 | SW Multi-ethnic 10, Tibetan 3 |
| Composed Mongolian state / homeland songs | 3 | Steppe |
| Haixi Mongol 花儿 vs 长调 genre rule | 3 | Steppe |
| 咸水歌 genre rule (≈ 45 rows `other`) | 1 rule | Yue |
| Red-era texts (门口挂盏灯, 湖塘塌塌岭) | 2 | Xiang, Gan |
| Single-source composer credits (阿克班玛, 一根竹竿容易弯, 番薯情, 船到码头把酒喝, 牧歌, 凌波情) | 6 | mixed |
| Other (class/region: 乌布西奔妈妈, 艺人翻身, 哭嫁 Hakka?, 清清剑河水 Jing vs Miao, 无据 folk_adapted, curator flag) | 6 | mixed |

35 recordings carry `disputed`. Two rules (咸水歌, 花儿 vs 长调) affect far more rows than their count: the 咸水歌 rule alone touches about 45 Yue recordings.

### 2.4 Song class and genre per region

`song_class` is `folk_traditional` for 85.1% of recordings. Non-traditional share is highest in Min–Tai (36%: 15 adapted, 14 narrative_quyi), Jiang–Huai (27%: 15 narrative_quyi) and Northeast Plain (23%). `unknown` class: Xinjiang 15, Steppe 9.

Genre (recordings):

| Region | dominant genre | `other` share | notes |
|---|---|---|---|
| Yue | other 45 | **52%** | 咸水歌/渔歌 unresolved |
| Xinjiang | ditty 59, other 58 | **45%** | muqam, dastan, Kazakh 阿依特斯 have no genre |
| Jiang–Huai | ditty 48 | 15% | |
| Min–Tai | ditty 41 | 7% | 0 field songs, 1 work song |
| NW Plateau | mountain_song 136 (67%) | 0% | |
| Hakka | mountain_song 78 (75%) | 1% | 0 work songs |
| Steppe | long_song 46, short_song 26 | 5% | long/short song used only here |
| Tibetan | song_and_dance 44 | 4% | 0 multipart |

`song_genre` total: ditty 484, mountain_song 465, **other 161**, song_and_dance 114, ritual_custom 93, work_song 74, narrative 64, long_song 46, children 45, field_song 40, multipart 31, short_song 26, religious 12.

### 2.5 Ethnic groups

49 distinct groups are named (incl. Han). 412 recordings (24.9%) have no ethnic group; in Northeast Plain 85%, Jiang–Huai 74%, Jiangsu–Zhejiang 74% are blank (presumably Han, but unstated). Absent: Korean (朝鲜, unmapped by design), Taiwan Indigenous (高山), Jingpo, Achang, De'ang, Derung, Maonan, Uzbek, Russian. Single-digit: Dai 1, Bouyei 2, Sui 2, Oroqen 2. A reviewer from ethnomusicology will note that the SW Multi-ethnic region (≥ 25 groups in Yunnan alone) has 24 groups over 168 recordings, most with fewer than 10 items.

---

## 3. Repertoire

| Measure | Value |
|---|---|
| Songs (region + key) | 1,469 |
| Recordings per song: 1 / 2 / 3 / 4 / 5 | 1,331 / 103 / 23 / 8 / 4 |
| Singleton share | **90.6%** |
| Generic per-recording keys (`#`) | 272 recordings |
| Normalised titles in > 1 region | 13 titles, 55 recordings (哭嫁歌, 对花, 绣荷包, 孟姜女, 月光光, 四季歌 …) |

- **Famous songs are not over-represented.** The most-recorded song has 5 recordings (送郎调, 打支山歌过横排, 斑鸠调, 辽阔的草原). The Round 2 cap (≤ 2 per named song) worked. 茉莉花 has 8 recordings over 4 regions.
- **The flip side: almost no within-song variation.** Cross-performance and tune-family analyses rest on 138 songs with ≥ 2 recordings and 13 cross-region titles. The planned 8-tune case study (critiques §1.7) has little material: 茉莉花 8, 绣荷包 7, 孟姜女 6 recordings.
- **Known key-splitting bug:** 沂蒙山小调, 康定情歌, 五指山歌, 请茶歌 get per-recording `#` keys (protocol "Known issue"). This inflates the singleton count and can leak a song across folds.

### 3.1 Genres missing relative to the musicology

| Region | Expected (Miao–Qiao, 集成 classification) | In the corpus |
|---|---|---|
| Hakka | 山歌 dominant; also 小调, 灯歌, 号子 | 0 work songs, 0 song_and_dance |
| Yue | 咸水歌, 木鱼, 龙舟, 粤讴, 渔歌 | 45 `other`; narrative 9 |
| Min–Tai | 褒歌, 南音 (excluded as quyi), 车鼓, Indigenous polyphony | 0 field songs; 0 multipart; 0 Indigenous |
| Tibetan | 嘉绒 multipart, 酒歌, 劳动歌 | 0 multipart; work_song 5 |
| Xinjiang | muqam, 达斯坦, Kazakh 阿依特斯 | 58 `other`; 0 long_song (Kazakh) |
| SW Multi-ethnic | 侗族大歌, 壮族多声部, 彝族海菜腔, 苗族飞歌 | multipart 29 (good); 飞歌 under mountain_song |
| Jiangsu–Zhejiang | 吴歌, 田山歌, 号子 | field_song 14, work_song 12 (adequate) |
| Northeast Plain | 号子, 秧歌, 二人转小帽 | work_song 11, song_and_dance 2 |
| Gan | 采茶, 山歌, 号子 | work_song 1 |

---

## 4. Performance context

| Region | 原生态 | field | 民族唱法 | other | instrumental | accompanied flag | speech ≥ 0.3 | median upload year |
|---|---|---|---|---|---|---|---|---|
| Gan | 18% | 13% | **43%** | 22% | 2 | 0% | 13% | 2022 |
| Southwest Plateau | 60% | 1% | **37%** | 1% | 0 | 1% | 13% | 2022 |
| Northeast Plain | 51% | 10% | **33%** | 6% | 0 | 4% | 3% | 2023 |
| Jiang–Han | 49% | 10% | **30%** | 10% | 0 | 0% | 7% | 2022 |
| Jiang–Huai | 69% | 2% | 20% | 8% | 1 | 3% | 10% | 2023 |
| NW Plateau | 91% | 5% | 4% | 0% | 0 | 7% | 2% | 2024 |
| Tibetan | 89% | 7% | 3% | 2% | 0 | 25% | 4% | 2021 |
| SW Multi-ethnic | 88% | 10% | 0% | 1% | 3 | 14% | 3% | 2021 |
| Steppe | 85% | 5% | 6% | 5% | 0 | 27% | 4% | 2021 |
| Xinjiang | 74% | 15% | 12% | 0% | 0 | 40% | 3% | 2021 |
| Yue | 58% | 20% | 8% | 14% | 0 | 0% | 17% | 2021.5 |

(Other regions are between these.) All 1,655: 原生态 1,172 (70.8%), 民族唱法 234 (14.1%), field 155 (9.4%), other 86, instrumental 8.

Findings:
- **民族唱法 is concentrated in four Han regions** (Gan 43%, SW Plateau 37%, NE Plain 33%, Jiang–Han 30%) and near zero in the minority regions. A classifier can partly learn "conservatory voice → Han region".
- **"原生态" mixes field and studio.** 99% of series items are labelled 原生态, yet the card calls the series "one studio production". Series median `vocal_db` = 34.0 dB vs 3.2 dB for the rest. A user cannot separate studio-staged from field singing with `performance_type`.
- **Accompaniment is unknown for 67%.** `feature_flags` is filled for 32.6% of recordings, and every filled row is a series item. Outside the series there is no accompaniment information.
- **Upload year is not recording year.** 2021 has 430 uploads (the series upload burst); 74% of uploads are 2021–2026. No recording date exists except the 8 CREM items (1959, 1988) and a few evidence notes ("1963 艺研院录音"). Diachronic claims are impossible.
- **Speech:** 123 recordings have speech share ≥ 0.3; 122 of them are in `subset=core` (98 in `core=True`). Yue (17%), Gan and SW Plateau (13%) are highest. The two-signal rule is defensible, but the classifier is known to fire on unaccompanied singing, so the share mixes speech and sparse singing.
- **Instrumental items:** 8 with `performance_type = instrumental`, 20 with a YourMT3+ primary transcription, 168 with an `instrument:` flag. A "folk song" corpus should flag or exclude the 8.

---

## 5. Transcription and derived data

### 5.1 Model mix and QC indicators

Primary model: GAME 3-run ensemble 1,618 (97.8%), ROSVOT 17 (8 in Steppe), YourMT3+ 20 (6 Tibetan, 4 SW Multi-ethnic).

| Region (sorted by GAME–ROSVOT agreement) | median agreement | agreement < 0.35 | median vocal_db | vocal_db < 0 dB |
|---|---|---|---|---|
| SW Multi-ethnic | 0.422 | **28.6%** | 15.7 | 10.1% |
| Northern Steppe | 0.424 | **28.0%** | 9.1 | 19.7% |
| Southwest Plateau | 0.435 | 19.8% | 4.7 | 25.6% |
| Xiang | 0.435 | 18.4% | 15.2 | 16.5% |
| Xinjiang | 0.435 | 14.7% | 2.9 | **31.8%** |
| Gan | 0.445 | 10.0% | 0.9 | **45.0%** |
| Tibetan | 0.479 | **24.6%** | 4.8 | **32.2%** |
| Jiangsu–Zhejiang | 0.489 | 10.1% | 20.2 | 13.1% |
| **All** | 0.453 | 16.4% | 6.3 | 22.8% |

By genre, agreement is lowest for multipart (0.327), long_song (0.382) and work_song (0.413). These are the genres the thesis cares most about.

**Weakest regions:** SW Multi-ethnic (multipart, low agreement), Northern Steppe (long song, ROSVOT fallbacks), Tibetan (YourMT3+ fallbacks, a third with accompaniment louder than the voice), Xinjiang and Gan (accompaniment louder than the voice in 32% and 45%).

### 5.2 Anthology distance check (`anthology_distance_summary.md`)

- 98 matched recordings: primary pitch accuracy 0.585 vs 0.394 for random same-volume scores; contour 0.857 vs 0.816; "confirms" 60.2%.
- Uncertain pairs (65) fall to 0.424 vs 0.376: the title match, not the transcription, drives much of the gap.
- **Coverage is Han-only in practice:** Northeast Plain 32, Jiang–Huai 20, Jiangsu–Zhejiang 19, Yue 10; Steppe 5, NW Plateau 3, Hakka 3; 0 for Tibetan, Xinjiang, SW Multi-ethnic, Xiang, Gan, Min–Tai, Jiang–Han. Round 3: 3 recordings.
- The contour baseline (0.816) is close to the result (0.857). Contour agreement says little.

### 5.3 Scores

10,830 scores (Anthology 8,641, Essen 2,189). Northeast Plain 2,853, Jiangsu–Zhejiang 2,385, Yue 2,111 = 68%. **Hakka 0**, Tibetan 6, Xinjiang 22, SW Multi-ethnic 24, Gan 66. The Anthology covers 9 provinces (5 regions); minority regions come only from Essen. The abstract presents the scores as covering the colour regions; they do not cover 4 of them in any useful amount.

### 5.4 What a user can and cannot rely on

| Can rely on | Cannot rely on |
|---|---|
| F0 tracks of the separated voice (RMVPE, PESTO with confidence) for single-voice, voice-dominant items | Note-level accuracy anywhere: no human reference yet (gold set unrated) |
| Melodic contour and pitch-class distribution in Han regions with Anthology support | Notes in multipart, long song, heterophonic or accompanied items (agreement < 0.35 for 16.4% overall, ~28% in SW Multi-ethnic/Steppe) |
| Link + fingerprint for re-download verification (1,655/1,655 fingerprints) | MusicXML metre (nominal grid; card says so) |
| Region at province level for 97.4% | County location for 56% (only 44.1% county) |

---

## 6. Release readiness for TISMIR

### 6.1 Paper vs data

| Paper says | Data say | Where |
|---|---|---|
| "collected the corpus in two rounds" | 3 rounds; Round 3 = 358 from one channel | `00_abstract.tex` l.8, `01_introduction.tex` l.32, `03_design.tex` l.5, `04_collection.tex` l.3 |
| Agents ran "28 September to 2 October 2026" | Round 3 and song labels ran 2026-10-04 to 10-14 | `04_collection.tex` |
| Largest channel "37% of Tibetan, 33% of SW Multi-ethnic" (typed) | 52.5% and 64.3% | `06_description.tex` |
| Tier A/B "24% (NE Plain) to 48% (Min–Tai)" (typed) | 22.7% (NE Plain) to 47.1% (Hakka) | `06_description.tex` |
| "compositions in folk style are excluded" | 31 `folk_style_composed` recordings are in the release | `04_collection.tex` |
| Example study on 1,184 core recordings | Core is now 1,537 (`core`) or 1,561 (`subset`) | `08_example_study.tex` |
| Eight CREM items: links and metadata only | HF ships MIDI ×3, MusicXML, F0 ×2 for all 8 | `09_ethics_limitations.tex` |
| Folds "assigned … to one of five folds" are part of the protocol | HF ships no `fold` (author decision); git `metadata/` ships it | `06_description.tex` |
| — | No mention of song labels, `song_label_check`, the subset column, Anthology overlap, or the series flag | whole paper |
| Draft text "h hioiii this paragraph is about reproducibility" | — | `06_description.tex` |

The section text is about 6,075 words without references. Adding Round 3 and song labels needs about 400–600 words; the 8,000-word cap includes references.

### 6.2 Release files

| Issue | Evidence | Severity |
|---|---|---|
| `core` and `subset` disagree | 24 rows (all `core_exclusion = speech`) have `subset = core`, `core = False`. A user filtering on `subset` gets 1,561; on `core` 1,537. `numbers.tex` uses 1,537 | High (silent) |
| `metadata/README.md` stale | Says 1,297 recordings, `round` "1 or 2"; omits `song_label_check` "disputed"… The HF card is current | Medium |
| `fold` in git `metadata/` | `export_metadata.py` line 23 exports it; HF build drops it | Medium |
| Region of song labels vs recordings | 13 recordings moved 赣 → Hakka; their songs stay `region = 赣` with `disagree:Hakka` in `song_labels.csv` | Low–medium |
| `check_release.py` misses all of the above | It prints OK | Medium |

### 6.3 Licence and rights

- CC BY-NC-SA 4.0 on derived data of third-party recordings. Derived MIDI/F0 of copyrighted performances is a grey zone; the paper should say why it is defensible (non-expressive, research, no audio) and cite a legal basis or precedent (e.g. other link-based MIR datasets).
- CREM items: "In Copyright" (critiques probe log). Their derived data is in the HF build now, against the paper's promise.
- Essen terms still `\authq` in §10.
- Round 3 is one commercial label's channel (瑞鸣音乐 Rhymoi). 539 items of derived data from one rights holder: ask them, or at least name the risk.

### 6.4 Link decay and reproducibility

- `link_status.csv` (2026-10-14): 1,646/1,655 alive (99.5%). **All 9 dead links are Round 3, YouTube, series, core.** Round 3 audio was downloaded days before. The decay is concentrated on the channel that holds a third of the corpus. If that channel is removed, 539 recordings lose audio.
- Fingerprints: 1,655/1,655, no duplicates, no duplicate URLs. Good.
- The paper's reproducibility paragraph has an `\authq` for environments and commands.

### 6.5 Splits

- `group_id`: 628 groups; the largest has 648 recordings (39.2%), including 60.5% of all minority-region recordings. Any group-respecting 5-fold split puts most minority data in one fold. The paper says this, but the card's advice ("report results with and without the series") has no released split that does it.
- Internal folds (329–333 per fold) cut the series link. They are not released. A reviewer will ask for the official split. **Release one**, documented as "series-split" vs "strict group".
- Song-disjointness relies on `song_key`, which has the `#` splitting bug (§3).

### 6.6 Privacy

- `singer_inheritor` names people on rows whose `singer` is withheld: 操明花 (A2, 徽州民歌), 艾赛提·莫合塔尔 and 艾买提·苏批 (A2, 哈密木卡姆), 曹光裕 (A2, 川江号子). If they are national bearers and the singers, these rows should be A1 and named; if not, the names should go.
- A1 rows name all co-singers (卓玛措、降巴其扎; 华尔贡、久西草; 汤明哲、童爱娜). Only the listed bearer has a public role. The co-singers may not.
- `title` keeps names as published (disclosed in §9). Acceptable, but say that the title is the main residual risk.
- The contrast set names singers for 92% (创作民歌) and 100% (古风) of items. These are professional public performers; still, apply the same rule or state a different one.

---

## 7. The contrast set (`data/contrast/candidates_clean/`)

| | 创作民歌 | 古风 |
|---|---|---|
| Candidates | 79 | 90 |
| Platform | Bilibili 100% | Bilibili 100% |
| Channels | 53; top channel 8 (10%) | 48; **top channel 29 (32%)**, a Hi-Res re-upload channel |
| Years | 1936–2013, median 1964 | 2003–2025, median 2018 |
| `idiom_region` filled | 75/79 (but 9 "全国", 4 "无", several provinces not regions) | **16/90**; 74 empty |
| Re-upload/restoration titles (修复, Hi-Res, 4K, MV, 录音棚) | 8 | **60** |
| Credits from secondary sources | 37 cite herongyang | — |
| Overlap with corpus song names | 6: 浏阳河, 十送红军, 洪湖水浪打浪, 映山红 (all in `folk_style_composed`), 黄河船夫曲 and 祝酒歌 (in **core**, `folk_traditional`) | 0 |
| Downloaded / transcribed | No | No |

Risks:
- **Rights.** Most 古风 items are commercial pop (e.g. 周杰伦《东风破》) re-uploaded by non-owners. Linking to infringing re-uploads, and publishing transcriptions of commercial songs, is a larger risk than folk field videos. Prefer official channels.
- **Definition.** 古风 is a pop genre with no regional idiom in 82% of items, so it cannot serve as a per-region contrast. 创作民歌 regions are free text, not the 15 codes.
- **Leakage with core.** 黄河船夫曲 and 祝酒歌 are `folk_traditional` in core but listed as composed songs in the contrast set. One of the two labels is wrong. 祝酒歌 (施光南 1977) vs a SW Multi-ethnic 祝酒歌 may be a title clash; 黄河船夫曲 has a known 1950s arrangement history. Resolve before release.
- **Timeline.** Planned for v1.1. It should not appear in the TISMIR paper beyond one sentence.

---

## 8. What a TISMIR reviewer would attack, ranked

| Rank | Attack | Severity | Cheapest credible fix | Effort |
|---|---|---|---|---|
| 1 | "The paper does not describe the released data" (rounds, numbers, missing song labels, stray text) | Desk-reject risk | Update §4, §6, §7, §9 for 3 rounds; generate all numbers (incl. channel and tier ranges) by macro; one paragraph + table on song labels and subsets | 2–3 days, writing |
| 2 | "No human has validated the agents' labels" | High | Fill the 60-item spot-check (4 per region) and report agreement with CIs; rate the 150-note gold set | 1.5 days, human |
| 3 | "One commercial studio series dominates the minority regions; results reflect the channel" | High | Release a second split that cuts the series; report every number with/without series; add series as a covariate | 1 day, data + ½ day writing |
| 4 | "Region labels are title-based for two thirds of items" | High | Report all analyses on tier A/B (591 items) as well; state per-region A/B share in Table 1 | ½ day, data |
| 5 | "Song labels are agent guesses" (70.9% knowledge-only, 89% low) | Medium–high | Rename "reviewed" to "consistency-checked (no source)"; use a search budget on the ~177 medium/high or famous titles and the 34 disputed; resolve the 3 genre rules | 2–3 days, labelling + ½ day author decisions |
| 6 | "Release tables are internally inconsistent" | Medium | Fix the 24 `core`/`subset` rows, `metadata/README.md`, `fold` export, song-label region; add these checks to `check_release.py` | ½ day, data |
| 7 | "Performance context is confounded with region" (民族唱法 in 4 Han regions; studio series in minority regions) | Medium | Add `recording_context` (field / broadcast / studio series / user upload) by rule from channel and flags; one covariate table | 1–2 days, data |
| 8 | "Rights: copyrighted archive derived data released; commercial series" | Medium | Remove CREM derived files from HF until permission; write to Rhymoi; add a rights paragraph with precedent | ½ day data + email |
| 9 | "Privacy: names leak through `singer_inheritor`" | Medium | Redact names in `singer_inheritor` except the A1 singer; re-tier the 4 named A2 bearers after a lookup | ½ day, data |
| 10 | "Scores are not mapped to all regions; minority regions have ≤ 24 scores, Hakka 0" | Medium | State it in the abstract and Table 1; restrict score-based claims to the 5–6 covered regions | ½ day, writing |
| 11 | "Transcriptions are unreliable exactly where it matters" (multipart, long song, accompanied) | Medium | Publish per-region/per-genre QC table (agreement, vocal_db) and a `transcription_reliability` flag (e.g. agreement < 0.35 or vocal_db < 0) | 1 day, data |
| 12 | "Genre coverage gaps" (`other` 52% Yue, 45% Xinjiang; no Indigenous Taiwan; multipart absent in Tibetan/Min–Tai) | Low–medium | Decide 咸水歌 and muqam genres; add a coverage-gap table in §9 | 1 day, labelling + writing |
| 13 | "Links will rot; the biggest channel is already losing items" | Low–medium | Re-check monthly until submission; report decay by channel; mention Internet Archive mirrors | 1 h per check |
| 14 | "Contrast set is pop re-uploads" | Low (v1.1) | Keep out of the paper; restrict to official channels | — |

---

## Prioritised action list

| # | Action | Owner type | Effort | Unblocks |
|---|---|---|---|---|
| 1 | Fix release bugs: 24 `core`/`subset` rows; `fold` out of `export_metadata.py` (or release it on purpose); `metadata/README.md` to 1,655 and 3 rounds; song-label region after overrides; redact `singer_inheritor`; drop CREM derived files from `build_hf.py`. Extend `check_release.py` to catch each | data | ½–1 day | 6, 8, 9 |
| 2 | Paper: rewrite for 3 rounds (abstract, intro, §3, §4, §6, §7, §9, §10); remove the stray line; add macros for channel share per region and tier A/B range; add a song-label paragraph and table | writing | 2–3 days | 1 |
| 3 | Run the 60-item curation spot-check and report agreement per field with 95% CIs | human study | 1 day | 2, 4 |
| 4 | Rate the 150-note gold set | human study | ½ day | 2, 11 |
| 5 | Release a second split ("series-split": series link cut, ≤ 25% of a region per fold) beside strict `group_id`; recompute the example study on 1,537 core with and without series | data | 1 day + GPU-free reruns | 3 |
| 6 | Tier-stratified results (A/B vs C) for every reported number | data | ½ day | 4 |
| 7 | Add `recording_context` column; report 民族唱法 and studio share per region in Table 1 | data | 1–2 days | 7 |
| 8 | Author decisions on the 34 disputed songs and the 咸水歌 / 花儿–长调 / muqam genre rules; apply via `adjudication.csv` | labelling (author) | ½ day + rebuild | 5, 12 |
| 9 | Targeted source search for medium/high and famous titles (≈ 180 songs), plus 黄河船夫曲 and 祝酒歌 (contrast-set conflict); relabel "reviewed" as consistency-only in docs | labelling | 2–3 days | 5 |
| 10 | Per-region/per-genre transcription QC table and a reliability flag column | data | 1 day | 11 |
| 11 | Coverage-gap table (provinces, ethnic groups, genres missing vs the region definitions) in §9 | writing | ½ day | 10, 12 |
| 12 | Rights: email CREM and Rhymoi; settle Essen terms; add a rights rationale paragraph | writing | ½ day + waiting | 8 |
| 13 | Fix the `#` key-splitting bug with a key-alias map | data | ½ day | 3 (song-disjoint splits) |
| 14 | Monthly link re-check, reported by channel | data | 1 h each | 13 |
| 15 | Code the 112 free-rhythm candidates; then freeze the notation-study selection | human study | 1 day | thesis claims 2b–2d |
| 16 | Contrast set: keep out of v1; before v1.1, restrict to official channels and map `idiom_region` to the 15 codes | data | 1–2 days (later) | 14 |

**Critical path to submission (2026-12-01):** items 1–6 (≈ 6–7 working days, of which 1.5 days are human). Items 7–12 strengthen the paper but are not blockers if the limitations are stated.
