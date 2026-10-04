# Thesis evidence plan: what must be done before we can draw conclusions

Started 2026-10-02. Thesis given by the author (see memory `project_paper_scope.md` and `../colour_regions_paper/THESIS.md`).

**Rule (author, 2026-10-02):** draw no conclusion on the friction, notation or interaction claims from the current automatic data. Collect accurate annotations first. This file records what has to be done, in what order, and what result would support or weaken each claim. Decide the analyses and criteria **before** the annotations arrive, and log every result here, including nulls.

---

## Claim map

| # | Claim | Needs | Status |
|---|---|---|---|
| 1 | The dataset exists and is sound | Round 2 transcription; link check; human label check; gold-set ratings | In progress |
| 2a | Regional identity is measurable | Melody classification under the strict protocol on the merged pool | Round 1 done (0.246 / 15 regions); merged pool pending |
| 2b | The music, the notation tradition (jianpu / Anthology conventions) and Western-trained AMT disagree in systematic places | **Accurate reference annotations** (A1–A3 below); matched recording–score pairs | Not started |
| 2c | Those places of maximum disagreement are a fingerprint of regional character | 2b plus enough annotated material per region | Not started |
| 2d | Expert notators disagree with each other, and that disagreement is signal, not noise, and forms the reference envelope for machines | 3 notators per excerpt (A1) | Not started |
| 3 | Shared vs distinctive elements across regions reflect cultural interaction (contact, migration, exchange) | Region profiles from 2a–2c; tune families; geography and migration covariates | Framed as enabled + preliminary |

---

## A. Annotations to collect (outsourced). Revised 2026-10-02 after review 02

Decisions by the author (2026-10-02):
- about 45 excerpts, all notated by the same 3 notators;
- 3 blind repeats per notator and 1 calibration excerpt;
- design frozen internally (dated git commit + sha256) before the selection runs.

### A0. Definitions (from review 02 §1.2; fixed before any data exist)

- **Event:** a sung unit in a notator's performance layer.
  - A **consensus event** is marked by ≥ 2 of 3 notators, with onsets within 100 ms (150 ms in free rhythm). Its type is the majority type.
  - An event marked by only one notator is an *existence disagreement*.
  - Split/merge differences are their own category.
- **Calibrated envelope:** machine *m* is "within the envelope" on attribute *a* at the rate at which notator *k* lies within the [min, max] range of the other two notators, i.e. **leave-one-notator-out**.
  - Why: a raw 3-notator range covers a 4th human only 50% of the time.
  - The human baseline is the mean of the 3 leave-one-out rates.
- **Friction, three quantities:**
  - **F_MH** = machine out-of-envelope rate − the human baseline. Tolerance: ≥ 50 cents for pitch, ≥ 50 ms for onset.
  - **F_NP** = the rate at which the jianpu skeleton does not represent consensus events: a missing event, a neutral tone written without a mark, a dropped ornament, or a metre imposed on free rhythm.
  - **F_HH** = the envelope width.
  - Machine friction is split into *model* friction (GAME/ROSVOT note events) and *pipeline* friction (our beat grid and quantisation). Only model friction is evidence about "Western-trained AMT".
- **"Western-trained AMT"** means AMT whose output follows Western staff-notation assumptions (12-TET pitch classes, one pitch per note, a metric grid), trained mainly on Mandarin studio singing.
- **Friction profile:** a within-recording contrast, the friction rate on event type *k* minus the rate on plain `note` events of the same excerpt. This cancels recording condition to first order.
- **Fingerprint (2c).** All three conditions must hold:
  - (i) the region variance component is > 0 in a mixed model with condition covariates and random effects for singer and channel;
  - (ii) the directional hypotheses hold at their minimum effects (table B5);
  - (iii) friction adds out-of-sample regional information beyond melody under the strict protocol.
- **Signal (2d).** All three conditions must hold:
  - (a) inter-rater variance / intra-rater variance ≥ 1.5, measured on the blind repeats;
  - (b) a stable notator × event-type interaction;
  - (c) in the debrief, ≥ 50% of disagreements are coded P (perception) or C (convention) rather than S (slip) or G (guideline).
  - Concentration of disagreement on ornaments alone is **not** evidence, because measurement noise is also larger on short events.
- **2a as defended:** regional identity is measurable; it forms a geographic continuum with a sharp Han/minority boundary; the colour-region partition is one near-optimal discretisation of that continuum (the score result in `region_classification.md` §18.3).

### A1. Excerpts (about 45; all notated by the same 3 notators)

