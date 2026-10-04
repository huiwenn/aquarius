# Can a melody tell us where it comes from? Region (色彩区) classification from symbolic music

Research log and reflection. Code: `src/regionclf/`. Results table (every run, all families):
`data/regionclf/results.csv`.

**Short answer.** Yes, partly:
- **Clean scores:** macro-F1 0.62 on 5 regions and 0.36 on 13 (chance 0.20 / 0.09).
- **Our noisy transcriptions:** 0.37 on all 15 regions (0.28 when folds are also grouped by channel; chance 0.05).
- **Best representation:** explicit, tonic- and tempo-relative multi-viewpoint motif counts, i.e. 2–4-note 音调
  cells.
- **Best way to mix clean scores with noisy performances:** dual-view. One model learns the shared *skeleton* from
  scores plus reduced transcriptions; another learns the performance *surface* from transcriptions alone.
- **Errors follow geography,** and the most-confused pairs are the literature's transition zones.

Jump to the **synthesis in §11**. Sections appear in the order experiments ran: 3 theory features and Markov
models, 4 descriptive musicology, 5 overview and pretrained embeddings, 6 data experiments, 9 confusion and
geography, 8 images, 7 sequence models, 10 robustness.

---

## 0. Question and framing

Chinese musicology divides Han folk song into **色彩区** (stylistic "colour regions", 江明惇 / 周青青), plus
minority song areas. The regions are defined by a *bundle* of traits rather than any one of them:
- scale type: 五声 vs 六/七声, and use of the 偏音 清角/变宫 (fa/ti)
- predominant mode: 宫商角徵羽 final
- characteristic intervals and 音调 cells: 西北's fourths and 信天游 leaps, 江浙's stepwise 小调, 湘's "羽音调",
  江汉's 三声腔
- phrase structure (two-, four-, five-line 赶五句 forms) and rhythm (散板 vs metered)

The computational question is whether these traits are learnable from notes alone, which representation captures
them best, and what kind of data (clean scores vs noisy transcriptions, one source vs a mix) makes the signal
learnable. We then read the results back musicologically: which traits separate which regions, and where the
regions blur.

## 1. Data

| Source | Items | Regions | Nature | Pitch | Time |
|---|---|---|---|---|---|
| **A** Anthology 《中国民间歌曲集成》 (OMR of printed 简谱) | 8,654 | 5 (东北部平原 2,673, 江浙平原 2,255, 粤 2,032, 江汉 987, 西南高原 707) from 9 province volumes | clean, edited *scores*: the collectors' skeleton melodies | 1=C (movable-do) | beats |
| **E** Essen Folksong Collection, China (Schaffrath, Humdrum kern) | 2,189 | 14 (西北部高原 1,068 dominates; minorities via ethnic group) | clean scores, older collection | real keys | beats |
| **T** our 色彩区 transcriptions (YouTube → htdemucs → GAME/ROSVOT/YourMT3+) | 600 | all 15 × 40 | noisy *performances*: ornaments, rubato, transcription errors | absolute sung pitch | seconds |

- **E region labels** come from the `!!!ARE` province keywords (Han) or the ethnic group (Menggu/Dawoer/Elunchun/
  Hezhe → 北方草原, Weiwuer/Hasake → 新疆, Zang → 藏族, Miao/Dong/Zhuang/Yao/Yi/Bai/Maonan → 西南多民族, Hui → 西北).
- **Not usable:** MGD (31.7k songs) turned out to be metadata only (titles, locations), with no notes.

**Confounds to design around:**
1. **Pitch conventions differ by source.** Every representation is made tonic-relative (宫 estimated by
   pentatonic-template fit), or explicitly tests absolute pitch as a confound probe.
2. **Time units differ** (beats vs seconds), so rhythm is always relative (IOI / median IOI).
3. **Same songs recur,** within sources (variants) and across them (109 transcriptions share a title with an
   Anthology score). Every split is grouped by normalized title, and external training data excludes titles
   present in the test fold.
4. **In A, region ≡ province volume ≡ one editorial team.** Part of what A5 learns could be editorial or OMR
   conventions, not regional style (§6).

