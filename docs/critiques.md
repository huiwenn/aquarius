# Critiques, improvement directions, and collection v2

Snapshot 2026-10-01. Companion to `docs/region_classification.md` (results, §12–22) and `docs/transcription.md` (collection, transcription, audit).

**Bottom line:** the biggest remaining problem is the data, not the models. The transcription set has 40 YouTube recordings per region, and one channel supplies 50–83% of the minority-region recordings.

---

## 1. Ways to improve (roughly by expected payoff)

1. **More, and more varied, transcription data.**
   - The learning curve had not flattened at 600 recordings.
   - At 2–10 recordings per region, adding the Anthology was worth about as much as doubling the transcriptions.
   - The few-shot table (§14.2) suggests that going from about 32 to 80–100 recordings per region could add more than any modelling change.
   - Spreading recordings across more channels per region matters as much as the raw count. The channel-grouped evaluation is only fair if minority regions don't depend on one channel.
2. **Model ornamentation (润腔) directly from audio.**
   - The skeleton/surface split showed that regional information lives in ornamentation, and the resynthesis test showed that note-level transcription loses it.
   - Build an F0 view from the RMVPE/PESTO tracks already extracted for the critic: glide shapes, vibrato rate and depth, deviation from tempered pitch, ornament density per phrase.
   - Add it to dual-view as a third, "surface from audio" view.
3. **Make transductive bias correction a real component.**
   - Re-centring logits took Anthology → transcriptions from 0.21 to 0.365 with no labels.
   - Untested so far: calibrating the dual-view skeleton view on the target batch.
   - Then try proper unsupervised domain adaptation (pseudo-labelling, or adversarial alignment of the skeleton view).
4. **Pretrain on Chinese folk melodies themselves.**
   - Generic and Western-trained models (MusicBERT, MuPT, CLaMP) miss mode and 偏音, which are exactly what defines 色彩区.
   - Train self-supervised on Anthology + Essen (+ MGD, if notes can be obtained) with 宫-relative degree and interval tokens.
   - The earlier masked-note pretraining was tiny: 6k steps on 11k songs, with generic tokens.
5. **Better labels.**
   - 色彩区 is coarser than the real stylistic structure. Provinces and Anthology volumes are separable, and Henan clusters with 东北 rather than 江汉.
   - Use hierarchical targets (province → 色彩区) or ordinal ones (regression on latitude/longitude, with geographic error as the metric).
   - Give partial credit for confusions between neighbouring regions.
6. **Cleaner minority-region evaluation.**
   - Hold out entire channels as a fixed external test set.
   - Report minority regions separately from Han regions. They behave differently: minority regions have distinctive scales, Han regions show channel dominance.
7. **Tune-family analysis** (for the influence-over-time question).
   - Align regional variants of shared tunes (茉莉花, 孟姜女, 绣荷包) to see which elements localize (mode, cadence, 偏音) and which travel intact.
   - Unlike song dating, this needs no absolute dates.

## 2. Critiques a reviewer would still raise

### Data and labels
- **Small, convenience-sampled data.**
  - The transcription set is 600 YouTube recordings with no control over singer, era, recording quality or editing.
  - Channel concentration is heavy.
  - We cannot claim the recordings represent their regions.
- **Labels are assigned, not observed.**
  - A recording's region comes from curation (song title, channel description), not from verified provenance of the singer.
  - Some 民族唱法 performers are not from the region they sing.
  - Some labels needed judgment calls (e.g. 江苏 → 江淮 vs 江浙).
- **The taxonomy is contested.** Our own clustering result says 色彩区 is no more learnable than any contiguous geographic grouping. "Classifying 色彩区" may really be estimating geographic proximity.
- **Modern compositions are mixed in.** Song dating found canonical "民歌" that are 1950s–80s compositions. They were not excluded from training or test.

### Method and evaluation
- **Pipeline-induced signal.**
  - Transcription quirks could correlate with region through recording conditions rather than music.
  - Channel-grouped folds block the obvious version of this, but not subtler ones (e.g. regions dominated by field recordings vs studio recordings).
- **Researcher degrees of freedom.**
  - About 900 runs are logged, and choosing what to report among them is a form of selection.
  - Nested CV and fresh seeds check the tuning, but not that choice.
  - There is no pre-registered held-out test set that was never touched during development.