| Set | n | Content | Matching |
|---|---|---|---|
| Base | 15 | One per colour region | Excludes the dominant Round 1 commercial channel; prefers Round 2 and tier A/B |
| 苦音 targets | 8 (incl. the NW base) | Northwest Plateau, ≥ 8 different singers | Comparators are matched on field/studio and accompaniment |
| Han comparators | 15 (incl. 10 Han base) | Other Han regions | — |
| Long-song targets | 8 (incl. the Steppe base) | Northern Steppe 长调, ≥ 8 singers | Comparators are **free-rhythm** excerpts only (信天游, 散板 山歌, Tibetan pastoral songs), not metred ones |
| Free-rhythm comparators | 15 | Free-rhythm excerpts from other regions | Some overlap with the base set |
| Calibration | 1 | Not analysed | Format feedback only |
| Blind repeats | 3 per notator | Different ID, start shifted 1–2 s, ≥ 7 days later | — |

Excerpt lengths and protocol rules:
- **Length:** base excerpts 30 s; targeted excerpts 20 s.
- **Eligibility uses metadata only.** No machine output (F0, transcription) is used to choose excerpts.
- **Windows:** a coordinator listening without any pitch display adjusts each window to phrase boundaries, and logs the adjustment.
- **Free / metred** comes from genre metadata. **Field / studio** comes from `performance_type`.
- **Order:** a random order per notator (a balanced Latin square over 4 blocks). Sessions of at most 2 h, with timestamps.

**Dropped or reframed hypotheses (review 02 §2.8):**
- *Yue 乙反*: a specialist must first confirm 乙反 use per excerpt; this is secondary and exploratory.
- *Jiang–Han three-tone-cell glides*: secondary, only if the cell is defined (la–do–re) with a predicted glide share.
- *Minority off-pentatonic share*: dropped.

### A2. Notator tasks (guideline v1.1-draft: `docs/annotation_guideline.md`)

- **Skeleton first.** The skeleton is written by ear, in jianpu, with no pitch display. The performance layer follows.
- **Steady spans.** Notators mark steady spans; the **cents come from F0** (pYIN and RMVPE medians over the marked span), not from the notator's reading. This removes conservatory 12-TET pull and pYIN circularity.
- **Audio:** the mix is the primary audio; the separated voice is optional, and its use is logged per passage.
- **Required forms:** a background form (training, fieldwork, native language and dialect, absolute pitch, familiarity with each region), and per excerpt a region and genre guess, time spent and audio used. The region guess is a manipulation check; blinding is partial and is not claimed.
- **Debrief** after all notations: reason codes P/C/G/S for each of the notator's own aligned disagreements, blind to who wrote the other versions.
- **Pilot:** 2 excerpts × 2 people, timed; then guideline v1.1 is frozen with its hash.
- **Consent:** for the use and release of the notations and the anonymised background (proposed licence CC BY 4.0); pay and acknowledgement stated. Check whether the institution requires ethics review.

### A3. Matched recording–score pairs (notation vs performance)

- **Pairs:** 48 core recordings have a same-province score, in 6 regions. None are in the Northwest, Jiang–Han or the minority regions, so the 苦音 and long-song tests cannot use the Anthology.
- **Measure:** notation friction as an excess over performance variation, i.e. d(Anthology, performance) − d(performance A, performance B of the same song), by event type.
- **Conventions:** quote the Anthology editorial rules (凡例) and list in advance which differences are convention-driven.
- **Tune identity:** a specialist confirms that each pair is one tune (title ≠ tune).

### A4. Human ratings already planned

- **Gold set:** 150 notes (author).
- **Label spot-check:** 60 recordings, https://claude.ai/artifact/LQgfcNr9y8sdnYY4huHzgL.

---

## B. Analyses (frozen before the excerpts are selected)

- **B0. Multi-notator alignment.** Pairwise `mir_eval` onset matching (100/150 ms); consensus = cliques matched in ≥ 2 of 3 pairs; split/merge as its own category; type by majority. Tested on a synthetic 3-notator file first.
- **B1. 2d.**
  - Variance decomposition on consensus events: excerpt + event + notator + notator × type + residual.
  - Inter/intra ratio from the repeats; bootstrap over **excerpts**.
  - Debrief shares.
  - Skill check: if one notator causes > 60% of the 1-of-3 events, report a skill effect and rerun the analyses without that notator.
  - Fatigue: position in the order as a covariate.
- **B2. 2b.**
  - (i) A mixed logit of friction on event type: OR ≥ 2 for the top type vs `note`.
  - (ii) Event-level co-occurrence of machine failure and notation drop, given the type: Mantel–Haenszel OR ≥ 1.5. Result (i) alone does not support 2b.
