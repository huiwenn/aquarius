# Columns of the release

`data/colour_regions/recordings.csv` is the full internal table. `metadata/recordings.csv` and the Hugging Face `recordings` table are the released subset: they omit internal QC and the `fold`, and HF adds file paths. **Source** says where a value comes from, which is the place to change it. "Built" means a script computes it, so don't edit it.

## Identity and source

| Column | Meaning | Values | Source |
|---|---|---|---|
| `item_id` | Video identifier (YouTube id, Bilibili BV id, Europeana id) | unique | candidate list |
| `round` | Collection round | 1, 2, 3, … | built (round folder) |
| `platform`, `url` | Platform and link | `youtube`, `bilibili`, `europeana` | candidate list |
| `title`, `channel`, `channel_key`, `upload_date`, `duration_s` | As published by the platform; `channel_key` = `platform:channel-id` | | downloader (`.info.json`) |

## Place and people

| Column | Meaning | Values | Source |
|---|---|---|---|
| `region` | Colour region (Chinese name) | the 15 names in `src/colour_regions/regions.py` | candidate list; moved by `region_overrides.csv` |
| `region_en`, `region_code`, `region_type` | English name, short code, `Han` / `minority` | | built from `regions.py` |
| `region_curator` | Region before any override | | built |
| `province`, `county_or_area` | Place as stated by the source (county/village level when known) | free text | candidate list |
| `geo_level`, `geo_name`, `lon`, `lat` | Gazetteer match of the place | `county` / `prefecture` / `province` / `none` | built (`geocode.py`) |
| `ethnic_group`, `ethnic_subgroup` | e.g. `汉` + `客家`, `蒙古`, `藏` | normalised, no 族 suffix | candidate list |
| `singer` | Name, **only for national heritage bearers** (tier A1) | | candidate list; redacted on build |
| `singer_id` | Pseudonymous, stable ID per normalised name | `S` + 8 hex | built |
| `singer_inheritor` | Heritage-bearer status as found on ihchina.cn | e.g. `国家级: 蒙古族长调民歌 (2009)` | `check_inheritors.py` |

## Song (curator level)

| Column | Meaning | Values | Source |
|---|---|---|---|
| `song_name` | Song title as the curator normalised it | | candidate list |
| `song_key` | Normalised title used to group recordings into songs. Generic titles (信天游, 山歌 …) get `title#item_id`, so they stay separate songs | | built |
| `genre` | Curator genre in Chinese (山歌, 小调, 号子, 花儿, 长调 …) | free text | candidate list |
| `performance_type` | `原生态` (tradition bearer), `field` (field recording), `民族唱法` (conservatory folk style), `instrumental`, `other` | 5 values | candidate list |
| `dating_flag` | Curator's first judgement: `traditional`, `check` (unsure), `composed` (known composer; leaves core) | 3 values | candidate list |

## Provenance (how sure is the region?)

| Column | Meaning | Values |
|---|---|---|
| `provenance_tier` | `A1` national heritage bearer of that song tradition; `A2` named singer whose county is stated; `B` field or locality-attested recording (county/township stated, e.g. a county cultural-centre film); `C` region inferred from title or genre only | A1, A2, B, C |
| `provenance_tier_curator` | Tier before automatic upgrades (`A` = A1 or A2) | |
| `provenance_evidence` | The evidence in one line (names redacted) | free text |
| `label_status`, `label_concern` | Round-1 label review (`exclude` / `minor`) | |

## Song labels (song level; evidence in `song_labels.csv`)

| Column (recordings / song_labels) | Values |
|---|---|
| `song_class` / `song_class` | `folk_traditional` (anonymous tradition), `folk_adapted` (traditional tune + new words or a named arrangement), `folk_style_composed` (创作民歌: new song in a folk idiom with a named author), `composed`, `court`, `religious`, `narrative_quyi` (曲艺 / 说唱), `opera` (a theatre excerpt), `instrumental`, `unknown` |
| `song_genre` / `genre` | `work_song` 号子, `mountain_song` 山歌 (信天游, 花儿, 爬山调, 飞歌 …), `field_song` 田歌, `ditty` 小调, `song_and_dance` 灯歌/歌舞 (花灯, 采茶, 秧歌, 锅庄, 弦子, 堆谐), `ritual_custom` 风俗/仪式歌 (婚嫁, 哭嫁, 酒歌, 祭祀), `narrative` 叙事歌, `children` 儿歌, `long_song` 长调, `short_song` 短调, `multipart` 多声部, `religious`, `other` |
| `song_genre_native` / `genre_native` | The attested Chinese term, as specific as possible (花儿·河州令, 吴歌·田歌, 锡林郭勒长调) |
| `composer`, `lyricist`, `arranger` | Names as a source gives them; empty for anonymous tradition (never "traditional") |
| `composition_period` | `traditional_undated`, `ming`, `qing`, `republic` (1912–49), `prc_1949_1965`, `prc_1966_1976`, `prc_1977_1999`, `after_2000`, `unknown` |
| `composition_year` / `year_best` + `composition_year_kind` / `year_kind` | The year and what it dates: `composition`, `adaptation`, `first_publication`, `first_recording`, `collection`, `earliest_attestation` |
| `song_label_confidence` / `confidence` | `high` (≥ 2 independent sources, or one authoritative), `medium` (one reasonable source or a well-known fact), `low` (genre, title or knowledge only) |
| `song_label_check` | `verified` (checked against a source by an independent reviewer), `reviewed` (a second reviewer found it consistent with all the evidence, without a source), `corrected` (changed after review), `disputed` (open question for the author: `song_labels/disputed.csv`), `unchecked` |
| — / `region_check` | `agree`, `disagree:<region>` (with a source), `unsure` |
| — / `evidence`, `sources`, `searched` | What the sources say; URLs, `anthology:<vol>#<n>`, `rhymoi_description`, `prior_dating` or `knowledge`; whether a web search was made |

## Features, subsets, quality

| Column | Meaning |
|---|---|
| `feature_flags` | Tags, `;`-separated (a list on HF): `series:musical_map_of_china`, `accompanied` / `unaccompanied`, `instrument:<name>`, `multiple_singers`, `song_and_dance`, `ritual`, `khoomei`. Add new tags in `src/colour_regions/rhymoi.py:semantic_flags` or the build, and document them here and in `metadata/README.md` |
| `subset` | `core` (default analysis set), `folk_style_composed` (创作民歌 kept as their own subset), `excluded` |
| `core`, `core_exclusion` | Core membership and the reasons: `label`, `arrangement`, `composed`, `folk_style_composed`, `speech` |
| `speech_share`, `speech_doc_meta`, `sung_share`, `music_share` | Speech screen: share of 10 s windows classified as speech, and whether the title/note marks a documentary. An item leaves core for speech only when both signals agree |
| `transcription_model` | Primary transcription: `game_ens3_pp` (GAME 3-run ensemble + trim), `rosvot`, `yourmt3` (instrumental) |
| `n_notes`, `notes_per_s`, `vocal_db`, `game_rosvot_agreement` | Transcription QC |
| `group_id` | Channel ∪ singer connected component. Keep a group on one side of any train/test split |
| `fold` | Internal 5-fold split, sampled by region (not released yet) |