- **Small effects, wide intervals.** On the 5-region tasks (≈200 items), effects of ±0.04 are at the edge of detection.
- **Score corpora are confounded with collections.**
  - In the Anthology, region = province volumes = editorial teams. Leave-one-volume-out helps (0.43 vs 0.69) but cannot fully separate regional style from editorial practice.
  - Essen is 49% 西北.
- **Transductive tricks.** The 0.365 transfer number relies on test-batch statistics and roughly balanced classes, which a deployed classifier would not have.
- **The resynthesis test used a toy voice.**
  - An additive synth is not a singer, so "the transcriber isn't the bottleneck" is suggestive, not proven.
  - The accompanied condition failed outright.
- **Transcription accuracy is not measured on our own data.**
  - The listening gold set was built (https://claude.ai/artifact/2d22Duf8owkvFQFx4xvYUU) but has not been rated.
  - So the accuracy that everything downstream depends on is still unmeasured on our recordings.

### Interpretation
- **Correlation stories.**
  - Musicological readings of n-gram coefficients and saliency maps (乙反调 in 粤, fourths in 西北) are post hoc.
  - They match the literature, but there is no test that an expert would agree those features cause the predictions.
- **The homogenization claim is weak.** n = 27, not significant. Dated songs mostly carry 20th-century attestation dates, not origin dates.

### Three things to do first
1. Collect a second batch of recordings from new channels for the minority regions, and keep it as an untouched test set.
2. Rate the listening gold set.
3. Add the F0 ornamentation view to dual-view.

---

## 3. Collection v2: mapping critiques to fixes

| Critique | Collection fix |
|---|---|
| Labels assigned from titles, not provenance | Sources that record **who sang it and where**: heritage-bearer (非遗传承人) lists, field-recording archives, institutional datasets |
| Channel concentration | **Per-region channel quotas** (e.g. ≤ 25% from any one channel), plus a held-out set from channels never used in training |
| Convenience sample, modern songs mixed in | Exclude composed songs with `data/regions_curated/song_dates/all_songs.csv`; prioritize field (原生态) recordings |
| Too small | New platforms (Bilibili is much larger for Chinese folk music), archives, academic audio datasets |
| Score corpora cover few regions | More symbolic sources with region labels |

### Probe log (2026-10-01; WebSearch budget is exhausted, so all probes use curl / yt-dlp)

| Source | Result | Verdict |
|---|---|---|
| MGD / MGDplus (https://chinglohsiu.github.io/files/MGD.html) | Only metadata links (`MGD-INFO/分省信息-*.xlsx`), Wikipedia links, and one Bilibili example (BV1gT4y1N7Fk). No audio download link. MGDplus (1,214 songs, 7 regions, partial audio–score alignment) is mentioned only. | Get the per-province xlsx files as a **title/region list** to drive searches. Contact the authors for MGDplus audio. |
| Internet Archive advancedsearch | `民歌 OR 山歌 OR 小调` + audio gives 711 hits, mostly noise (audiobooks, podcasts). Only 3 hits for "Chinese folk song". IA does hold **Bilibili mirrors** (`BiliBili-BV…` identifiers). | Low yield for field recordings. Possibly useful as a Bilibili mirror for dead links. |
| Europeana API (`wskey=api2demo`) | 16 sound items for "chinese folk song". Includes **CREM (Centre de Recherche en Ethnomusicologie)** field recordings: Tibetan, Miao, Kyrgyz songs (rights: In Copyright). | Real provenance-labelled field recordings for minority regions. Next: query by ethnic group (Miao, Yi, Uyghur, Mongol, Tibetan, Dong…). Also query CREM/Telemeta (archives.crem-cnrs.fr) directly. Research use only. |
| Wikimedia Commons | `Category:Folk_music_of_China` → `Category:Folk songs of China`, `Jiangnan sizhu` | Small, but freely licensed. Enumerate the subcategory recursively. |
| ihchina.cn (中国非物质文化遗产网) | `representative.html` (国家级代表性传承人) is reachable with a browser UA. | Scrape the inheritor list for project category 传统音乐 (民歌): **singer name + county + ethnicity + genre**. Then search YouTube/Bilibili by **singer name**, which gives provenance-verified labels. |
| Bilibili via yt-dlp | Not yet tested. The yt-dlp path in the probe was wrong; it lives elsewhere, see `src/secaiqu/download_curated.py`. Earlier `bilisearch` returned HTTP 412 (needs wbi signing / cookies). | Next: download BV1gT4y1N7Fk with Firefox cookies. If that works, search via the web API with cookies, or via IA mirrors. |

### Remaining ideas, not yet probed
- **Heritage-bearer search:** take the 传承人 names from ihchina, then run `ytsearch` / Bilibili search for "<name> <genre>". Provenance comes from the official list, not the title.
- **Broadcasters' field series:** CCTV 《民歌·中国》, 《中国民歌大会》 (studio, modern arrangements, so use for caution/negatives), and provincial TV 原生态 contests (青歌赛 原生态唱法 2006–2013: singers are explicitly labelled by ethnicity and region).
- **Commercial/academic anthologies:** 《中国民族民间器乐曲集成》 and 《中国民间歌曲集成》 audio companions; 中国艺术研究院 音乐研究所 archive (only the catalogue is likely accessible); Smithsonian Folkways and Ocora China releases (metadata gives singer and county; streaming only).
- **Ximalaya / QQ Music / NetEase playlists:** large but provenance-poor. Use them only for counts and title lists.
- **Symbolic:** per-province 《中国民间歌曲集成》 scans + OMR (Audiveris / oemer, jianpu OMR is harder); 简谱 sites (e.g. jianpu99, qupu123), whose jianpu text is parseable and already region-tagged by the uploader.
- **Quality controls for v2:** per-region channel cap; a held-out test set from new channels, frozen before any experiment; exclusion of composed songs via the dating table; a `provenance` column (`official_list` / `archive` / `title_only`) so results can be reported per provenance tier.

---

## 4. Status of each critique (2026-10-02, paper draft in `../colour_regions_paper/`)

| Critique (§2 above) | What was done | Status |
|---|---|---|
| Small, convenience-sampled data | Round 2 added 697 recordings (1,297 in total, 73–90 per region), Bilibili added, 8 CREM archive items; the sampling bias is stated in paper §10 | Addressed; bias disclosed |
| Channel concentration | Round 2 caps 4 per channel per region (max 12%); folds grouped by channel ∪ singer (`group_id`); merged pool still 37%/33% in Tibetan/SW Multi-ethnic, reported | Addressed; residual reported |
| Labels assigned, not observed | Provenance tiers A1/A2/B/C; 34 singers verified on the national heritage list (A1); Round 1 re-tiered (10% A/B vs 52% in Round 2); 55 label/arrangement exclusions → core subset; human spot-check page built | Partly; human check pending |
| Taxonomy contested | Sources of the 15 regions stated (Miao–Qiao 11 + CCTV minority areas); "not more learnable than contiguous geography" result reported in §8.1; province/county/ethnic group released | Addressed |
| Modern compositions mixed in | `dating_flag`; 57 composed recordings excluded from core | Addressed |
| Pipeline-induced signal | Within-recording friction contrasts, same-singer cross-channel pairs and controlled degradation planned (`thesis_evidence_plan.md` B3); recording-condition covariates | Designed; pending |
| Researcher degrees of freedom / no held-out set | Round 2 kept apart from Round 1 channels; design and criteria frozen before notation (internal hashed commit); merged-pool + Round 1 → Round 2 test planned | Designed; pending Round 2 transcription |
| Small effects, wide intervals | CIs and permutation tests on all reported numbers; power analysis for the notation study (review 02) drove 45 excerpts | Addressed in design |
| Score corpora confounded with collections | Leave-one-volume-out reported; Henan/Jiangsu mapping limits stated; editorial practice treated as a component | Disclosed |
| Transductive tricks | Transfer-with-bias-correction numbers not used in the paper | Removed |
| Resynthesis test used a toy voice | Not used as evidence in the paper | Removed |
| Transcription accuracy unmeasured on our data | Gold set (150 notes) ready to rate; 3-notator envelope study designed (guideline v1.1-draft, selection script, decision table) | Pending human work |
| Correlation stories (post-hoc musicology) | Replaced by pre-specified hypotheses with minimum effects (苦音, long song, 润腔 → error type) | Designed |
| Homogenization claim weak | Not claimed in the paper | Removed |
| §1.2 F0 ornamentation view | Intonation profiles computed (`src/regionclf/intonation.py`); exploratory only, chance level on Round 1 | Exploratory, logged |
| §1.7 Tune-family analysis | Planned as an 8-tune case study with specialist check (§9) | Designed |