- **B2b. 2b, native-theory error model** (primary hypothesis 3; from `docs/research_report_secaiqu_measurable.md` H9, after Shen 1982 音腔 and Dong 2004 润腔):
  - Within recordings, the event type predicts the machine error category (Molina et al. 2014: split, merge, spurious, onset, pitch).
  - Pitch-type inflections (glide, slide-in, throw) → more split and spurious notes than plain notes.
  - Long melisma (拖腔, `melisma_group`) → more merged notes.
  - Falsetto break → more voicing and octave errors.
  - Model: a multinomial mixed model, error category ~ event type + condition covariates + (1|excerpt) + (1|notator-consensus source).
  - Minimum effect: OR ≥ 2 for each predicted cell vs plain notes.
- **B3. 2c, primary measures (Holm over the three primary hypotheses: 苦音, long song, error model):**
  - **苦音:** NW degree 4 is ≥ +15 cents and degree 7 is ≤ −15 cents relative to the other Han regions, beyond the pan-regional drift.
  - **Long song:** inter-notator onset SD on Steppe 长调 events is ≥ 1.5 × the SD on free-rhythm comparators.
  - Plus a region variance component > 0 on within-recording contrasts after condition covariates.
- **Condition controls:**
  - within-recording contrasts;
  - the 8 same-singer/same-song cross-channel pairs and the 33 multi-channel singers;
  - controlled degradation of the 5 cleanest excerpts and the vocadito clips (accompaniment at corpus `vocal_db` quantiles, reverb, codec);
  - matched selection.
- **Scale-up gate:** an automatic friction measure is applied to the full corpus only if Spearman ρ ≥ 0.7 against the human-referenced measure, with a lower 95% CI bound ≥ 0.35 (per event type, over excerpts). Otherwise report "not validated" and skip the open test.
- **B4. 3, contact (confirmatory test on Round 2 only).**
  - The Round 1 and Essen comparisons are the exploratory work that produced the hypothesis, and are reported as such.
  - Links are fixed on 2026-10-02, **after** seeing Round 1/Essen similarities:
    - Hakka with Gan, Min–Tai and Yue;
    - 湖广填四川 (Southwest Plateau with Jiang–Han and Xiang);
    - Northern Steppe with Northeast Plain and with Northwest Plateau;
    - hua'er coded as Northwest Plateau–Tibetan.
  - Three distance forms are fixed in advance: linear, log, and exponential (range fitted on unlinked pairs).
  - Null: a spatially constrained permutation, plus a regression on distance matrices with a multi-membership random effect. The result must hold under all three forms.
  - Also: recording-level distance-decay residuals, and a Han/minority barrier test.
  - Literature models: `brown_2014`, `savage_2022`, `volk_vankranenburg_2012`, plus Guillot & Rousset 2013 and Legendre et al. 2015 (to be added to the bib).
  - **Tune families:** a case study of about 8 tunes that occur in ≥ 3 regions, with membership confirmed by a specialist and skeleton alignment (`savage_2022`-style). Registered prediction: mode and auxiliary tones change more across regions than contour does.

### B4b. Guardrails (from the research report, §2.2 and H13/H17)

- **Defining vs non-defining features:**
  - Melody features (mode, intervals, cells) are close to the traits used to define the regions, so they test internal consistency only.
  - Independent validation uses non-defining features: cents intonation, ornament density from audio, friction profiles and disagreement.
  - Report the two families separately.
- **Free rhythm is a genre effect.** Comparisons of rhythm or onset friction stratify by free vs metred, so that a genre effect is not reported as a region effect.
- **Media diffusion.** Contact links must also hold in tradition-bearer recordings alone, because broadcast-era songs spread features without migration.
- **走西口 corridor.** The Mongolian–Han link is specified as the 走西口 migration (Shanxi/Shaanxi → western Inner Mongolia). 漫瀚调 recordings, if present, are a natural mixture test.
- **湖广填四川 evidence.** The documented evidence is for opera (高腔), not folk song; the folk-song prediction is an inference.

### B5. Decision table