## 2. Protocol
`src/regionclf/common.py`:
- tasks **A5**, **E** (13 regions with ≥20 songs), **T15**, **T5** (T restricted to A's 5 regions)
- StratifiedGroupKFold(5, seed 0) grouped by song title
- headline metric macro-F1, plus balanced accuracy

Chance (stratified random), macro-F1: A5 0.20, E 0.09, T15 0.05, T5 0.21.

## 3. Attempts log

(Chronological. Each row points to the script, the key numbers, and what we learned.)

### 3.1 Music-theory features (`features.py`, `exp_theory.py`), family "theory"
Blocks:
- scale-degree histogram relative to 宫
- final and longest-note degree (mode)
- scale type (number of degrees, 偏音 mass)
- interval histogram and contour
- 12×12 degree-transition matrix
- tempo-free rhythm (log IOI ratios, long/short-note shares)
- relative register

| Model | A5 | E | T15 | T5 |
|---|---|---|---|---|
| logistic regression | 0.466 | 0.253 | 0.211 | 0.378 |
| random forest | 0.475 | 0.166 | **0.288** | 0.441 |
| gradient boosting | **0.540** | **0.292** | 0.270 | **0.489** |
| + absolute pitch (LR) | 0.474 | 0.257 | 0.216 | 0.378 |

- **Absolute pitch adds nothing** once features are tonic-relative. The classifier isn't exploiting singer register
  or source key conventions.
- **Single-block ablations** (LR, macro-F1) show what carries the signal:

| Block | A5 | E | T15 | T5 |
|---|---|---|---|---|
| degree transitions (144) | **0.40** | 0.20 | 0.18 | 0.31 |
| intervals (27) | 0.35 | **0.22** | **0.20** | 0.33 |
| scale-degree histogram (12) | 0.29 | 0.11 | 0.12 | **0.36** |
| rhythm (10) | 0.29 | 0.10 | 0.14 | 0.28 |
| scale type (3) | 0.28 | 0.08 | 0.06 | 0.22 |
| mode final (12) | 0.13 | 0.04 | 0.07 | 0.29 |

  *Reading:*
  - On clean scores (A5), *how degrees follow each other* (the 音调 / melodic cells) is most regional.
  - On noisy transcriptions (T15), intervals are the most robust signal. They don't depend on estimating 宫, which
    ornaments and transcription errors perturb.
  - The mode final is weak everywhere except T5. Scores often end on the 宫 or 徵 regardless of region, and
    transcriptions' last note is often a trailing ornament.
EOF
echo ok
### 3.2 Per-region n-gram language models (`exp_markov.py`), family "markov"
This is a multiple-viewpoint approach after Conklin & Witten. We train a backoff n-gram model per region on each
viewpoint and classify a song by the region whose models give it the highest mean log-likelihood.
Viewpoints:
- **deg:** scale degree relative to 宫
- **int:** interval
- **degd:** degree × relative-duration class
- **ctr:** contour (direction × step/skip/leap)

| Viewpoints / order | A5 | E | T15 | T5 |
|---|---|---|---|---|
| deg / 2 | 0.368 | 0.203 | 0.192 | 0.347 |
| deg / 4 | 0.468 | 0.271 | 0.185 | 0.326 |
| int / 3 | 0.473 | 0.302 | 0.199 | 0.307 |
| degd / 3 | 0.505 | 0.267 | 0.207 | 0.312 |
| ctr / 3 | 0.429 | 0.276 | **0.266** | **0.378** |
| deg+int+degd+ctr / 3 | **0.515** | **0.345** | 0.255 | 0.349 |

What we learned:
- **On Essen, the multi-viewpoint combination is the best method so far** (0.345 vs 0.29 for feature vectors).
  Sequence likelihood captures melodic formulae (音调) that a bag of features dilutes.
- **On clean scores, longer contexts help** (deg 0.37 → 0.47 from order 2 to 4). Regional style lives in
  3–4-note cells, e.g. the 西北 "sol–do–re" fourth-plus-step cell and the 江浙 stepwise turn figures.
- **On noisy transcriptions, the coarsest viewpoint wins.** Contour beats exact degrees (0.266 vs 0.19). Every
  finer viewpoint inherits the transcriber's pitch errors and the 宫-estimation errors, and abstraction trades
  resolution for robustness. That is the multiple-viewpoint argument, shown empirically on noisy data.

### 3.3 Transfer between sources (`exp_mixing.py transfer`), family "data"
Theory features + gradient boosting, trained on one source only:

| Train → test | Macro-F1 | Chance |
|---|---|---|
| Anthology → T5 (transcriptions) | 0.223 | 0.21 |
| Essen-5 → T5 | 0.230 | 0.21 |
| Anthology + Essen-5 → T5 | 0.233 | 0.21 |
| T5 → Anthology | 0.170 | 0.20 |
| Essen-5 → Anthology | **0.335** | 0.20 |
| Anthology → Essen-5 | **0.449** | 0.20 |
| Essen → T14 | 0.069 | 0.05 |

- **Score ↔ score transfer works** (Anthology and Essen are independent collections: different editors, eras and
  encodings). This is the strongest evidence that what A5 learns is regional style, not one volume's editorial
  habits.
- **Score ↔ performance transfer fails,** in both directions.

## 4. Why scores don't transfer to performances: descriptive musicology (`describe.py`)
Per region and source means are in `data/regionclf/describe.csv`.

**Scores (Anthology and Essen) agree with each other and with the literature:**
- **Mode finals:**
  - 徵 dominates 东北部平原 (0.42/0.45), 江汉 (0.56/0.57), 江淮 (0.58), 赣 (0.58) and 西北部高原 (0.55, plus 商
    0.21: "徵、商调式为主" ✓).
  - 羽 leads in 西南高原 (0.30/0.53), 北方草原 (Mongolian, 0.48), 西南多民族 (0.46) and 湘 (0.28, cf. "湘羽音调").
  - 江浙平原 is 徵-first (0.33/0.42, "五声徵调式最多" ✓). 粤 is 徵 + 羽 ("羽、徵、商调式" ✓).
- **Fourth leaps (±5 st):** highest among Han regions in 西北部高原 (0.13, the 信天游/花儿 fourth). 闽台 and
  西南多民族 are also high (0.14).
- **偏音 (fa/ti etc.):** 1–3% of duration in Han regions, but **12% in 新疆** (Uyghur/Kazakh non-pentatonic
  systems). 东北/西北 have slightly more 偏音 than 江浙/粤 (cf. "六、七声音阶为主" in 东北).

**Transcriptions are a different object:**
- 偏音 at 8–20% everywhere; 7–8 scale degrees in use vs ~5
- 12–40% of finals on non-pentatonic degrees
- fourth leaps only 0.05–0.07, with stepwise motion up

A transcription records the *performance*: 润腔 ornaments (滑音, 倚音, 波音), non-tempered intonation, glides
between skeleton tones, and transcriber errors. The chromaticized, stepwise surface hides the skeleton that a
collector's score writes down. That is the domain gap. The regional signal isn't absent from transcriptions (7× chance
on T15); it sits at a different level of the musical surface.

Only 新疆 keeps its identity across domains: the most 偏音 in both scores (12%) and transcriptions (20%). Its
distinctiveness is scale-level and survives any surface noise.

## 5. Representation families: overview (best macro-F1 per family, song-grouped folds)

| Family | Script(s) | A5 | E | T15 | T5 |
|---|---|---|---|---|---|
| chance (stratified) | `common.py` | 0.200 | 0.087 | 0.050 | 0.210 |
| theory features + GBM | `exp_theory.py` | 0.540 | 0.292 | 0.288 | 0.489 |
| per-region n-gram LMs | `exp_markov.py` | 0.515 | 0.346 | 0.266 | 0.378 |
| multi-viewpoint n-gram TF-IDF + LR | `exp_seq_ngram.py` | **0.619** | **0.363** | 0.352 | 0.500 |
| pretrained embeddings (CLaMP 3 C2 ⊕ theory) | `exp_pretrained.py` | 0.568 | 0.320 | 0.309 | 0.451 |
| rendered images (CNN fusion) | `exp_image_*.py` | 0.545 | 0.294 | 0.248 | 0.427 |
| **dual-view mixing** (n-gram surface ⊕ skeleton+scores) | `exp_fusion.py` | — | — | **0.369** | **0.514** |

Details of the sequence and image families are in §7 and §8, written from those agents' reports.

### 5.1 Pretrained symbolic embeddings, family "pretrained" (agent report, `emb_*.py`, `exp_pretrained*.py`)
Models tried as frozen encoders, followed by LR / RBF-SVM / kNN on the shared folds:
- **CLaMP 3 C2** symbolic encoder (MTF or interleaved ABC input). Best on its own: A5 0.524, E 0.307, T15 0.284,
  T5 0.423.
- **M3** (the CLaMP 2 encoder), comparable.
- **MusicBERT-style** (GigaMIDI REMI+BPE): A5 0.502, T15 0.264.
- **MuPT-190M** (an ABC LM): 0.15–0.35.
- **Qwen3-Embedding** on 简谱 degree strings: 0.15–0.26.
- **Concatenated C2 ⊕ theory features:** A5 0.568, E 0.320, T15 0.309. The embeddings add complementary information
  to the hand-made features.
- **Zero-shot CLaMP 3 with region/province text prompts:** at chance (A5 0.20, E 0.07). No evidence of memorized
  labels, even though Essen may be in its web-ABC pretraining data.

Probing what the embeddings encode (T15/E):
- **Recovered well:** register (mean pitch R² 0.9), length (0.99), interval size (0.75–0.87) and absolute key (90%).
- **Recovered poorly:** exactly the properties that define 色彩区: 偏音 content (R² 0.3–0.5) and modal final
  (near the majority baseline for M3/MusicBERT).

These are Western-trained "melodic surface" descriptors: they see contour, leap and rhythmic grain, but not the
五声 scale-and-mode system. Tonic normalization shifts the encoding toward musically meaningful content (mode-final
probe 0.22 → 0.34, key probe 0.52 → 0.19) without raising accuracy.

### 5.2 Fusion
Late fusion (mean probability) of n-gram LR + theory GBM: A5 0.620 (≈ n-gram 0.619), E 0.316 and T15 0.286, both
*below* n-gram alone. The GBM's overconfident probabilities dominate an unweighted average. Fusion needs calibration
or stacking to help; we didn't pursue it further, since the n-gram model already subsumes most theory-feature signal.

## 6. Data: cleaner, more diverse, mixed? (`exp_mixing.py`, `exp_reduce.py`, `exp_fusion.py dual`)
All rows in §6.1–6.3 use theory features + GBM, so only the data changes. §6.4 uses the n-gram model.

### 6.1 Cleaner vs noisier (T15)

| Training data | Macro-F1 |
|---|---|
| GAME primary transcriptions (all) | **0.270** |
| single-run GAME | 0.267 |
| ROSVOT transcriptions (the worse transcriber in the audit) | 0.219 |
| + ROSVOT versions of the training recordings (noise augmentation) | 0.257 (n-gram: 0.345 → 0.352) |
| top 50% by GAME–ROSVOT agreement | 0.205 |
| top 50% by critic ok-share | 0.192 |
| random 50% (control) | 0.177 |
| top 75% by agreement / by critic / random | 0.233 / 0.236 / 0.231 |
| 原生态 recordings only (~23/region) | 0.196 |
| stage (民族唱法 etc.) recordings only (~17/region) | 0.110 |
| learning curve, 25 / 50 / 75 / 100% of training data | 0.166 / 0.186 / 0.225 / 0.270 |

- **Transcription quality matters:** the transcriber our audit judged better also gives better classification.
- **At a fixed size, cleaner beats random** (+0.02–0.03 at 50%), but **quantity dominates.** The learning curve is
  still steep at 100%, so more recordings would help more than filtering.
- **原生态 recordings are the most informative training data.** Stage performances (民族唱法, arranged) are
  stylistically homogenized: conservatory vocal technique and orchestral accompaniment erase regional 润腔.

### 6.2 More diverse / mixed

| Target | + extra training data | Macro-F1 (target alone → mixed) |
|---|---|---|
| A5 | + T5 transcriptions | 0.540 → 0.547 |
| A5 | + Essen-5 | 0.540 → 0.547 |
| E | + T15 transcriptions | 0.292 → 0.308 |
| E | + Anthology | 0.292 → 0.270 |
| T5 | + Anthology (8.6k scores) | 0.489 → **0.350** |
| T5 | + Anthology, down-weighted to equal mass | 0.489 → 0.417 |
| T5 | + Anthology + source flag | 0.489 → 0.350 |
| T5 | + Essen-5 | 0.489 → 0.442 |
| T15 | + Essen | 0.270 → 0.258 (down-weighted 0.268) |
| T15 | + Essen + Anthology | 0.270 → **0.164** |

Mixing is asymmetric:
- **Clean-score targets gain a little from diverse extra data,** even from noisy transcriptions: more variety of the
  same skeletons.
- **The noisy performance target is hurt by clean scores,** and the more scores, the worse: the model learns a
  score-domain decision boundary. Down-weighting only softens this, and a source-indicator feature doesn't help.
- **E + Anthology hurts E.** Anthology's 5 regions are over-represented relative to E's 13, so its skeleton
  statistics pull E's minority regions toward Han decision regions.

### 6.3 Melodic reduction (performance → skeleton)

| Reduction level | T15 within-domain | T5 within-domain | Anthology → T5 | Essen → T14 | T5 + Anthology |
|---|---|---|---|---|---|
| raw | **0.270** | **0.489** | 0.223 | 0.069 | 0.350 |
| drop ornament notes | 0.212 | 0.418 | 0.187 | 0.088 | 0.373 |
| + merge repeats | 0.225 | 0.364 | 0.210 | 0.092 | **0.402** |
| + snap to 五声 | 0.211 | 0.290 | **0.283** | **0.104** | 0.355 |

Reduction makes performances more score-like: transfer and mixing improve. But it removes regional information that
lives in the performance surface, so within-domain accuracy drops sharply (T5 0.49 → 0.29).

**Musicologically, 润腔 is regional.** The literature treats ornamentation practice (滑音, 倚音, 波音, 甩腔,
颤音 types and densities) as a regional marker in its own right, alongside scale and mode. Our result is the
computational counterpart: the skeleton and the surface are *two layers* of regional identity, and scores only
record the first.

### 6.4 Dual-view: learn each layer from the data that has it
- **Surface view:** n-gram LR on raw transcriptions only.
- **Skeleton view:** n-gram LR on *reduced* transcriptions plus reduced scores, sources balanced.
- **Prediction:** the mean of the two views' probabilities.

| Training setup | T5 | T15 |
|---|---|---|
| surface only | 0.496 | 0.346 |
| naive mix (raw transcriptions + scores in one model) | 0.455 | 0.327 |
| skeleton view only | 0.449 | 0.346 |
| **dual-view** | **0.514** | **0.369** |

This is the right way to mix clean scores into a performance task. Scores contribute only at the level where the two
domains share structure (the skeleton), and the performance surface is modelled separately. It is the best result on
both transcription tasks.

### 6.5 Honesty check: channel-grouped folds
Transcriptions from the same YouTube channel share a singer, a recording chain and transcription artifacts. One
channel (中国音乐地图 / Rhymoi) supplies 11 regions and 50–83% of the minority regions.

| Model | T15 folds by song → by channel | T5 folds by song → by channel |
|---|---|---|
| theory + GBM | 0.270 → 0.181 | 0.489 → 0.476 |
| n-gram LR | 0.346 → 0.247 | 0.496 → 0.504 |
| CLaMP C2 (agent) | 0.284 → 0.178 | 0.423 → 0.396 |
| **dual-view** | **0.369 → 0.283** | **0.514 → 0.525** |

- **On T15, about 30% of song-grouped accuracy is channel leakage** or region depletion under channel grouping.
  Channel grouping is harsh: in some folds, a minority region loses most of its training recordings.
- **Dual-view stays best under the honest protocol.**
- **The n-gram model is the most channel-robust single model.** It keeps 71% of its score, vs 67% for theory features and 63%
  for embeddings.
- **T5 (Han regions with diverse channels) is unaffected.**
- We report both numbers. The true generalization to *new singers and channels* lies between them.

### 6.6 "Cleaner" transcriptions can be *less* informative: the 3-run GAME ensemble (`exp_ens3.py`)
The majority-vote ensemble of three GAME runs is the cleaner transcription by audit standards: 35% less run-to-run
noise, and vocadito COnP 0.587 → 0.600. We compared it on the same 591 recordings and the same folds (paired):

| Model | Single-run GAME | 3-run ensemble |
|---|---|---|
| theory + GBM | 0.267 | 0.248 |
| n-gram LR | 0.328 | 0.305 |
| dual-view | **0.377** | 0.353 |

The ensemble is ~0.02 *worse* for region classification under every model. Each difference is within seed noise, but
the direction is consistent.

Why: voting removes about 3% of notes, and the removed notes skew toward ornaments (short-note share 0.118 →
0.109). Notes a stochastic transcriber is unsure about are disproportionately 润腔 (short glides, grace notes).
Voting is a mild skeleton reduction, and §6.3 showed that the surface layer carries regional information.

**Lesson:** "cleaner" by transcription-accuracy standards (onset/pitch F1 against annotated notes) isn't the same
as "more informative" for stylistic analysis. The released dataset should keep both versions, the ensemble as the
primary melody and the single-run outputs as the ornament-rich surface.

## 9. Where do the models get confused, and why? (`analyze.py`)
Out-of-fold confusion matrices and per-region F1 are in `data/regionclf/analysis/`.

### 9.1 Confusion follows geography
For each region pair, we correlate the symmetric confusion rate with the great-circle distance between approximate
region centres (Spearman, with a permutation p-value over region labels).

| Model / task | ρ (confusion vs distance) | p |
|---|---|---|
| n-gram, E (13 regions, scores) | **−0.59** | 0.0002 |
| n-gram, T15 (transcriptions) | −0.36 | 0.0004 |
| dual-view, T15 | −0.32 | 0.002 |
| n-gram, A5 (only 10 pairs) | −0.26 | 0.24 (n.s.) |

Neighbouring regions are confused more, in both scores and performances. The classifiers recover a *geographic
continuum* of style rather than discrete boxes. That is what the 色彩区 literature itself says: region boundaries
are drawn through transition zones, and several regions are explicitly defined as transitional.

### 9.2 The most confused pairs match the literature's transition zones
- **江浙平原–江淮** (T15: 0.17–0.21, the most confused pair). The 色彩区 system defines 江淮 as the belt
  "由六、七声音阶向五声音阶过渡": the gradient between 东北's 6–7-note scales and 江浙's pentatonic 小调. It shares
  repertoire with 江浙 (扬州 茉莉花/鲜花调 variants), and the curation itself had to adjudicate 江苏 songs between the two.
- **东北部平原–江淮** (0.12–0.14): the other side of the same gradient. 苏北/徐州 is included in 东北 by definition.
- **客家特区–闽台** (0.12–0.14): Hakka heartland 闽西 (龙岩, 永定, 上杭) lies inside Fujian. Hakka 山歌 and 闽西 songs
  share dialect-driven melodic contours.
- **北方草原–藏族** (0.10–0.14): two pastoral traditions with free-rhythm, melismatic, wide-range long songs
  (蒙古长调, 藏族 牧歌/山歌). The model hears a shared "high-plateau pastoral" style.
- **Scores (Essen):** most confusions go *into* 西北部高原, the dominant class (1,068/2,189): 东北–西北 0.19,
  北方草原–西北 0.15. Imbalance plus genuine 北方 affinities (爬山调 in 内蒙古西部 is classed with 西北).

### 9.3 Which regions are distinctive?
Per-region F1 on T15 (dual-view):

| Region | F1 | Region | F1 | Region | F1 |
|---|---|---|---|---|---|
| 新疆 | **0.59** | 粤 | 0.47 | 客家 | 0.28 |
| 北方草原 | 0.57 | 东北 | 0.44 | 西南高原 | 0.27 |
| 藏族 | 0.56 | 西北 | 0.43 | 江淮 | 0.24 |
| 赣 | 0.47 | 江汉 | 0.40 | 江浙 | 0.19 |
| | | 西南多民族 | 0.34 | 湘 | 0.16 |
| | | | | 闽台 | 0.15 |

- **Minority song areas are the most recognizable,** in performances (新疆, 北方草原, 藏族 top three) and in scores
  (E: 西北 0.82, 新疆 0.79, 北方草原 0.61). Their distinctiveness is systemic: non-pentatonic scales in 新疆 (§4:
  12–20% 偏音), and free-rhythm long-song phrasing in 北方草原/藏族. Only 20% of predictions cross the Han/minority
  boundary on T15, and 5.5% on E.
- **Some caution for 藏族 and 西南多民族:** 75–83% of their recordings come from one channel, so part of their
  recognizability in T15 may be the channel (§6.5).
- **The hardest Han regions are the "soft-boundary" ones.** 江浙 is the archetypal pentatonic 小调 region, whose
  melodic material has diffused widely (茉莉花, 孟姜女 families appear everywhere). 湘 and 闽台 lie between larger
  neighbouring styles.
- **Paradox for 江浙 and 西南高原:** they are distinctive in scores (A5 F1: 粤 0.70, 东北 0.70, 江浙 0.64, 西南
  0.56, 江汉 0.49) but not in performances. Their regional identity is carried more by skeleton melody than by
  performance style, which is consistent with 江浙's smooth, lightly ornamented 小调 singing.

### 9.4 Negative result: hierarchical Han/minority → region (`exp_hier.py`)
Stage 1 (Han vs minority) reaches 82% accuracy (75% channel-grouped). But the two-stage model is worse than flat
(T15 0.322 vs 0.346; channel-grouped 0.228 vs 0.247). With 27% minority recordings, stage-1 errors are
unrecoverable, while the flat model already respects the boundary in its errors (only ~20% cross-boundary
confusions). The Han/minority distinction is real, but a hard gate adds error rather than removing it.

## 8. Rendered images, family "image" (agent report, `exp_image_*.py`)
**Renderings.** All are tonic-normalized, tempo-free, and sampled as 4 windows per score and 8 per transcription:
- piano roll
- contour line
- "简谱" degree × time (3 octave channels)
- self-similarity matrix
- whole-song interval-transition heatmaps ("itrans")
- MFDMap (Khoo, Man & Cao 2012–13)

**Models:**
- frozen DINOv2-S/14, CLIP ViT-B/32 and ResNet-50, with crops mean-pooled and logistic regression
- CNNs from scratch, with late fusion across renderings
- fine-tuned ResNet-18
- ELM / R-ELM for MFDMap

| Experiment | A5 | E | T15 | T5 | Essen Han-5 (prior-work set) |
|---|---|---|---|---|---|
| theory + GBM (reference) | 0.540 | 0.292 | 0.270 | 0.489 | 0.539 |
| **CNN fusion, itrans + 简谱** | **0.545** | **0.294** | 0.233 | 0.427 | 0.523 |
| CNN fusion + roll | – | – | 0.246 | 0.427 | **0.550** |
| CNN 简谱 | 0.495 | 0.251 | **0.248** | 0.340 | 0.504 |
| frozen backbones (best combination) | 0.481 | 0.291 | 0.237 | 0.339 | 0.470 |
| fine-tuned ResNet-18 | – | – | – | 0.292 | 0.429 |
| MFDMap from corpus notes (R-ELM) | 0.501 | 0.247 | 0.245 | 0.306 | 0.47–0.49 |

- **Images tie the theory features on scores and lose on transcriptions.** The best renderings (itrans, 简谱) are
  pictures of the same interval and degree-transition statistics the features already contain.
- **General-purpose vision backbones (DINOv2, CLIP) add nothing over small CNNs.** Natural-image priors don't
  transfer to music renderings.
- **Self-similarity matrices (phrase and repetition structure) are the weakest rendering** (0.12–0.32). Repetition
  structure is not regional: most regions use 2- or 4-phrase strophic forms.
- **Prior-work comparison, corrected.**
  - MFDMap is by Khoo, Man & Cao (Swinburne; ICSPCS 2012, R-ELM 72%; AI 2012, FIR-ELM 80.65%; thesis 2013, up to
    85.6%). The *84.7% CRF-RBM* number (Li et al., MTAP 2018) is on *audio*, so it isn't comparable.
  - A faithful MFDMap replication on Essen Han-5, under their random 10-fold accuracy protocol, gives **53–55%**.
    Theory features + GBM give 56.7%.
  - The ~20-point gap isn't explained by encoding, classifier or protocol, and is most likely their exact 333-song
    selection plus best-of-grid reporting.
- **Saliency (Grad×input on 简谱/itrans CNNs):**
  - 江浙: sol and mi, and the (+3,+2) / (−2,−3) interval pairs, i.e. the **mi–sol–la / la–sol–mi** three-note
    pentatonic cell of southern 小调.
  - 粤: re and mi, and the (±2,∓2) neighbour-note oscillation.
  - Shanxi (西北): (−5,−2), a **falling fourth then a step**, the northwestern fourth idiom.
  - 西南 (Sichuan): la, with (+3,−3) and (−2,−3) minor-third figures, i.e. **羽-mode colour**.
  - 新疆 (T15): fa ×1.77 and salient semitones, i.e. heptatonic, non-pentatonic.
  - 赣 / 客家: la.
  - Cadence matters most: on Essen, the *final* window of a song is the most regional (crop accuracy 0.58 vs 0.48 for
    the opening), consistent with 落音 / cadence formulae carrying regional identity.

## 7. Tokenization + sequence models, family "sequence" (agent report, `exp_seq_*.py`)
**Vocabularies** (`exp_seq_tok.py`), all 宫-relative and tempo-relative:
- int, deg, degoct (degree + register), degdur, intdur, dur, contour, cad (phrase-final 落音)
- abs (non-normalized, as a control)
- MidiTok REMI / TSD / Structured, with and without BPE (1k/4k)

| Experiment | A5 | E | T15 | T5 |
|---|---|---|---|---|
| **n-gram 1–4, all 7 vocabs, TF-IDF + LR** | **0.619** | **0.363** | **0.345** | **0.500** |
| n-gram intdur 1–3 (best single vocab) | 0.577 | 0.314 | 0.301 | 0.425 |
| n-gram int 1–4 | 0.515 | 0.324 | 0.294 | 0.398 |
| n-gram deg 1–4 | 0.488 | 0.284 | 0.230 | 0.360 |
| n-gram contour 1–4 | 0.435 | 0.259 | 0.238 | 0.395 |
| n-gram dur 1–4 (rhythm only) | 0.352 | 0.150 | 0.152 | 0.250 |
| n-gram abs 1–4 (not key-normalized) | 0.495 | 0.239 | 0.175 | 0.233 |
| MidiTok, best of REMI/TSD/Structured ± BPE | 0.580 | 0.294 | 0.216 | 0.386 |
| CNN from scratch (factored note embeddings) | 0.526 | 0.222 | 0.186 | 0.322 |
| BiGRU / Transformer from scratch | – / – | – / 0.224 | 0.194 / 0.198 | 0.386 / 0.342 |
| Transformer + masked-note pretraining (11.8k songs), fine-tuned | 0.509 | 0.242 | 0.194 | 0.364 |
| k-NN, edit distance on degree strings | 0.406 | 0.170 | 0.129 | 0.324 |

- **Short motifs carry the signal.** Unigrams are weak, 1–2-grams jump, and 1–3/1–4 is best (3–5 alone is worse).
  In musical terms, regional style lives in **2–4-note 音调 cells**, as in the Markov results (§3.2).
- **Pitch × rhythm tokens are the strongest single vocabularies** (intdur, degdur). Pooling complementary
  viewpoints adds +0.03–0.05. That is the multiple-viewpoint principle again.
- **Intervals beat degrees on transcriptions and Essen.** 宫 estimation is noisy on sung pitch, and transcription
  degree streams are full of chromatic ♯宫/闰.
- **Key normalization is essential** for transcriptions (abs: T15 0.175 vs 0.345) and matters less for the 1=C
  Anthology.
- **Neural models lose to n-grams by 0.09–0.16.** Pretraining didn't help, even though the pretraining corpus
  included the unlabeled test songs, which would favour it. At 600–9k songs, a linear model over explicit motif
  counts is the better inductive bias.
- **MidiTok vocabularies are worse than the custom ones,** and BPE doesn't change that. Generic
  Western-performance tokenizations (bars, velocities, absolute pitch) spend capacity on things that aren't
  regional here.
- **Caveat:** the vocabulary mix, n and C were chosen on the same folds that are reported, which is mild optimism.
  The later fusion and dual-view runs reused the recipe without further tuning.

**Most discriminative n-grams** (top LR coefficients, degree/interval vocabularies), with a musicological reading:
- **粤:** 徵-宫-商, 徵-商-羽, **清角-角-商, 变宫-商-商**. 偏音 fa and ti prominent: the 广东 **乙反调**
  (乙 = si/变宫, 反 = fa/清角) colour, a textbook 粤 marker.
- **江浙平原:** stepwise 商-商-宫, 徵-角-宫, 徵-羽-宫; intervals +2+2+3 / +2+3+2 with short durations. Smooth,
  lightly ornamented stepwise 小调 lines cadencing on 宫, the same in Anthology and Essen.
- **东北部平原:** 清角, 羽-清角-角, 宫-商-变宫, and falling minor sixths (−8). Six- and seven-note scales and 大跳,
  exactly "六、七声音阶为主".
- **江汉:** 清角-宫, 徵-清角-宫, and 4th/5th leaps followed by stepwise descent (+5−5−2). 六声 scales with 清角
  (湖北).
- **西南高原:** 宫-羽 / 羽-宫 minor thirds, 商-宫-羽, and long 羽. 羽-mode colour.
- **北方草原 (Essen):** octave and sixth leaps (−12, −9, +3−12), 角-徵-羽. The wide-range 长调.
- **新疆 (Essen):** semitones ±1, 变宫-宫, 角-清角. Heptatonic, maqam-like semitone steps.
- **西北部高原 (Essen):** 变宫-羽, −1−2 descents, 徵 and 商 unigrams. 偏音 in falling cadences around the 徵–商
  fourth frame.
- **T15:** many top n-grams involve chromatic degrees (♯徵, 闰). These are likely intonation and transcription
  artifacts, which is the same chromaticization seen in §4.

## 10. Robustness: fresh folds (`exp_seed.py`)
The n-gram recipe was selected on the seed-0 folds, so we re-evaluated it, unchanged, on grouped folds with seeds 1 and 2.

| Model / task | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| n-gram, A5 | 0.619 | 0.620 | 0.617 |
| n-gram, E | 0.363 | 0.364 | 0.355 |
| n-gram, T15 | 0.346 | 0.307 | 0.345 |
| n-gram, T5 | 0.496 | 0.527 | 0.452 |
| **dual-view, T15** | **0.369** | **0.346** | **0.366** |

- **No selection optimism on the score tasks.** Numbers are identical within ±0.005.
- **Transcription tasks have seed variance of ±0.02 (T15) and ±0.04 (T5),** because each region has only 40
  recordings (8 per test fold). Single-number comparisons below ~0.03 on T tasks are within noise.
- **Dual-view beats the plain n-gram model on T15 in every seed** (+0.02 to +0.04), so the gain is consistent.

---

## 11. Synthesis

### 11.1 What works best

| Task | Best method | Macro-F1 (song-grouped) | Honest (channel-grouped) | Chance |
|---|---|---|---|---|
| A5, Anthology scores, 5 regions | multi-viewpoint n-gram TF-IDF + LR | **0.62** | – | 0.20 |
| E, Essen scores, 13 regions | multi-viewpoint n-gram TF-IDF + LR | **0.36** | – | 0.09 |
| T15, our transcriptions, 15 regions | dual-view (n-gram surface ⊕ n-gram skeleton + Essen scores) | **0.37** (0.35–0.37 over seeds) | **0.28** | 0.05 |
| T5, transcriptions, 5 regions | dual-view | **0.51** | **0.53** | 0.21 |

Ranking of representation families: **explicit multi-viewpoint motif counts** > theory features ≈ CLaMP 3
embeddings (+ theory) ≈ rendered-image CNNs > per-region Markov LMs (best on E among early methods) > neural sequence
models from scratch or pretrained > generic tokenizers (MidiTok) > text/ABC LLM embeddings.

### 11.2 Exploration → exploitation: what we learned about *representation*
1. **Relative, musically-informed abstraction beats generic encodings.**
   - The winners are all tonic-relative (宫) and tempo-relative.
   - Absolute-pitch encodings lose sharply on performances (0.175 vs 0.345), because register is singer identity,
     not region.
   - Generic MIDI tokenizers (MidiTok), Western-trained symbolic LMs (MuPT, MusicBERT) and natural-image vision
     backbones all underperform simple 五声-aware vocabularies.
2. **Multiple viewpoints.**
   - Pitch-only, interval-only, rhythm-only and contour-only views are each weak.
   - Their combination, especially the joint pitch×duration tokens, is consistently best. This reproduces the
     multiple-viewpoint argument (Conklin & Witten) on a new repertoire.
   - On noisy data, the *coarsest* viewpoints (contour, interval) degrade least.
3. **The unit of regional style is the short motif.**
   - In every sequence family, orders 2–4 beat unigrams, and beat longer contexts alone.
   - This is the computational counterpart of the 音调 / 核心音调 concept: a regional style is recognized by a
     small inventory of characteristic 3–4-note cells rather than by global statistics or long-range form.
   - The discriminative cells match textbook descriptions:
     - 西北: falling fourth + step
     - 江浙: mi–sol–la stepwise cell
     - 粤: 乙反 (fa/ti) turns
     - 东北: 清角 and 大跳
     - 西南: 羽–宫 minor third
     - 新疆: semitone steps
4. **At 600–9k songs, count-based linear models beat deep models,** whether from scratch, pretrained, or frozen
   foundation encoders. Frozen encoders help only as a complement to explicit features (CLaMP ⊕ theory: A5 0.568).

### 11.3 What we learned about *data*
1. **Clean vs noisy.** Clean scores are far easier (A5 0.62 on 5 classes) than transcriptions (T5 ≈ 0.5 on the same 5
   regions). At equal size, a cleaner subset of transcriptions beats a random one (+0.02–0.03). But quantity beats
   filtering, and the learning curve is still rising, so **more recordings would help more than stricter filtering.**
   Better transcription helps: the transcriber our audit rated higher (GAME) gives 0.27 vs 0.22 for ROSVOT. But
   "cleaner" isn't always better: the 3-run GAME ensemble, cleaner by audit standards, is ~0.02 worse because voting
   trims ornaments (§6.6).
2. **Diverse and mixed.**
   - Mixing is asymmetric.
   - Clean-score tasks gain slightly from any extra data, including noisy transcriptions (+0.01–0.02).
   - Performance tasks are *hurt* by naively added scores, and the more scores the worse (T5 0.49 → 0.35 with 8.6k
     Anthology scores). Re-weighting and domain flags only soften this.
3. **Two layers of regional identity.**
   - Melodic reduction (dropping ornaments, merging repeats, snapping to 五声) makes transcriptions score-like and
     improves transfer, but costs within-domain accuracy (T5 0.49 → 0.29).
   - Regional identity therefore lives in **two layers**: the *skeleton* (骨干音: scale, mode, motif cells), which
     scores and performances share, and the *surface* (润腔: ornament density and type, glides, rhythmic
     elasticity), which only performances have.
   - **Dual-view learning** respects this: a skeleton model trained on scores plus reduced transcriptions, and a
     surface model trained on raw transcriptions only. It is the one way of mixing clean and noisy data that helps
     on every seed. This is the main methodological answer to "what happens if we mix datasets?".
4. **Transfer.** Score ↔ score transfer works (Anthology → Essen 0.45 on 5 regions), which supports the idea that
   these are real regional styles rather than one collection's editorial habits. Score → performance transfer is near
   chance (0.22), and it becomes useful only after skeleton reduction (0.28), for the reason above.
5. **Leakage and confounds matter.**
   - Grouping by song is necessary: same-title variants recur within and across sources.
   - For transcriptions, grouping by channel removes ~30% of T15 accuracy. Singer, recording chain and channel
     identity are learnable and partly aligned with region, because one channel supplies most minority-region
     recordings.
   - Honest T15 accuracy is ~0.28 macro-F1: 5.6× chance, but far from solved.

### 11.4 A computational-musicology reading
- **The 色彩区 map is recoverable from notes alone,** most clearly from scores. Model errors are *geographic*
  (Spearman ρ between confusion and distance: −0.59 on Essen, −0.32 to −0.36 on transcriptions). The most confused
  pairs are exactly the literature's transition zones: 江淮 ↔ 江浙/东北, 客家 ↔ 闽台 (闽西), and 北方草原 ↔ 藏族
  (pastoral long song). Style varies as a *continuum with cores*, as 江明惇's map itself implies.
- **The strongest boundaries are systemic, not local.** Minority song areas are the most recognizable: 新疆 F1 0.59–0.79
  (heptatonic, semitone-rich), and 北方草原/藏族 (wide-range, free-rhythm long song). Only 5–20% of errors cross the
  Han/minority line.
- **Among Han regions, identity is a matter of dialects of one pentatonic language.** Modes (徵 dominant in the
  north and center, 羽 in the southwest and among minorities), 偏音 use (东北/江汉 清角, 粤 乙反) and a handful of
  motif cells distinguish them, and these are learned consistently from two independent score collections.
- **Performance practice is regional too.** The accuracy lost when ornaments are removed from performances (T5
  0.49 → 0.29) measures, indirectly, how much regional identity lies in 润腔 and other surface traits. Per-region
  surface-vs-skeleton contributions were not measured and are a natural next analysis. So is separating genuine 润腔
  from channel and recording traits, which also live on the surface (§6.5).
- **Stage performances (民族唱法) are stylistically homogenized.** A model trained only on them is much worse than one
  trained on 原生态 recordings (0.11 vs 0.20). The conservatory singing style and arranged accompaniment erase
  regional markers. That is a caution for any dataset built from popular "folk song" videos.

### 11.5 Limitations and next steps
- **Sample size:** transcriptions have 40 per region (seed variance ±0.02–0.04). The learning curve says more
  recordings is the highest-value next step.
- **Mismatched scales:** Anthology covers only 5 regions and Essen is 49% 西北, so the score tasks don't span all
  15 regions.
- **Channel confound:** diversify channels for the minority regions before trusting their per-region numbers.
- **Audio-level surface features:** 润腔 is better captured from F0 than from notes. §6.6 shows that note-level
  transcription systematically trims it.
- **Stacking:** calibrated stacking of n-gram, theory and CLaMP views might add a little. Unweighted late fusion
  didn't.

---

# Part II — Reviewer-driven follow-up (2026-10-01)

## 12. Self-review: what a critical reviewer would ask
We reviewed Part I as a reviewer at a top ML venue would, and list the concerns before running anything. Each is
addressed in §13–§19; the status column is filled at the end (§20).

| # | Concern | Why it matters | Planned response |
|---|---|---|---|
| R1 | **No uncertainty estimates.** Differences of 0.02–0.04 on 600 items are claimed without CIs or tests. | Several conclusions (dual-view > n-gram, ensemble < single-run, cleaner > random) may be noise. | Bootstrap CIs and paired permutation tests for every headline comparison (§13). |
| R2 | **Anthology→transcription transfer was tested only with theory+GBM,** and without any domain adaptation. | "Transfer fails" may just mean "this model fails". | Transfer with the best representation, plus standard domain-adaptation baselines: label-shift correction, CORAL, score-side noise augmentation, few-shot target data (§14). |
| R3 | **Is the gap the transcriber or the music?** Transcriptions differ from scores both by transcription error and by performance practice. | Decides whether better transcription could close the gap. | Render Anthology scores to audio and push them through the *same* transcription pipeline. The result has transcriber noise without performance practice (§15). |
| R4 | **Same-song evidence.** 109 recordings share a title with an Anthology score. | A direct, paired test of whether transcriptions keep the melody that the scores classify on. | Song-identity retrieval (transcription → its own score) and paired region predictions (§14). |
| R5 | **Dual-view ablations.** Is the gain from the external scores, or just from ensembling two views of the same data? | The central "how to mix data" claim depends on it. | Skeleton view without scores; reduction level; source weights; each score source separately; fusion weight (§16). |
| R6 | **Shortcut confounds.** Channel, recording length, note density, performance type, and in the Anthology region ≡ volume ≡ editor. | Classifiers may learn collection artifacts. | Metadata-only shortcut baselines; volume-vs-volume discrimination within one province; length-matched evaluation (§17). |
| R7 | **Validity of intermediate steps.** 宫 (tonic) estimation is used everywhere but never validated. Near-duplicate songs under different titles could leak across folds. | Error propagation, and leakage. | Validate 宫 against known tonics (Anthology 1=C, Essen key signatures); melodic near-duplicate audit across folds (§17). |
| R8 | **Label validity and clustering.** Is the 色彩区 partition what the data supports? Would provinces or a coarser North/South split be more learnable? Does unsupervised structure recover the regions? | Classification of an imposed taxonomy says nothing about whether the taxonomy is natural. | Unsupervised clustering (NMI/ARI), hierarchical clustering of region profiles vs geography and vs the 色彩区 map, and learnability of alternative label sets (§18). |
| R9 | **Unequal tuning across families.** The n-gram model was tuned on the test folds, while neural models may be under-trained. | Unfair comparison. | Nested CV for the main linear models; state the neural-training budget honestly (§19). |
| R10 | **Scope.** Two score collections cover only 5 and 13 regions; transcriptions have 40/region from YouTube. | Generalization claims. | Discussed as limitations; per-region learning curves (§19–20). |

## 17. Confounds and validity (R6, R7): `rev_confounds.py`

### 17.1 Shortcut baselines on T15: the song-grouped transcription numbers are confounded
Region predicted *without any melody*, song-grouped folds:

| Features | Macro-F1 (T15, chance 0.05) |
|---|---|
| metadata only (duration, #notes, notes/s, vocal dB, performance type, upload year), GBM | 0.220 |
| **channel identity only** (one-hot YouTube channel), LR | **0.343** |
| metadata + channel, LR | **0.368** |
| *for reference: n-gram melody model / dual-view* | *0.346 / 0.369* |

**The channel alone does as well as the melody models under song-grouped folds.** This is the most important
correction to Part I. The song-grouped T15 numbers (0.35–0.37) *cannot* be read as evidence of melodic learning.
They are an upper bound contaminated by channel identity, since recordings from one channel cluster by region.

Two controls show that the melodic signal is nonetheless real:
1. **Channel held constant.** Classify region only among the 174 recordings from the one channel (中国音乐地图 /
   Rhymoi) that spans many regions: 9 regions with ≥8 recordings, chance ≈ 0.11, song-grouped folds.

   | Model | Macro-F1 |
   |---|---|
   | **n-gram melody model** | **0.437** |
   | metadata only (duration, #notes, notes/s, vocal dB) | 0.308 |

   With the channel fixed, melodies still identify the region at ~4× chance, well above the metadata. Some metadata
   is itself musical, e.g. note density reflects syllabic vs melismatic singing and 号子 vs 长调.
2. **Channel-grouped folds.** Metadata-only collapses to 0.093 (≈ chance), so the metadata shortcut was mostly a
   channel proxy. The melody models keep 0.25–0.28 (§6.5).

**Revised headline for transcriptions:** use channel-grouped folds. Dual-view reaches 0.283 (T15) and 0.525 (T5),
and within-channel accuracy is 0.437 (9 regions). The song-grouped 0.37 overstates it.

### 17.2 宫 (tonic) estimation is accurate enough
| Source | Check | Accuracy |
|---|---|---|
| Anthology (简谱 rendered 1=C) | estimated 宫 = C | **91.8%** |
| Essen | estimated 宫 = do of the kern key signature | **88.2%** (n = 2,187) |
| Transcriptions | GAME vs ROSVOT transcriptions of the same recording give the same 宫 (chance 8%) | **79.0%** |

All Anthology errors are fifth or fourth displacements: 宫 estimated on 徵 (376 songs) or 清角 (334). That is the
inherent ambiguity of pentatonic collections, where do–re–mi–sol–la on C shares four notes with the collection on G.
Degree-based vocabularies inherit ~10% tonic noise on scores and ~20% on transcriptions. This is one reason
interval vocabularies, which need no tonic, are more robust on transcriptions (§7).

### 17.3 The Anthology's editorial units: volumes are partly separable, and leave-one-volume-out is much harder
Region ≡ set of province volumes in the Anthology, and each volume had its own editors. Can the model tell volumes apart?

| Test (n-gram, grouped CV) | Macro-F1 | Chance |
|---|---|---|
| Hebei vol. 1 vs vol. 2 (same province) | 0.584 | 0.50 |
| Jiangsu vol. 1 vs vol. 2 (same province) | **0.721** | 0.50 |
| province within 东北部平原 (Hebei / Tianjin / Jilin) | 0.644 | 0.33 |
| province within 江浙平原 (Jiangsu / Shanghai) | 0.717 | 0.50 |
| lyrics-included vs melody-only subset (confounded: lyrics subset = Guangdong + Jiangsu only) | 0.697 | 0.50 |

**Leave-one-volume-out** (`review_leave_volume_out.csv`): train on everything except one volume (and same-title
songs), test on that unseen volume.

| Held-out volume | Region | n | Accuracy, unseen volume | Accuracy, grouped CV (same songs) |
|---|---|---|---|---|
| hebei1 | 东北 | 513 | 0.704 | 0.768 |
| hebei2 | 东北 | 687 | 0.549 | 0.659 |
| tianjin | 东北 | 598 | 0.518 | 0.701 |
| jilin | 东北 | 865 | **0.353** | 0.729 |
| jiangsu1 | 江浙 | 788 | 0.458 | 0.637 |
| jiangsu2 | 江浙 | 636 | 0.451 | 0.610 |
| shanghai | 江浙 | 831 | 0.391 | 0.665 |
| guangdong | 粤 | 1,070 | **0.273** | 0.690 |
| hainan | 粤 | 959 | 0.389 | 0.756 |
| **weighted** | | 6,947 | **0.431** | **0.691** |

**This is the largest correction on the score side.** Anthology A5 accuracy in the standard grouped CV is inflated
by volume-level signatures: a model that has seen other songs from the same volume does much better than one facing
an unseen volume (0.69 vs 0.43; 5-class chance accuracy ≈ 0.2–0.3). Two readings, not mutually exclusive:
1. **Editorial / OMR signatures.** Each provincial editorial team had its own transcription and notation habits
   (e.g. how it notated grace notes and rhythm), plus volume-specific OMR errors.
2. **Real sub-regional style.** The 色彩区 is coarser than the stylistic granularity of the data.
   - Jilin (Manchurian 东北 with 二人转 influence) differs from Hebei.
   - Hainan and Guangdong are different provinces with different dialects (海南话 vs 粤语).
   - Jiangsu's two volumes likely differ in genre make-up (号子/山歌 vs 小调).
   - Held-out *regions within a volume* transfer best where provinces are culturally closest: hebei1 (0.70) when
     trained with hebei2/tianjin.

Either way, **the defensible claim is "region transfers to an unseen collection at ~2× chance", not "0.62 macro-F1".**
The Essen results (a different collection altogether, §3.3: Anthology → Essen-5 0.45) are consistent with that.

### 17.4 Length and near-duplicates
- **Length matters, and is not a shortcut.**
  - Truncating songs to their first N notes: Anthology 16 → 0.42, 32 → 0.52, 64 → 0.59, 128 → 0.61, full 0.62.
    Transcriptions 16 → 0.12, 32 → 0.18, 64 → 0.23, 128 → 0.25, full 0.35.
  - Scores saturate after ~64 notes (≈ one or two strophes), while performances keep improving over their full length
    (≈400 notes): noisy material needs more evidence.
  - Song length alone predicts Anthology region only at 0.24 (chance 0.20).
- **Near-duplicates are negligible.** 78 Anthology songs (0.9%) have a near-identical melody (cosine ≥ 0.9) under a
  different title in another fold. Removing them from the test set changes nothing (0.617 vs 0.619).

## 13. Uncertainty for the headline claims (R1): `rev_stats.py`
We computed out-of-fold predictions for fold seeds 0/1/2, pooled them (items × seeds), and report 95% bootstrap CIs
(2,000 resamples) and a paired permutation test (10,000 random swaps of the two models' predictions per item).
Full table: `data/regionclf/review_stats.csv`.

| Comparison (A vs B) | F1 A [95% CI] | F1 B [95% CI] | Δ [95% CI] | p |
|---|---|---|---|---|
| T15: dual-view vs n-gram | 0.360 [0.339, 0.380] | 0.333 [0.313, 0.353] | **+0.027 [+0.010, +0.044]** | **0.003** |
| T15: n-gram vs theory + GBM | 0.333 [0.313, 0.353] | 0.258 [0.237, 0.276] | **+0.076 [+0.052, +0.099]** | **<0.001** |
| T15: n-gram vs naive mix + Essen | 0.333 | 0.330 | +0.003 [−0.017, +0.023] | 0.76 |
| T5: dual-view vs n-gram | 0.523 [0.482, 0.560] | 0.492 [0.451, 0.530] | +0.031 [−0.004, +0.065] | 0.07 |
| T5: n-gram vs naive mix + Anthology + Essen-5 | 0.492 | 0.455 | +0.037 [−0.008, +0.081] | 0.12 |
| A5: n-gram vs theory + GBM (seed 0) | 0.619 [0.607, 0.630] | 0.540 [0.527, 0.552] | **+0.079 [+0.066, +0.092]** | **<0.001** |
| T15 n-gram: single-run GAME vs 3-run ensemble transcriptions | 0.322 [0.301, 0.343] | 0.298 [0.277, 0.317] | **+0.025 [+0.008, +0.041]** | **0.004** |
| T15 dual-view: single-run vs ensemble transcriptions | 0.358 | 0.341 | +0.017 [+0.001, +0.034] | 0.051 |

What survives:
- **Dual-view > n-gram on T15 (significant),** and **n-gram > theory features (highly significant, on both T15
  and A5).**
- **"Cleaner" ensemble transcriptions are less informative** than single-run ones (§6.6): significant under
  n-gram, borderline under dual-view.
- **T5 comparisons point the same way but aren't significant.** Only 200 items; the dual-view gain and the harm from
  naive mixing are both p ≈ 0.07–0.12.
- **With n-gram models, naive mixing with Essen is neutral on T15** (Δ +0.003). The strong harm from naive mixing
  reported in §6.2 was measured with theory+GBM, where the 8.6k scores dominate. With the linear n-gram model the
  harm is smaller and not significant. **Revised claim:** naive mixing doesn't help, and hurts when the extra data
  dwarfs the target (T5 + 8.6k Anthology). Dual-view is the only mixing scheme with a significant gain.

## 21. Song dating and first look at change over time (requested 2026-10-01)
**Goal:** track how regional elements evolve as regions influence each other. That needs dates, so three research
agents dated every distinct song in the 600-recording dataset: 503 songs, 5 regions per agent.
- **Sources:** Baike, 非遗/UNESCO listings, academic papers, record discographies.
- **Rule:** never invent a date. Legends and genre-level antiquity go in notes, not in the date columns.
- **Constraint:** the session's shared web-search budget (200 calls) ran out near the end, so a few 粤/闽台 songs
  have thinner evidence (flagged `low`).

**Files:**
- `data/regions_curated/song_dates/<region>.csv`
- merged: `all_songs.csv`
- joined to the index: `data/regions_transcription/dataset_index_dated.csv` (columns `song_type`, `origin_period`,
  `earliest_attestation_year`, `composer_or_adapter`, `composition_or_adaptation_year`, `date_best`,
  `evidence_urls`, `confidence`, `dating_notes`)
- generators: `src/secaiqu/dating/`

| song_type | Songs |
|---|---|
| traditional (anonymous, orally transmitted) | 428 |
| traditional-adapted (known collector/arranger/new lyrics) | 41 |
| newly-composed-folk-style (known composer) | 17 |
| unknown | 17 |

**Only 90 songs (18%) have a documentable year** (`date_best`). The dates cluster in **1930s–1960s** (1930s: 9,
1940s: 13, 1950s: 31, 1960s: 16): the era of collection, arrangement and state-sponsored composition, not of
origin. The earliest attestations are genre or tune families: 茉莉花/鲜花调 1756–1767 (《缀白裘》), 凤阳花鼓 1767,
槐花几时开 lyrics in a Guangxu-era print, and 鸿雁's melody attributed to Mergen Gegen c. 1750.

**Findings that matter for the dataset:**
- **Several canonical "民歌" are modern compositions:** 浏阳河 (1950–51), 洪湖水浪打浪 (1958), 十送红军 (1960–61),
  映山红 (1973–74), 挑担茶叶上北京 (1960), 沂蒙山小调 (1940 propaganda song on a 花鼓调), 圪梁梁 (1981), 回娘家
  (a 1982 Taiwanese pop song relabelled "河北民歌" in 1984), and 望春风/雨夜花 (邓雨贤 1933/34).
- **Famous minority "folk songs" are arrangements:** 王洛宾's 1938–39 Xinjiang songs, and 燕子 (Zhubanov 1944 →
  吴祖强 1954).
- These should be flagged or excluded when a study needs *traditional* repertoire. The index now allows that.

**First analysis: are modern songs less regionally distinctive?** Mean out-of-fold accuracy on T15 over 3 seeds
(chance 0.067):

| song_type | n recordings | dual-view | n-gram |
|---|---|---|---|
| traditional | 485 | 0.358 | 0.362 |
| traditional-adapted | 71 | 0.521 | 0.376 |
| newly-composed-folk-style | 27 | **0.272** | **0.148** |

Newly composed folk-style songs are the least recognizable region-wise under both models. That fits a
**homogenization** reading: post-1949 composers wrote in a pan-national "民歌" idiom drawing on several regional
sources (e.g. 十送红军 on 赣南 长歌; 洪湖水 on 天门/沔阳 tunes plus opera). The evidence is weak: n = 27, and
traditional vs (adapted + new) isn't significant (p = 0.06 and 0.34). Adapted songs show no consistent effect.

**Limits for "evolution over time":** with 82% of songs undatable and most dates being 20th-century
*attestations*, song-level dating can't support a longitudinal study of pre-modern style change. Feasible
alternatives:
1. **Recording date as time.** Our recordings span decades of upload and performance (1950s archival to 2020s). Style
   drift in *performance practice* (润腔 density, tempo, range) can be tracked against recording year.
2. **Collection-date layers of the score sources.** Essen (Chinese source books of the 1950s–80s) vs the Anthology
   (collected 1950s–80s, published 1990s–2000s), and early 20th-century printed songbooks where available.
3. **Diffusion via shared tune families.** The same tune (茉莉花, 孟姜女, 绣荷包 …) appears across regions, and
   comparing regional variants of one family shows which elements localize (mode, 偏音, cadence) and which travel
   intact. This is the classical approach to regional influence (tune-family analysis) and needs no absolute dates.

## 19. Tuning fairness (R9): nested cross-validation (`rev_nested.py`)
The n-gram recipe (vocabularies, n, C) was selected on the reported folds. Nested CV re-selects C ∈ {0.3…30} and,
for transcriptions, the vocabulary subset {all7, core4, robust3} on inner grouped 3-folds of each outer training set.

| Task | Fixed recipe (Part I) | **Nested** | Optimism |
|---|---|---|---|
| A5 | 0.619 | **0.619** | 0.000 |
| E | 0.363 | **0.365** | 0.000 |
| T15, song-grouped | 0.346 | **0.335** | 0.011 |
| T15, channel-grouped | 0.247 | **0.239** | 0.008 |
| T5 | 0.496 | **0.463** | 0.033 |

Selection optimism is nil on the score tasks and 0.01–0.03 on the small transcription tasks, where the inner
selection sometimes picks `core4` instead of `all7`. **The nested numbers are the ones to cite.** On neural
baselines: the from-scratch and pretrained sequence models (§7) had early stopping and a fixed small architecture
search, not an equal-budget sweep. Their 0.09–0.16 deficit is large enough that under-tuning is an unlikely full
explanation at these data sizes, but this is a known caveat.

## 18. Is the 色彩区 taxonomy natural? Clustering and label validity (R8, agent report; `rev_cluster*.py`)
Outputs: `data/regionclf/review/`. Figures: `notebooks/figures/regionclf_dendrogram_*.png`,
`regionclf_cluster_sweep.png`, `regionclf_labels_null_{A,E}.png`.

### 18.1 Songs don't cluster into regions
k-means, Ward and GMM on theory features, n-gram SVD and CLaMP embeddings, for k = 2–30. Agreement with 色彩区 is at
most AMI 0.14 (transcriptions, n-gram), and 0.02–0.09 for the scores. In the Anthology, clusters follow
province/volume slightly more than 色彩区. CLaMP clusters mostly sort songs by *length* (AMI with length bins
0.26–0.30).

*Song-level variance is dominated by genre, mode and length. Region is a weak, distributed signal that needs
supervision to extract.* This is consistent with folk-song typology, where the same regional repertoire spans 号子,
山歌 and 小调, which differ more among themselves than regions do.

### 18.2 At the level of region *profiles*, the structure is real and replicates across sources
Region-mean profiles use bias-corrected distances and average linkage, with 200-bootstrap clade support.

| Source | Tree vs geography (Mantel ρ, p) | Han vs minority | North vs South (Han) |
|---|---|---|---|
| Essen, 13 regions | 0.75 (<0.001) | separated (p = 0.004) | not recovered (p ≈ 0.1) |
| Transcriptions, 15 | 0.79 (<0.001) | separated (p = 0.001) | not recovered |
| Anthology, 5 | 0.66 (0.10, only 5 leaves) | – | not recovered |

- **Independent corpora agree.** The Essen *score* tree and the *transcription* tree of the same 13 regions are
  significantly concordant: cophenetic ρ = 0.87, p < 0.001; Fowlkes–Mallows B4 = 1.00, null 0.58, p = 0.003.
  Two collections decades apart, one notated by collectors and one sung by today's performers, imply the same
  regional similarity structure.
- **Robust clades:**
  - **新疆** is the outermost branch everywhere (74–100% support): a non-pentatonic system.
  - **北方草原 + 藏族** (transcriptions, 74%): pastoral long song.
  - **东北 + 西北** (Essen, 100%): a northern 徵/商, fourth-leap idiom.
  - **江汉–江浙–江淮–赣** (84%): the central/lower-Yangtze belt. Within it, 江淮 ≈ 江浙 and 江汉 ≈ 赣 are
    statistically indistinguishable (bias-corrected distance ≈ 0).

### 18.3 Is the 色彩区 partition more learnable than alternatives? Yes, but so is geography
All rows use n-gram LR with identical folds (grouped by title, stratified by province).

| Label set | Anthology κ (macro-F1) | Essen κ (macro-F1) |
|---|---|---|
| **色彩区** | **0.547** (0.621), K = 5 | **0.294** (0.322), K = 10 |
| random same-size partitions of the same provinces, mean [max] | 0.439 [0.510], p = 1/31 | 0.224 [0.265], p = 1/41 |
| geography-optimal / geographic k-means, same K | = 色彩区 | 0.310 / 0.300 |
| province | 0.461 (K = 9) | 0.243 (K = 20) |
| North/South, literature | 0.542 | 0.434 |
| North/South, **Qinling–Huai line** (33.5°N) | **0.583** | **0.497** |

- **The province→色彩区 grouping beats every random grouping of the same provinces.** In the exhaustive post-hoc
  version it ranks 3rd of 3,781 (Anthology) and 2nd of 5,001 (Essen).
- **Province errors concentrate inside 色彩区:** 26% vs 14% expected (p = 0.001) on the Anthology; 14% vs 7%
  (p = 0.007) on Essen.
- **But geographic contiguity alone explains the advantage.** On the Anthology, the 色彩区 *is* the distance-optimal
  grouping. On Essen, purely geographic groupings are as learnable.
- **A plain latitude split (the Qinling–Huai line) is more learnable than the literature's north/south split.** The
  difference comes from Henan and Anhui.

### 18.4 Musicological reading
- **What the data support:** a geographic *continuum* of Han style with core clades (north, central Yangtze), plus a
  sharp **Han/minority** boundary, sharpest for 新疆. That's what §9's geography-following confusions already
  suggested.
- **What the data don't specifically support:** the 色彩区 boundaries as such (they're no better than any
  contiguous grouping), and the literature's Han north/south line.
- **Specific mapping doubts:**
  - **Henan** (mapped to 江汉) clusters with and is confused with 东北 provinces (Hebei, Shandong) in both corpora.
    That supports `mapping.py`'s own ambiguity note (豫东 ∈ 东北部平原).
  - **西北部高原** splits into Shanxi/Ningxia vs Gansu/Qinghai (花儿).
  - **Taiwan, Hainan and Jilin** are outliers within their assigned 色彩区.
- **The Anthology volume question (§17.3), refined.** Volumes of the same province cluster together (p = 0.003), so
  Hebei I/II and Jiangsu I/II are not separate editorial *styles*. The leave-one-volume-out drop is better explained
  by province-level (sub-regional) style than by editorial artifacts, which is itself evidence that the 色彩区 is
  coarser than the real stylistic granularity.

## 16. Dual-view ablations (R5): `rev_dual_ablation.py`
Every variant pools 3 fold seeds and is compared with the plain n-gram model: bootstrap 95% CI, paired permutation p.
Table: `data/regionclf/review_dual_ablation.csv`.

**T15 (15 regions; n-gram baseline 0.333):**

| Variant | Macro-F1 | Δ vs n-gram [95% CI] | p |
|---|---|---|---|
| **no scores** (skeleton view = reduced transcriptions only; pure two-view self-ensemble) | 0.330 | −0.003 [−0.018, +0.011] | 0.69 |
| scores = Essen (default: level 2, equal mass, α = 0.5) | 0.360 | **+0.027 [+0.010, +0.044]** | **0.003** |
| scores = Essen + Anthology | 0.349 | +0.015 [−0.004, +0.032] | 0.08 |
| level 1 (drop ornaments only) | 0.362 | +0.028 [+0.011, +0.046] | 0.002 |
| level 3 (+ snap to 五声) | 0.345 | +0.012 [−0.009, +0.032] | 0.27 |
| score mass 0.25× | 0.356 | +0.022 [+0.006, +0.037] | 0.007 |
| score mass 4× | **0.365** | **+0.032 [+0.013, +0.050]** | **<0.001** |
| α (skeleton weight) = 0.25 | 0.355 | +0.022 [+0.009, +0.034] | 0.001 |
| α = 0.75 | 0.361 | +0.027 [+0.008, +0.046] | 0.006 |

**T5 (5 regions, 200 items; n-gram baseline 0.492):** no scores 0.471 (−0.021, p = 0.17); Essen-5 0.522 (+0.030,
p = 0.08); Anthology 0.509 (+0.017, p = 0.33); Anthology + Essen-5 0.523 (+0.031, p = 0.07).

What the ablations establish:
1. **The gain comes from the external scores, not from ensembling.** A skeleton view without scores adds nothing
   (T15 −0.003; T5 −0.021). The scores add +0.027 to +0.032 on T15. The central mixing claim holds.
2. **More score weight is better, not worse,** once scores are confined to the skeleton view: 0.25× → 1× → 4× gives
   +0.022 → +0.027 → +0.032. Contrast with naive mixing, where more scores hurt (§6.2): *where* the score
   information enters matters more than how much of it there is.
3. **Light reduction is best.** Dropping ornament notes (level 1–2) helps; snapping to the pentatonic scale (level 3)
   throws away too much, because 偏音 are regional (§4, §7).
4. **The score source should match the target's label space.** Essen covers 13 of the 15 T15 regions and helps most.
   Adding the Anthology (5 regions, 8.6k songs) dilutes the skeleton view on T15, although it helps the 5-region T5.
5. **Robust to the fusion weight** (α 0.25–0.75, all significant).
6. **T5 comparisons are underpowered** (200 items). The direction replicates T15, but no single T5 contrast reaches
   p < 0.05.

## 14. Anthology → transcription transfer, done properly (R2, R4)
Code: `rev_transfer.py`, `rev_transfer_bias.py`, `rev_transfer_fewshot.py`, `rev_transfer_pairs.py`, written by the
transfer agent; the agent was cut off by an account spend limit before writing its report. Results are all in
`results.csv` (family `review_transfer`), `review_transfer.csv` and `review_pairs_*.csv`. The numbers below come
straight from those files.

### 14.1 Zero-shot transfer with the best representation and standard domain adaptation
Train on the Anthology (8.6k scores, test-title songs excluded) and test on the 200 T5 transcriptions (chance ≈ 0.21).
The n-gram LR model is used unless stated.

| Method | Macro-F1 |
|---|---|
| plain transfer (argmax) | 0.208 |
| + skeleton reduction L3 on the transcription side | 0.355 |
| importance weighting (domain classifier) | 0.205–0.246 |
| CORAL / per-domain z-scoring (n-gram SVD) | 0.318 |
| score-side noise augmentation (synthetic ornaments, chromatic neighbours, glides), A ∪ aug | 0.336 |
| label-shift: uniform-prior rescale | 0.208–0.258 |
| label-shift: EM prior estimation (Saerens et al.) | 0.077–0.140 (*worse*) |
| **prediction-bias correction:** logit centering on the test batch / transductive balanced assignment | **0.365** |

**The largest single problem is not that transcriptions lack regional signal. The score-trained model's decision
boundary is shifted on transcriptions:** it predicts one or two regions for most of them. Simply re-centering its
logits on the unlabeled test batch, or forcing a balanced assignment, raises transfer from chance (0.21) to 0.365.
That is ~75% of the within-domain T5 score (0.49), with **no target labels at all**.
- **EM prior estimation hurts,** because it amplifies the bias. It assumes the classifier is calibrated on the
  target domain, which it isn't.
- **Skeleton reduction of the transcriptions alone gets 0.355.** Removing ornaments and snapping to 五声 undoes much
  of the shift.
- **Feature-alignment methods help less** than these music-specific or batch-level fixes: CORAL 0.32, augmentation
  0.34, importance weighting ~0.25.
- **Other directions:** Essen → T14 goes from 0.08 to 0.26 with bias correction. T5 → Anthology stays at 0.16–0.26:
  132 noisy performances can't teach the score domain.

Caveat: centering and balanced assignment are transductive. They use the test batch's unlabeled predictions and
assume roughly balanced classes, which holds for T5 (40 per region). They are legitimate for dataset-level
annotation, not for classifying a single new recording.

### 14.2 Few-shot: how much is the source data worth? (`rev_transfer_fewshot.py`)
k labeled target transcriptions per region come from the training folds only; grouped 5-fold on T5.

| k per region | Anthology only | target only | A + shots | A + shots (upweighted) | dual-view | late fusion A ⊕ target |
|---|---|---|---|---|---|---|
| 0 | 0.197 | – | – | – | – | – |
| 2 | 0.197 | 0.270 | **0.332** | 0.286 | 0.280 | 0.228 |
| 5 | 0.197 | 0.330 | **0.372** | 0.368 | 0.346 | 0.225 |
| 10 | 0.197 | 0.355 | 0.401 | **0.418** | 0.395 | 0.229 |
| 20 | 0.197 | 0.448 | 0.430 | 0.435 | **0.461** | 0.249 |
| all (~32) | 0.197 | 0.496 | 0.453 | 0.460 | **0.501** | 0.271 |

- **With few target recordings (k ≤ 10), mixing in the Anthology is worth +0.04 to +0.06,** which equals roughly
  doubling the target data. The scores supply the regional skeleton statistics that 2–10 noisy recordings can't.
- **With more target data (k ≥ 20), naive mixing starts to hurt** and dual-view becomes best. The crossover explains
  the apparent contradictions in §6.2: *mixing helps when target data is scarce, and must be confined to the
  skeleton view when it isn't.*
- **Late fusion of separately trained A and target models is poor at every k.** The A model's biased probabilities
  dominate, the same failure as §5.2.

### 14.3 Same-song evidence: transcriptions keep the tune but lose the regional detail (`rev_transfer_pairs.py`)
The test set is the 62 recordings whose title matches a region-consistent Anthology score.

**Song-identity retrieval.** Rank all of that region's Anthology scores (~1,900) by similarity to the transcription:

| Method | Median rank of the same-title score | R@1 | R@10 |
|---|---|---|---|
| chance | 354 | 0.002 | 0.02 |
| n-gram TF-IDF cosine, raw | 82 | 0.15 | 0.26 |
| n-gram TF-IDF cosine, skeleton-reduced | 65 | 0.23 | 0.37 |
| melodic alignment (transposition-invariant NW) | 56 | 0.13 | 0.29 |
| melodic alignment, cohort-normalized | **21** | **0.26** | **0.47** |

**Region prediction on the same 62 songs** (Anthology-trained n-gram LR):

| Input | Macro-F1 |
|---|---|
| the Anthology score | **0.64** (skeleton L2: 0.66) |
| the transcription of a performance of the same song | 0.20 (L2: 0.24; logit-centered: 0.33) |

This is the cleanest statement of the domain gap. **A transcription usually still identifies its tune**: the
same-title score is found in the top 10 of ~1,900 almost half the time, and 26% at rank 1, against a chance rate of
0.2%. **But the classifier can't recover the region from it** (0.64 → 0.20 on the same songs). The tune identity lives
in the contour and skeleton, which survive transcription. The regional detail the score model uses lives in the
exact scale-degree and 偏音 statistics, which transcription (ornaments, intonation, chromatic glides) corrupts.

Musicologically, that matches how 润腔 works. The performer keeps the 骨干音 (skeleton tones, and hence the tune),
and elaborates everything between them in ways that are regional but *not* the same regional traits a collector's
score encodes.

## 15. Is the gap the transcriber or the music? A resynthesis test (R3)
Code: `rev_resynth_render.py` (render), `rev_resynth_transcribe.sh` (the dataset's GAME + trim pipeline),
`rev_resynth_eval.py`. Outputs: `data/regionclf/resynth/{fidelity_summary,summary,steps}.csv`. The agent built and
ran rendering and transcription; the evaluation was run by the coordinator after the agent hit the spend limit.

**Design:**
- **Sample:** 600 Anthology scores (120 per region), rendered as a formant-synthesized "voice" (one syllable per note,
  consonant noise, legato dips) at a random tempo of 60–100 bpm, transposed into a singing register.
- **Conditions:**
  - plain: exact score
  - expressive: vibrato ±30 c, portamento, onset jitter ±20 ms, intonation ±15 c
  - heavy: doubled expressive parameters, plus 40% of notes sung as melisma
  - ornamented: expressive + simulated 润腔 (倚音 grace notes, 上/下滑音)
  - accompanied: expressive + ChMusic accompaniment, then htdemucs
- **Pipeline:** each condition goes through the same GAME + trim pipeline as the real recordings.
- **Classification:** grouped 5-fold; each fold trains on all *other* clean Anthology scores; test = the held-out
  songs in each form. 95% bootstrap CIs; paired differences on the same songs.

| Condition | Transcriber COnP | Skeleton agreement | 偏音 share | Degrees in use | n-gram F1 [95% CI] | n-gram, skeleton L2 | theory |
|---|---|---|---|---|---|---|---|
| clean score | – | – | 2.0% | 4.97 | **0.633** [0.593, 0.670] | 0.577 | 0.546 |
| plain | 0.914 | 0.999 | 1.9% | 4.97 | 0.569 [0.527, 0.609] | 0.524 | 0.510 |
| expressive | 0.912 | 0.999 | 2.0% | 4.97 | 0.611 [0.570, 0.651] | 0.535 | 0.476 |
| heavy (+ melisma) | 0.776 | 0.994 | 2.2% | 4.98 | 0.483 [0.440, 0.521] | 0.506 | 0.456 |
| ornamented (simulated 润腔) | 0.752 | 0.998 | 2.3% | 4.97 | 0.492 [0.450, 0.532] | **0.532** | 0.460 |
| accompanied → htdemucs | 0.178 *(invalid, see below)* | 0.849 | 4.8% | 4.57 | 0.202 | 0.177 | 0.245 |
| **real recordings (A → T5)** | – | – | **13.1%** | **7.89** | **0.209** [0.155, 0.261] | 0.231 | 0.223 |

Paired steps (n-gram):

| Step | Δ [95% CI] |
|---|---|
| clean → plain | −0.064 [−0.099, −0.029] |
| plain → expressive | +0.042, n.s. |
| expressive → heavy | −0.129 [−0.169, −0.089] |
| expressive → ornamented | −0.120 [−0.162, −0.078] |
| expressive → ornamented, *with skeleton reduction* | −0.002 [−0.032, +0.029] |
| heavy → real recordings | −0.274 [−0.339, −0.209] (unpaired: different songs) |

**Findings:**
1. **The transcriber isn't the main cause of the score→performance gap.** Plain, expressive and even heavily
   expressive synthetic singing, transcribed by the same pipeline, keep 0.48–0.61 macro-F1, against 0.63 for the
   clean scores. Real recordings of the same regions fall to 0.21. At least ~0.27 of the ~0.42 gap remains after
   the worst simulated transcriber conditions.
2. **Ornaments hurt, and skeleton reduction undoes them exactly.** Simulated 润腔 costs −0.12, and with skeleton
   reduction the loss disappears (−0.002). It also validates the reduction (§6.3) as the right inverse of
   ornamentation.
3. **The chromaticization of real transcriptions doesn't come from the transcriber.** Even with ±30-cent intonation
   drift, vibrato and glides, resynthesized transcriptions keep ~2% 偏音 and ~5 degrees, exactly like scores. Real
   transcriptions have 13% and 7.9. It must come from what real recordings contain and the synthesis doesn't:
   - larger and structured intonation deviation: regional non-tempered intervals, e.g. 西北's neutral "苦音" 4th/7th,
     闽 and 粤 乙反 neutral tones
   - real voices' breathiness and falsetto shifts
   - accompaniment bleed after separation
   - performers singing *different variants* of a song than the collector notated
4. **The "accompanied" condition is not a valid test.** htdemucs doesn't recognize the additive synth as a voice and
   keeps only ~18 of 85 notes per song, so its 0.20 says nothing about real vocals. On real recordings, separation
   works (docs/transcription.md §4.1). A proper test needs a real singing-voice synthesizer (SVS), left as future work.

**Conclusion:** the gap is dominated by *music and recording reality*, not by the transcription model. Better
transcription (e.g. the 3-run ensemble) won't close it, which is consistent with §6.6 and §14.3.

---

## 20. Response to the reviewer (status)

| # | Concern | Addressed? | Outcome (section) |
|---|---|---|---|
| R1 | No uncertainty | ✅ | Bootstrap CIs and paired permutation tests over 3 seeds. Dual-view > n-gram (+0.027, p = 0.003) and n-gram > theory (p < 0.001) hold. T5 contrasts are underpowered. Naive-mix harm is significant only when extra data dwarfs the target (§13). |
| R2 | Transfer only with one model, no DA | ✅ | Best model + 6 DA families. Prediction-bias correction lifts A→T5 from 0.21 to 0.365 with no target labels. EM priors hurt. Few-shot: the source is worth +0.04–0.06 at k ≤ 10 (§14.1–14.2). |
| R3 | Transcriber vs music | ✅ (partly) | Resynthesis: the transcriber costs 0.02–0.15, real recordings 0.42. The gap is mostly musical/acoustic. The accompanied condition needs a real SVS (§15). |
| R4 | Same-song evidence | ✅ | Transcriptions retrieve their own score (median rank 21 of ~1,900), but region accuracy drops 0.64 → 0.20 on the same songs (§14.3). |
| R5 | Dual-view ablations | ✅ | The gain needs the scores (no scores: −0.003). More score mass helps, light reduction is best, and the source must match the label space (§16). |
| R6 | Shortcut confounds | ✅, with a major correction | Channel ID alone equals the melody model under song-grouped folds, so channel-grouped or within-channel numbers are the valid ones: 0.28 / 0.44. Anthology leave-one-volume-out 0.43 vs 0.69 (§17). |
| R7 | Validity of intermediate steps | ✅ | 宫 estimation correct 92% (Anthology) / 88% (Essen); near-duplicates 0.9%, no effect (§17). |
| R8 | Label validity, clustering | ✅ | No song-level clusters. 色彩区 beats random province groupings but not geographic ones; Han/minority is the robust boundary; Essen and transcription trees agree (§18). |
| R9 | Tuning fairness | ✅ | Nested CV: 0 optimism on scores, 0.01–0.03 on transcriptions (§19). |
| R10 | Scope | ⚠️ limitation | 40 recordings per region, YouTube-sourced; the score corpora cover 5 and 13 regions; dating is sparse (§21). |

**Revised headline numbers** (the ones we'd defend in review):

| Task | Metric | Chance |
|---|---|---|
| Anthology, 5 regions | 0.62 in-collection; **0.43 accuracy on an unseen volume**; 0.45 on an unseen collection (Anthology → Essen) | 0.20 |
| Essen, 13 regions | 0.36 (nested) | 0.09 |
| Transcriptions, 15 regions | **0.246** dual-view, strict channel+song protocol (§22); n-gram 0.197; 0.44 within one channel (9 regions) | 0.05 / 0.11 |
| Transcriptions, 5 regions | **0.443** dual-view, strict protocol (§22) | 0.21 |

**Remaining limitations we couldn't fix here:**
- a real SVS for the resynthesis accompaniment test
- more recordings per region and more channels for the minority regions
- human-verified region labels at the county level
- a transcription-independent audio baseline, to test the surface (润腔) layer directly from F0

---

## 22. Protocol decision: musical features only, and channel can't leak (2026-10-01)
**Principle:** region must be predicted from musical features alone.
- **No model has ever taken channel or any other metadata as input.** We audited `features.py`, `exp_seq_tok.py`,
  `exp_fusion.py`, `reduce.py`, `exp_markov.py` and `pretrained_io.py`: all read only the note arrays.
- **The "channel identity only" and "metadata" rows in §17.1 are diagnostic shortcut baselines,** not models. They
  exist to measure how much channel identity *could* leak into an evaluation.
- **The leak itself is indirect.** Under song-grouped folds, a channel's singer, recording chain and transcription
  artifacts appear on both sides of the split, so a melody model can implicitly profit from them.

**New default protocol for transcriptions** (`common.folds`, `by=None` → `channel+song`):
- folds are grouped by **channel**
- each training fold also **drops every recording whose song appears in the test fold**
- verified: 0 shared channels and 0 shared songs between train and test in every fold
- strict song ∪ channel connected components are infeasible (one component holds 394/600 recordings)
- score corpora keep song-grouped folds (`by='group'`)
- everything reported from now on for T15/T5 uses this protocol

**Official transcription results** (`rev_protocol.py`; musical features only; 3 seeds pooled; 95% bootstrap CI):

| Model | T15 macro-F1 (chance 0.05) | T5 macro-F1 (chance 0.21) |
|---|---|---|
| theory features + GBM | 0.173 | 0.384 |
| multi-viewpoint n-gram LR | 0.197 [0.181, 0.213] | 0.399 [0.361, 0.436] |
| **dual-view** (n-gram surface ⊕ skeleton + scores) | **0.246 [0.227, 0.262]** | **0.443 [0.404, 0.481]** |
| Δ dual-view − n-gram | **+0.048 [+0.032, +0.065], p = 0.0002** | **+0.044 [+0.010, +0.076], p = 0.013** |
| Δ n-gram − theory | +0.025, p = 0.010 | +0.015, p = 0.49 (n.s.) |

**Reading:**
- **Under the strict protocol, every transcription number drops.** T15 n-gram falls from 0.35 (song-grouped) to 0.20.
  That is the size of the channel leakage that song-grouped evaluation allowed. The strict numbers are the honest
  estimate of generalization to *new singers and channels*: about 5× chance on 15 regions and 2× on 5.
- **The dual-view gain nearly doubles** (+0.027 → +0.048 on T15) and becomes significant on T5 too. The external
  scores carry no channel information, so their purely musical regional knowledge matters more once the shortcut is
  gone. This is now the strongest evidence for the dual-view mixing scheme.
- The song-grouped numbers earlier in this document remain as a record, but are superseded for transcriptions by
  §22. §20's headline table is updated accordingly.