| Claim | Supported if | Refuted if | Otherwise |
|---|---|---|---|
| 2b | B2 (i) **and** (ii), each with a CI excluding 1 | The MH OR CI lies inside [0.67, 1.5] | Report as inconclusive |
| 2c | ≥ 1 of the 2 primary hypotheses passes Holm at its minimum effect, **and** the region variance component is > 0 after condition controls | Both primary effects lie inside equivalence bounds (±10 cents; onset SD ratio 0.8–1.25), or the region effect vanishes after condition controls | "No evidence at this sample size", with CIs |
| 2c open | Δ macro-F1 ≥ 0.02 (CI excludes 0) after the scale-up gate | The gate fails, or the Δ upper CI bound is < 0.01 | — |
| 2d | inter/intra ≥ 1.5 (CI excludes 1) **and** debrief P+C ≥ 50% **and** a stable notator × type interaction | The inter/intra CI lies inside [0.8, 1.25], or S+G > 50% | "Partly structured" |
| Envelope usable | The human leave-one-out within-envelope rate is ≥ 0.6 for pitch on `note` events | The rate is lower | Report the envelope as a finding, not as a yardstick |
| 3 | Linked pairs have a residual > unlinked, p < .05 under the spatial null, under all 3 forms | p ≥ .2, or the sign changes across forms | "Preliminary, not robust" |

Note: the 2c criterion is "≥ 1 of the 苦音/long-song hypotheses"; the error-model hypothesis supports 2b, not 2c. The "≥ 1 of 2 primary hypotheses" wording, because review 02's "≥ 2" assumed more hypotheses than the 2 kept.

---

## C. Exploratory automatic probes so far (NOT conclusions)

Run on Round 1 only, 2026-10-02, with automatic F0 and transcriptions, core subset (n ≈ 500), strict protocol. Scripts are in the scratchpad; the intonation feature code is `src/regionclf/intonation.py`.

**C1. Aggregate per-recording friction did not separate the 15 regions.**
- Features: tracker agreement, glides, wobble, GAME–ROSVOT agreement, critic verdict rates.
- Macro-F1 0.071, against a shuffled-label 95th percentile of 0.080.
- Interpretation limit: these features also reflect recording conditions.

**C2. Scale-degree intonation profiles did not separate regions either** (15-way, or Han vs minority).
- The automatic tonic and the steady-frame deviation per degree did not separate regions.
- Off-pentatonic degrees deviate toward their pentatonic neighbours in every region: 4 is flat, ♯4 sharp, ♭7 flat and 7 sharp, by 7–28 cents.
- Possible artefacts: automatic tonic errors (about 20% on transcriptions), binning neutral tones into the wrong semitone, and transition frames.

**Why these are not evidence against the thesis:**
- They use automatic tonic and F0, not human reference annotations.
- 15-way classification is a blunt test compared with the targeted hypotheses of B3.
- Round 2 is not included.

They show only that coarse automatic measures are not enough, and they motivate A1–A2.

---

## D. Order of work, owners and dates

| Date | Step | Owner | If missed |
|---|---|---|---|
| by 9 Oct | Freeze this plan, the guideline v1.1-draft and the selection script: a dated git commit plus the sha256 recorded below | Author + Claude | — |
| by 7 Oct | Code free/metred **by ear** for `data/annotation/free_rhythm_candidates.csv` (112 recordings outside the Steppe, about 1–2 h), save as `free_rhythm_coding.csv`. Needed because the metadata marks free rhythm almost only in the Northwest | Coordinator | Long-song comparators fall back to NW free-rhythm songs (confounded; report it) |
| by 9 Oct | Run the selection; the coordinator adjusts the windows by ear; freeze `excerpts.csv` (with its hash) | Coordinator | Go to the fallback for 2c, keep 2d |
| by 16 Oct | Contract 3 notators (≥ 1 with fieldwork-based ethnomusicology training); consent; pilot 2 × 2; freeze guideline v1.1 | Author | Reduce to 24 excerpts (base + 4 + 4 targets) |
| by 10 Nov | All notations, repeats and debriefs received | Notators | If 2 notators finished ≥ 12 excerpts, run 2d on that subset; otherwise fallback |
| by 17 Nov | Registered analyses run; results logged here, including nulls | Claude | Fallback |
| by 24 Nov | Paper frozen at ≤ 8,000 words | Author + Claude | — |

**Workload estimate:**
- about 45 excerpts × 3 notators × 1.5–2 h ≈ 200–270 notator-hours;
- plus 9 repeats, 3 calibration tasks, 3 debriefs (about 1 h each) and the forms.
- That is about 75–95 h per notator over about 3.5 weeks. The pilot timing replaces this estimate.

**Fallback structure** (review 02 §5.3): a data paper whose thesis section is a registered open question. It contains the definitions, the decision table, a worked pilot excerpt marked n = 1, and the release plan for the notations.

**Freeze log:** (sha256 values and commit ids go here)
