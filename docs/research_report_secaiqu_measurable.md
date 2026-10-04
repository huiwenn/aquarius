# 色彩区 as a Measurable Object: Integrated Research Report

Humanities and MIR evidence for a TISMIR paper on regional style, transcriber disagreement, and the limits of Western-trained transcription in Chinese folk song

Prepared 2026-10-02 for the Digital Musicology project.

---

## How to read this report

The report has three layers:

- §1–§5 are the integrated synthesis: the bottom line, where the two lines of evidence agree and where they conflict, the reviewer objections that cut across both, a unified list of testable sub-hypotheses that can serve as the spine of the analysis section, and the minimum design those hypotheses need.
- **Part A** is the annotated humanities survey (Q1–Q5): transcription theory, Chinese notation conventions, 色彩区 theory, critiques of MIR bias, and contact/migration precedent.
- **Part B** is the annotated technical survey (Q6–Q10): AMT state of the art and failure modes, metrics, models of annotator variation, mixed-effects and Bayesian statistics, and envelope benchmarking. It ends with a tool stack.

Every source entry gives its claim, method, and relevance. Section references such as §A3.1 or §B9.3 point into Parts A and B.

**Verification legend.** The two parts were researched separately and use slightly different tags, which are kept as they are:

- Part A: **[V]** means confirmed by search or by opening the page in this session. **[V-partial]** means the work exists but one named element is unconfirmed. **[R]** means recalled from memory and not confirmed.
- Part B: untagged items were confirmed against search results, publisher or arXiv pages, or Crossref. **[UNVERIFIED]** and **[DOI unverified]** mark items that were not.

No citation was invented. Items that were not fully confirmed are collected in Appendix C and should be checked before submission. Text labelled "inference" is a proposal for this paper, not a claim from the literature.

---

## 1. Bottom line

1. **The thesis is new and defensible, but its three claims carry different risks.** No published study has tested the Miao–Qiao 色彩区 boundaries against feature distributions with source and transcriber treated as variance components. None has modelled transcriber disagreement on Chinese material. And none has asked whether AMT failures fall where Chinese music theory says the note concept breaks down (§A3.3, §B13). The three claims are not equally strong:
   - "色彩区 is real and measurable" can be tested now, but it has a **circularity** problem.
   - "Disagreement as fingerprint" is the most original claim, but it needs data that the corpus probably does not yet contain: the same audio transcribed by several experts.
   - "Feature-sharing as cultural interaction" has the strongest precedents (the Savage group; Nishikawa & Ihara 2025), but the inference is the hardest to secure. Shared features can also come from common origin, from shared function, or from spread through modern media.

2. **Native Chinese theory supplies the failure model, which keeps the paper from being "AMT is bad on a new dataset".** 沈洽's 音腔论 (1982) says the basic unit of Han music is an inflected tone with a head, body and tail, not a point pitch. 董维松's four types of 润腔 (2004) give a typology of melodic inflection. Together they predict *which* layer of AMT should fail and *where* (§A2.3). The Molina split/merge/spurious categories and cents-level deviation are the instruments that can test that prediction (§B7). This is the main point where the humanities and technical lines meet, and it is the most publishable result in prospect.

3. **"Western-trained" is the wrong label for most of the systems.** The singing transcribers likely to be used (ROSVOT, SOME, VOCANO, and models trained on MIR-ST500, Opencpop or M4Singer) were trained mostly on **Mandarin pop** (§B6.3). The three-system tension (the music, Chinese notation, Western models) is better framed as **four reference systems**:
   - regional practice;
   - Chinese prescriptive notation;
   - conservatory and pop vocal norms, which both the models and many Bilibili singers absorbed;
   - Western instrumental priors (MT3).

   This turns a reviewer objection into a designed contrast.

4. **The largest single risk is that disagreement between anthologies mixes two things.** Two notations of "the same song" in different sources usually record different performances or different variants, not two transcribers hearing one performance (§B12, objection 1). Without a calibration subset of the same audio transcribed by at least three experts across regions, the "envelope" can only be estimated at the level of tune families.

5. **The effective sample size for a region effect is about 10 regions and their provinces, not 700 recordings.** In the 集成 anthology the editorial team sits inside the province, and the province sits inside the 色彩区. So region is confounded with transcription school by construction (§A2.2, §B9.3). The humanities line argues this is partly the point, because notation tradition is one of the systems under study. The response is to separate the variance into components rather than try to remove the confound.

6. **The English-language literature is thin exactly where the thesis rests.** 色彩区 theory, the 音腔/润腔 account of the tone, 集成 editorial practice, migration-and-song case studies, and measured intonation of 苦音 (the "bitter-tone" mode) are essentially Chinese-language only (§A6). AMT of Chinese folk singing, ornament metrics and heterophony evaluation are thin in every language (§B13). Reading 苗晶 & 乔建中 1987, 杨匡民 1987, 周青青 2009/2011, 杜亚雄 2011, 沈洽 1982 and 董维松 2004 in the original is a prerequisite, not an optional extra.

---

## 2. Integrated synthesis

### 2.1 Where the two lines reinforce each other

| Humanities claim (Part A) | Technical counterpart (Part B) | What the combination buys |
|---|---|---|
| Seeger 1958: staff notation is *prescriptive*, while machine pitch tracing is *descriptive*. Chinese 谱简腔繁 ("sparse score, rich performance"): the score records only the skeleton tones (§A1.1, §A2.1) | Three evaluation layers (F0 / note segmentation / symbolic). Wang et al. 2026: notation-level and playback-level scores favour different pipelines (§B7) | Reframes "AMT vs. anthology error" as **descriptive layer vs. prescriptive layer**. The layered metrics measure that gap directly instead of calling it error |
| England 1964 (four independent transcriptions of one Hukwe recording), List 1974, Stanyek 2014: transcription is selective, and experts disagree most on microtones, ornaments and free rhythm (§A1.1) | Ozaki et al. 2021 (κ ≈ .7 among humans vs. < .4 for AMT); Balke et al. 2016 (disagreement concentrated on glides, onsets/offsets and voicing); Plank 2022, "human label variation" (§B6.4, §B8) | A convergent prediction: **disagreement concentrates on specific features**. The humanities line explains why; the technical line supplies the measure (per-position entropy and variance components) |
| 沈洽 音腔 (head, body, tail); 董维松 润腔 types: pitch, rhythm, dynamics, timbre (§A2.3) | Molina split / merge / spurious; cents deviation; MIDI pitch bend; MV2H meter (§B7) | A **mapping from native theory to error type**: pitch-type 润腔 → splits and bend drift; rhythm-type → onset and segmentation error; timbre-type → invisible to MIDI, so audio features are needed (§3, H9) |
| 苦音 ↑4 / ↓7 are written only as signs; their size is lost in jianpu (§A2.1, §A3.2) | Cents per scale degree (Koduri et al. 2014 Carnatic method); Tarsos; Benetos & Holzapfel 2015 microtonal grid (§B6.4, §B7) | The audio layer is *better* than the notation for one regional feature. This is a strong argument that the noisy layer carries information the human layer cannot |
| 杨匡民 三声腔 (three-note cells); 王耀华 腔音列 (interval cells); 杜亚雄 2011: metre, range and phrase-final note (§A3.1) | n-gram and alignment features; Needleman–Wunsch; music21 (§B7, §B11) | **Native, computable feature definitions** instead of generic pitch histograms. This answers the "not just another dataset" critique (Huang et al. 2023) |
| 周青青 2011: 底层 / 借用 / 交融 (substratum / borrowing / blending) (§A3.1, §A5.2) | Mixture-membership models on profile vectors (§B14, T9) | A **native vocabulary that matches a statistical model**: substratum = home-region component; borrowing = a localized foreign component; blending = an intermediate mixture weight |
| Nishikawa & Ihara 2025: barriers, not distance, drive melodic divergence (§A5.1) | Boundary-discontinuity tests; GP vs. categorical-region comparison (§B9.3) | One test serves both "regions are real" and "contact": **sharp change at a boundary beyond distance-decay** |
| The 集成 picks one representative variant; editors normalized toward conservatory theory (§A2.2) | Weiß et al. 2020: separate the version axis from the annotator axis (§B8.2) | Both lines say the same design is needed: **separate performance/variant variance from transcriber variance** |

### 2.2 Where they conflict

1. **Truth-model conflict.** The humanities line treats transcriber difference as interpretation that a transcriber's position makes inevitable (Seeger, Stanyek, 周凯模 2004). The standard technical aggregation models, such as Dawid–Skene, assume one latent true label and estimate "error rates" against it.
   - *Resolution:* report per-transcriber confusion matrices as **systematic tendencies**, not error rates (§B8.1).
   - Prefer models that let variance itself be the outcome: brms distributional models with σ ~ region, and soft-label evaluation (Uma et al. 2021).
   - Say in the paper which variance is treated as noise (OCR, clear slips) and which as signal (interpretive choices).

2. **The circularity trap.** The humanities line wants features grounded in native theory (mode, 三声腔, cadence notes). But those are close to the evidence Miao and Qiao, and the textbooks, used to draw and describe the regions. The technical line wants features *not* used in the definition. So the most theory-valid features are also the most circular.
   - *Resolution:* preregister two feature families.
     - **Defining features:** mode, interval cells, cadence notes.
     - **Non-defining features:** cents intonation, ornament density from audio, AMT failure profiles, disagreement entropy.
   - Recovering regions from defining features shows the theory is *internally consistent*. Recovering them from non-defining features is *independent validation*. Report the two separately (H2 vs. H3).

3. **Region as category or as gradient.** Miao and Qiao hedge with 近似 ("approximate") and call 江淮 a transitional zone. Cornelissen et al. 2026 find no discrete contour clusters in the Essen Chinese subsets. Hodges & Reich 2010 show a spatial smoothing term can absorb a categorical region effect.
   - This is less a contradiction than an agreement that the claim should be put differently. "色彩区 is real" should mean **a regional partition explains variance beyond smooth geography and shows boundary discontinuities for some features**, not that songs fall into discrete types (H4).
   - The discrete-type claim should be dropped explicitly.

4. **Confound or object of study?** To the technical line, province-nested editorial teams are a confound to be controlled. To the humanities line, notation tradition is one of the three systems the paper studies.
   - *Resolution:* model editorial and transcriber variance as a **named component** whose size, compared across features, is itself a finding (H6). Do not fold it into a nuisance term.

5. **What carries regional style.** Chinese theory puts much of regional colour in 腔词关系 (tune–text relations) and dialect tone (于会泳; 杜亚雄's "music dialect" areas). The planned pipeline is melody-only MIDI.
   - Both lines therefore predict a ceiling on what melody alone can recover.
   - *Mitigation:* use the lyrics-aligned OMR subset (Bu et al. 2025 report more than 1,400 songs with lyrics) and dialect-zone covariates. State the melody-only limit as a scope condition.

6. **Is Bilibili a field recording?** The technical line treats Bilibili as the out-of-sample audio test set. The humanities line warns that much of it is conservatory 民族唱法 (the trained "national" singing style), revival or staged performance, which reproduces textbook regional style. Validation on Bilibili could then be circular in a second way.
   - *Resolution:* code performer type (原生态 tradition-bearer / 学院派 conservatory / revival) as a factor.
   - Treat "region signal decays with conservatory training" as a hypothesis in its own right (H5). Do not treat it as noise.

### 2.3 Strongest reviewer objections by side

These are the objections most likely to decide acceptance. Full lists with mitigations are in §A8 (ten humanities objections) and §B12 (twelve technical objections).

**Humanities reviewer**
1. *Circularity and reification.* 色彩区 is a 1980s PRC disciplinary construct, defined partly by dialect and geography from the same kind of anthology material, so recovering it shows the editors' categories. *Response:* §2.2 items 2 and 3; cite Yang Mu 1994/2003; treat regions as a hypothesis with graded membership.
2. *A transcriber fingerprint, not a fingerprint of the music.* Regional differences in disagreement may reflect provincial training cultures. *Response:* H6 vs. H7 separates the two, and the calibration set is needed.
3. *Feature-sharing ≠ interaction.* 杜亚雄's Yugur–Hungarian argument is the cautionary example. *Response:* corridor vs. matched non-corridor nulls, and date stratification (H12–H14).
4. *Han-centrism and English-only engagement.* *Response:* state the scope (Han + Hakka), analyse Han–minority contact zones (花儿, 漫瀚调) separately, and cite Chinese originals with pinyin and translation.

**Technical reviewer**
1. *Anthology–anthology difference is variant difference.* *Response:* the calibration set (Ozaki design, ≥ 3 experts, stratified by region) plus the Weiß decomposition.
2. *Pseudo-replication and too few regions.* *Response:* the recording is the unit; partial pooling with half-t priors (Gelman 2006); a preregistered simulation of power at realistic, unbalanced allocations (§B9.4).
3. *AMT failure just tracks recording quality.* *Response:* quality covariates (SNR, separation residual, bitrate, reverb), and a check that region effects keep their direction in the cleanest quartile.
4. *12-TET MIDI builds in the bias it claims to measure.* *Response:* make continuous F0/cents the primary layer and quantized MIDI one condition (§B12, objection 5).
5. *The OCR layer is not a human reference.* About 5% note error is implied by Bu et al. 2025. *Response:* an OMR-NED audit stratified by volume and region, with OCR uncertainty propagated.

---

## 3. Unified testable sub-hypotheses (the spine of the analysis section)

These merge the humanities inferences (§A1–A5, §A7) with the technical hypotheses T1–T9 (§B14). Each gives the claim, the operationalization, the prediction that supports the thesis, and what would count against it. Priority: **P1** can be tested on the existing corpus; **P2** needs the calibration set or new coding; **P3** is exploratory.

Shared notation for the formulas below: *r* is 色彩区; *f* is a feature (pitch class, cents, onset, duration, ornament, boundary, metre); *s* is song/recording; *p* is province/volume; *t* is transcriber/edition; *u* is Bilibili uploader; *k* is pipeline.

### Family A: 色彩区 is real and measurable

**H1. Region structure in the symbolic layer (P1).**
- *Claim:* within 集成 scores, features defined by native theory (mode distribution as in 周青青 2009; 三声腔/腔音列 trigrams; 杜亚雄's metre, range and cadence note) vary by Miao–Qiao region more than by province alone.
- *Test:* a hierarchical multinomial or distributional model, feature ~ *r* + (1|*p*) + genre. Compare it by LOO-CV with a province-only model and a genre-only model.
- *Supports:* the region term improves ELPD, and its effects match the qualitative descriptions (for example 湘羽 "Hunan *yu*-mode tune system", 江汉 三声腔).
- *Against:* no gain over province, or effects that contradict the textbook descriptions.
- *Caveat:* this tests internal consistency only (§2.2, item 2).

**H2. Independent validation from non-defining features (P1/P2).**
- *Claim:* regions are also recoverable from features the theory did not use to draw them: cents intonation per scale degree, ornament density measured from audio, the AMT failure profile, and disagreement entropy.
- *Test:* the same model on Bilibili-derived features, with quality covariates and (1|*u*).
- *Supports:* the region term survives quality adjustment, and its direction is stable in the cleanest quartile.
- *Against:* the region effect disappears once quality and uploader are added.

**H3. Holdout with an external replication set (P1).**
- *Claim:* a region model fitted on 集成 transfers to Essen Han/Natmin and to Bilibili, both of which have different transcription chains.
- *Test:* out-of-source prediction accuracy compared with a permutation null.
- *Against:* transfer at chance, which would point to editorial artefact.

**H4. Partition beyond geography (P1).**
- *Claim:* a categorical 色彩区 term explains variance beyond a smooth spatial surface for *some* features. Pairs of nearby sites on opposite sides of a boundary differ more than equally distant pairs on the same side.
- *Test:* three models (region; Gaussian-process spatial term; both) compared by ELPD. A matched-pair boundary test. Follows Hodges & Reich 2010 and Nishikawa & Ihara 2025.
- *Supports:* boundary sharpness for at least some features.
- *Against:* the GP alone is as good as region + GP for all features. Then regions are gradients, and the thesis should be restated in those terms.

**H5. Region signal decays with conservatory training (P2).**
- *Claim:* 学院派 (conservatory) performances show weaker region effects in non-defining features than 原生态 (tradition-bearer) performances.
- *Test:* region × performer type interaction on the H2 features.
- *Why it matters:* it turns the Bilibili sampling objection into a finding about modern homogenization. Neither line found any measured precedent.

### Family B: Disagreement as a fingerprint

**H6. A fingerprint of the notation tradition (P1/P2).**
- *Claim:* edition and transcriber variance is large for rhythm, ornament and phrase boundaries, and small for pitch-class skeleton. This is the 谱简腔繁 principle in measurable form. The size of the edition variance also differs by province, consistent with uneven normalization by editors.
- *Test:* variance components by feature, (1|*t*) within (1|*p*). Per-volume grace-note density as a direct measure of normalization (§A2 synthesis).
- *Against:* edition variance is uniform across features. That would suggest noise, not a tradition.

**H7. A fingerprint of the music (P2; needs calibration).**
- *Claim:* on the same audio, the per-position entropy of expert disagreement is predicted by local acoustic properties (glide extent, notes under about 150 ms, melisma on one syllable, 苦音 degrees). Its regional means differ *after* transcriber effects are removed.
- *Test:* a distributional model, entropy ~ local features + *r* + (1|*t*) + (1|*s*). This is technical T2, and it extends the England 1964 inference.
- *Against:* entropy is explained by transcriber identity alone.

**H8. Disagreement is structured where notation under-specifies (P2).**
- *Claim:* expert disagreement concentrates on the features jianpu encodes only as signs or leaves out: 润腔, 散板 durations, the size of neutral intervals. It is low on features jianpu encodes fully: degree, octave, barred durations.
- *Test:* rank-correlate per-feature disagreement with a coded "notational specificity" scale derived from §A3.2.
- *Why it matters:* this is the direct test of the Seeger / 谱简腔繁 argument.

### Family C: Model deviation and ontological mismatch

**H9. Native theory predicts where AMT fails (P1).**
- *Claim:* the Molina error categories line up with 董维松's 润腔 types:
  - pitch-type 润腔 (slides, 甩腔 flung phrase-endings) → **split** and spurious notes plus bend drift;
  - rhythm-type → onset and merge errors;
  - long syllabic melisma / 拖腔 (prolonged melismatic tail) → **merge** errors;
  - timbre-type (真假声 true/falsetto alternation) → voicing and octave errors.
- *Test:* code 润腔 events on a stratified sample. Then a multinomial GLMM on error category ~ 润腔 type + quality covariates + (1|*s*).
- *Supports:* the 润腔 type predicts error type better than generic difficulty (SNR, tempo, accompaniment). This addresses humanities objection 7.
- *Against:* error type is explained by generic difficulty alone.

**H10. Humans and models struggle in the same places (P2).**
- *Claim:* per-position AMT split rates correlate with human ornament disagreement within region (T4). That would mean AMT "failure" partly tracks genuine ambiguity, not random error.
- *Test:* a within-region correlation on aligned positions, and the envelope grid in §B10.2.
- *Interpretation:* inside the envelope with high human variance = a property of the music. Outside the envelope with low human variance = a tradition-specific model failure. Outside the envelope in a consistent direction = epistemic bias.

**H11. Systematic quantization bias (P1).**
- *Claim:* sung scale degrees deviate from 12-TET in region-structured ways (苦音 ↑4/↓7 in the Northwest; neutral intervals elsewhere). 12-TET-quantizing pipelines produce **direction-consistent** pitch-class errors at exactly those degrees (T5).
- *Test:* per-degree cents distributions with bimodality tests and a direction-consistency test, compared with the drift baseline in Mauch et al. 2014 (about 11 cents).
- *Note:* this is also the first measured 苦音 intonation study the search found in either language, which is a stand-alone contribution.

**H12. Whose prior? (P1).**
- *Claim:* the gap between the training-free pYIN arm and the pop-trained arms (ROSVOT, SOME) varies by region and grows with stylistic distance from Mandarin pop. The MT3 arm (trained on Western instruments) fails differently again (T6).
- *Test:* pipeline as a fixed effect with *r* × *k* interactions. Optional: an unsupervised PESTO fine-tuning arm as a domain-adapted control.
- *Why it matters:* it changes "Western-trained bias" from an assertion into a decomposition over three priors.

**H13. Free metre is a genre effect, not a region effect (P1).**
- *Claim:* MV2H meter and note-value scores collapse for 散板 (free-metre) material whatever the region. Apparent region effects on rhythm error are mediated by genre (T7).
- *Test:* stratify, or run a mediation analysis.
- *Why it matters:* a guardrail that stops a genre effect being reported as a 色彩区 effect.

### Family D: Feature-sharing as cultural interaction

**H14. Corridor excess (P1).**
- *Claim:* feature-sharing between non-adjacent regions exceeds a geographic-distance null specifically along documented migration corridors. The two main cases are 走西口 (Shanxi/Shaanxi → western Inner Mongolia) and 湖广填四川 (Hubei/Hunan/Jiangxi → Sichuan).
- *Test:* pairwise feature similarity ~ distance + corridor indicator + dialect-group distance, with Mantel-type or dyadic mixed models (Passmore et al. 2024-style controls). Compare with matched non-corridor pairs.
- *Caveat:* for 湖广填四川 the musical evidence is documented for opera (高腔, from 弋阳腔), not folk song. The folk-song prediction is an inference (§A5.2).

**H15. Border songs are mixtures (P1/P3).**
- *Claim:* songs from border and contact zones have profiles that are mixtures of their neighbours' profiles, and the mixture weights fit 周青青's substratum / borrowing / blending categories (T9). Test cases: 江淮 (the explicitly transitional region), 房陵 (Fangling, NW Hubei), and 漫瀚调 (between the Northwestern Plateau and Ordos Mongolian short song).
- *Test:* a mixture-membership (admixture-type) model on profile vectors.
- *Supports:* 漫瀚调 sits between its two source distributions, and 江淮 shows intermediate weights.
- *Against:* border songs look like one parent or like neither.

**H16. Tune-family phylogeny follows contact, not only distance (P1/P3).**
- *Claim:* in a 同宗 (same-ancestor) family such as 茉莉花 / 鲜花调 (Jasmine Flower / Fresh Flower Tune), alignment distances between variants follow 色彩区 boundaries and known routes more than straight-line distance. Following Savage et al. 2022, rhythmically and functionally strong notes should be more conserved.
- *Test:* Savage–Atkinson alignment, then a phylogenetic network, then a dyadic model.
- *Extra datum:* Barrow's 1804 European transcription is a historical *inter-transcriber* point, which links Family B and Family D.

**H17. Contact vs. common origin vs. media diffusion (P3, guardrail).**
- *Claim:* shared features attributed to contact should be (a) localized along corridors, (b) present in older or tradition-bearer sources, and (c) absent from purely radio-era repertoire.
- *Test:* date-stratify (集成 collection date; Bilibili performer type). Check whether sharing is confined to post-1950s "national" songs, which would point to modern media rather than migration.
- *Why it matters:* this is the main defence against the Lomax and 杜亚雄-type objection.

### Hypothesis-to-claim map

| Thesis claim | Primary hypotheses | Guardrails |
|---|---|---|
| 色彩区 is real and measurable | H1, H2, H3, H4 | H5, H13 |
| Disagreement is a fingerprint | H6, H7, H8 | H10 (separates ambiguity from model failure) |
| Model deviation reveals a mismatch of note concepts | H9, H11, H12 | H13 |
| Feature-sharing is evidence of interaction | H14, H15, H16 | H17 |

---

## 4. Minimum design the hypotheses require

| Requirement | Needed for | Status / action |
|---|---|---|
| **Calibration set:** the same audio transcribed independently by at least 3 experts, stratified across regions; ideally both jianpu-trained and staff-trained notators | H7, H8, H10; the envelope protocol (§B10.2) | Probably missing. Highest-priority new data. Check whether Jing Luo's MGD "1,214 songs, 7 regions, five annotations" subset really has multiple annotators: "five annotations" may mean five label *types* |
| **OCR audit:** a hand-checked stratified sample, OMR-NED per volume and region | All symbolic-layer results | Bu et al. 2025 imply about 5% note error. Also check whether the paper's OCR pipeline *is* Bu et al.'s; if so, cite it as shared infrastructure, and if not, distinguish the two |
| **County-level provenance** for each 集成 song, plus a Hakka flag | Region assignment, H1, H4, H14 | 色彩区 boundaries cut across provinces; province labels are not enough |
| **Collection date** and 集成 volume/editor metadata | H6, H17 | Read from each volume's 凡例 (editorial guidelines) and front matter |
| **Performer coding** for Bilibili (原生态 / 学院派 / revival; staged or in-context), uploader ID, and quality covariates | H2, H5, H12 | Humanities coding plus automatic SNR, bitrate and separation-residual estimates |
| **润腔 event coding** on a stratified sample (types per 董维松) | H9 | Expert time. Gong & Serra's jingju work suggests the syllable as the segmentation unit |
| **Continuous F0 kept as the primary layer**; quantized MIDI as one condition | H2, H11, H12 | Pipeline design choice (§B11) |
| **Pipeline arms:** pYIN (training-free), ROSVOT/SOME (Mandarin pop), MT3/YourMT3+ (Western multi-instrument); optional PESTO domain-adapted | H12 | All open source |
| **Preregistration:** feature families (defining vs. non-defining), random-effects structure, equivalence margins, and a simulation-based power analysis at realistic unbalanced allocation | All confirmatory tests | §B9.4. Do not quote power figures until a pilot gives the ICCs |

**Power, plainly.** About 700 recordings give strong power for contrasts *within* a recording or pipeline (H9, H11, H12). They give limited power for omnibus region effects, which depend on roughly 10 regions and their provinces (Westfall et al. 2014). Balancing recordings across regions helps far more than adding recordings to well-covered regions. Expect some regions to fall below a usable count. Plan to pool or report those regions descriptively, and decide which beforehand.

---

## 5. Uncertainty ledger

### 5.1 Consensus vs. inference

| Proposition | Status |
|---|---|
| Transcription is selective; experts disagree most on microtones, ornaments and free rhythm | Consensus in both literatures |
| Experts agree highly on pitch sequence under a shared 12-TET frame; AMT agrees much less | Empirical, one study (Ozaki et al. 2021, 32 songs, pitch only) |
| Chinese notation records a skeleton (谱简腔繁) | Native consensus |
| Han folk song has approximate regional colour zones (10 + Hakka) | Disciplinary consensus in China; qualitative, partly extra-musical criteria, never formally validated |
| Regional style is carried by mode, interval cells, 润腔 and text-setting | Consensus in Chinese theory; relative weights unknown |
| Inter-annotator agreement bounds achievable system scores | Established in MIR (Flexer & Grill 2016; Ni et al. 2013) for same-item designs |
| Musical features track population history | Supported at group level (Brown et al. 2014; Pamjav et al. 2012); weakly in global data (Passmore et al. 2024) |
| Feature-sharing shows *contact* | Contested; needs controls |
| Disagreement is region-structured; AMT failure falls where the 音腔 concept and the Western note diverge; region recoverable from non-defining features | **Novel inference, untested; the paper's contribution** |

### 5.2 Where English is thin and Chinese is essential

- **Chinese-only:** 色彩区 theory and its criteria for each region; the 音腔/腔音/润腔 account of the tone; 集成 editorial rules, which are internal documents not online (the fallback is each provincial volume's 凡例); 同宗民歌 and migration-and-song studies (走西口, 湖广填四川).
- **Thin in every language:** AMT of Chinese folk singing (no benchmark found); measured 苦音 intonation; ornament metrics; heterophony in AMT evaluation; a Chinese-language critique of MIR/AMT bias (none found; the Chinese critiques address Western *music theory*, not tools).
- **Strong in English:** transcription theory, MIR bias critique (Serra; Huang et al. 2023; Morreale et al. 2025), AMT and F0 methods, annotator-disagreement modelling, mixed models and equivalence testing, phylogenetic comparative musicology.
- **Search not done:** neither line could search CNKI or Wanfang. Chinese-language computational work in 《中国音乐学》, 《音乐研究》 and 《中央音乐学院学报》, and the acoustics work of 韩宝强 and 李伟's Fudan group, may already partly address H1, H11 or H14. A CNKI pass is needed before claiming novelty in Chinese scholarship.

### 5.3 Two must-cite overlaps to resolve first

1. **Bu et al. 2025** (arXiv:2512.14758): jianpu OCR on the same anthology. Either the same pipeline or the closest prior work.
2. **Jing Luo's MGD** (more than 31,000 symbolic songs organized by province) and its 1,214-song, seven-region Han subset. It may share sources with the corpus, and it may be the only existing source of multiple annotations.

---

# Part A — Humanities annotated survey (Q1–Q5)

Verification tags: [V] confirmed this session; [V-partial] partly confirmed (the missing element is named); [R] recalled, not confirmed.

## A1. Inter-transcriber disagreement: error, interpretation, or evidence about the music?

### A1.1 Foundational Western ethnomusicology

**Seeger, Charles. 1958. "Prescriptive and Descriptive Music-Writing." *The Musical Quarterly* 44(2): 184–195. doi:10.1093/mq/XLIV.2.184. [V]**
- *Claim:* Staff notation is mainly *prescriptive*: it tells a performer who already knows the tradition how to make sound. *Descriptive* writing, which records how a particular performance actually sounded, needs other means. Seeger argued for the automatic "melograph" for this purpose. Notation always leaves out what the writer's culture takes for granted.
- *Method:* Conceptual argument, with comparisons between staff notation and electronic pitch tracings.
- *Relevance:* This is the central frame for the paper. Anthology 简谱 scores are prescriptive and written for insiders. Bilibili audio transcribed to MIDI is a crude descriptive layer. The two will disagree because they encode different things, not only because one of them is wrong. Seeger's distinction lets the paper reframe "AMT error against anthology" as "descriptive layer against prescriptive layer."

**England, Nicholas M. (organizer), with Robert Garfias, Mieczyslaw Kolinski, George List, Willard Rhodes; Charles Seeger (moderator). 1964. "Symposium on Transcription and Analysis: A Hukwe Song with Musical Bow." *Ethnomusicology* 8(3): 223–277 (England's introduction pp. 223–233). [V for authors, venue, issue and introduction pages; the full page range of the symposium is R]**
- *Claim and method:* Four specialists transcribed the same recording (a Hukwe ǃXũ song with musical bow, recorded by England) independently, without talking to one another, and with minimal contextual information. Their results were then compared. Garfias's contribution, which I checked, says transcription is necessarily selective. He used staff notation for the bow and a graph for the voice, and he left out the overtone layer because it was not audible throughout. Seeger contributed a melograph reading.
- *Relevance:* This is the classic natural experiment in inter-transcriber disagreement. The transcriptions differed in segmentation, pitch reference, and which layers were notated at all. The usual reading in the field is that the differences show each transcriber's analytical decisions, not mistakes. This is the direct precedent for treating expert disagreement as a *reference envelope* rather than noise. **Inference (mine):** where the four transcriptions diverged most (sustained pitches with fluctuating intonation, and the bow's overtone layer) tracks where the music itself is acoustically ambiguous. That supports "disagreement as fingerprint of the music's properties." I did not do a fresh reading for this survey, so treat it as a hypothesis to check against the symposium text.

**List, George. 1974. "The Reliability of Transcription." *Ethnomusicology* 18(3): 353–377. [V]**
- *Claim (summary recalled, [R] for detail):* An empirical test of how consistent transcriptions are, within one transcriber over time and between transcribers. List found reasonable consistency for pitch contour and much lower consistency for exact pitch inflection, ornaments, and rhythmic detail in free-rhythm passages.
- *Relevance:* This is the earliest quantitative precedent for measuring inter-transcriber agreement *per feature*. It points toward the paper's per-feature envelope (pitch, ornament, segmentation, rhythm).

**Ellingson, Ter. 1992. "Transcription" (pp. 110–152) and "Notation" (pp. 153–164), in Helen Myers (ed.), *Ethnomusicology: An Introduction*. London: Macmillan / New York: Norton. [V for the "Transcription" chapter and pages; the "Notation" chapter's pages are R]**
- *Claim:* Gives a history of transcription from Abraham & Hornbostel through the melograph. Argues that transcription is a form of representation shaped by the transcriber's purpose and the notational system, and is never a neutral copy of sound.
- *Relevance:* The standard review citation. Use it to anchor the claim that "a transcription is a theory of the music."

**Abraham, Otto & Erich M. von Hornbostel. 1909/1910. "Vorschläge für die Transkription exotischer Melodien." Translated by George and Eve List as "Suggested Methods for the Transcription of Exotic Music," *Ethnomusicology* 38(3) (1994): 425–456. [V-partial: confirmed via 周凯模 2004's bibliography; the original German venue (*Sammelbände der IMG*) is R]**
- *Claim:* Proposes extensions to staff notation (signs for cents deviation, glides, unstable pitches).
- *Relevance:* Disagreement about how to notate microtonal and gliding pitch has been built into comparative musicology from the start. The 简谱 diacritics ↑4 and ↓7 used for 苦音 are a local descendant of the same problem.

**Nettl, Bruno. 2005 (1st ed. 1983). *The Study of Ethnomusicology: Thirty-One Issues and Concepts*. Urbana: University of Illinois Press. Chapter "I Can't Say a Thing until I've Seen the Score: Transcription." [V]**
- *Claim:* Traces how transcription moved from the field's core method to a contested practice. Distinguishes transcription for analysis from transcription for preservation. Notes that insiders and outsiders hear and segment differently.
- *Relevance:* Use for the insider/outsider dimension. The Chinese anthology transcribers were (mostly) cultural insiders trained in conservatory solfège. A Western-trained AMT model is a third kind of "listener."

**Marian-Bălaşa, Marin. 2005. "Who Actually Needs Transcription? Notes on the Modern Rise of a Method and the Postmodern Fall of an Ideology." *The World of Music* 47(2): 5–29. [V]**
- *Claim:* A critique of transcription as an ideology tied to scientism and to staff-notation literacy.
- *Relevance:* A sceptical voice the reviewer may raise. It also justifies treating the score as a cultural artefact (a fingerprint of a notational tradition), not as ground truth.

**Stanyek, Jason (ed.). 2014. "Forum on Transcription." *Twentieth-Century Music* 11(1): 101–161. [V]**
- *Claim and method:* Short position statements from many leading practitioners on how transcription is understood today: as a creative, interpretive, and media-specific act. The forum explicitly references the 1964 Hukwe symposium as precedent.
- *Relevance:* A recent humanities statement that disagreement is constitutive of transcription. Useful against a reviewer who says "just use the consensus score."

**Ozaki, Yuto, John McBride, Emmanouil Benetos, Peter Q. Pfordresher, Joren Six, Adam T. Tierney, Polina Proutskova, Emi Sakai, Haruka Kondo, Haruno Fukatsu, Shinya Fujii & Patrick E. Savage. 2021. "Agreement among Human and Automated Transcriptions of Global Songs." *Proc. 22nd ISMIR*, pp. 500–508. [V]**
- *Claim:* Three expert transcribers of 32 global traditional song recordings agreed about 90% of the time (κ ≈ 0.7). Agreement between humans and ten automated methods was under 60% (κ < 0.4). No automated method dominated.
- *Method:* Independent staff-notation transcriptions in MuseScore, quantized to 12-TET (A4 = 440 Hz). Pitch sequences were aligned with Needleman–Wunsch, and rhythm was excluded.
- *Relevance:* **This is the closest methodological precedent for "is the model inside the human envelope?"** It is a bridge to the technical line. Its 12-TET quantization and pitch-only design are exactly the limits this paper should go beyond (cents, 润腔, 散板 timing).

### A1.2 Chinese-language discussion of 记谱 (notation and transcription)

**周凯模 (Zhou Kaimo). 2004. 《音乐人类学的"记谱与分析"之方法讨论》 (*Yinyue renleixue de "jipu yu fenxi" zhi fangfa taolun*, "On method in 'transcription and analysis' in music anthropology"). 《杭州师范学院学报（社会科学版）》 2004(6). [V]**
- *Claim:* European staff notation comes from church and concert practice and cannot adequately record or explain 口传身授 (oral, body-to-body) traditions. Any notation can only "approximately" restore the sound. Using Kartomi's insider/outsider and experience-near/experience-distant distinctions, Zhou says different cultural positions yield "considerably different" transcriptions of the same text.
- *Method:* Review and programmatic essay, including a practical step-by-step transcription protocol: listen through, slow down ornamented passages, isolate unclear intervals.
- *Relevance:* A Chinese-language statement that transcriber position produces systematic difference. It supports the "fingerprint" thesis from inside Chinese scholarship.

**杨荫浏 (Yang Yinliu). 1962. 《工尺谱浅说》 (*Gongchepu qianshuo*, "A simple introduction to gongche notation"). 北京：音乐出版社. [V]**
- *Claim (content partly R):* A concise overview of 工尺谱 and its translation into modern notation. A long-standing theme in Yang's work is that traditional scores record a skeleton (骨干), and that the 腔 (melodic elaboration) is supplied by oral practice.
- *Relevance:* This is the Chinese prescriptive tradition in Seeger's sense. "谱简腔繁" (sparse score, rich performance) is a native statement that score and sound are expected to disagree.

**Yang Mu 杨沐. 1994. "Academic Ignorance or Political Taboo? Some Issues in China's Study of Its Folk Song Culture." *Ethnomusicology* 38(2): 303–320 (pages R). [V for author, year, title, venue]**
- *Claim:* PRC folk-song scholarship systematically avoided certain topics, especially erotic song and social context, because of political constraint rather than ignorance. Anthologies reflect selection and editing.
- *Relevance:* The anthology corpus is a *curated and censored* sample, not a random draw from practice. Stephen Jones (blog, 2019 [V]) says parts of this critique are now dated, so cite both.

**Yang Mu. 2003. "Ethnomusicology with Chinese Characteristics? A Critical Commentary." *Yearbook for Traditional Music* 35. [V for title and venue; volume and pages R]**
- *Relevance:* A critique of PRC 民族音乐学 paradigms. Gives a reviewer-proof framing of how editorial ideology shapes notated corpora.

**李志成 & 詹庆芬 (Li Zhicheng & Zhan Qingfen). 2025. 《文献评述：中国民间音乐研究范式的变迁》 ("A literature review of paradigm change in Chinese folk-music research"). 《社会科学与教育》 2025(10): 61–66. [V; a minor venue]**
- *Claim:* Chinese folk-music research has moved from a "曲理–乐理" morphological paradigm toward an anthropological "音乐–文化–人" (music–culture–people) paradigm. 音腔论 and 腔音列 are flagged as the key native analytical units, and the use of European aesthetic and evaluative standards is criticized.
- *Relevance:* A recent overview to cite for the shape of the Chinese debate. Do not rely on it for primary claims.

**Synthesis for Q1 (consensus vs inference).**
- *Consensus:* Transcription is selective and theory-laden, and experts disagree, especially on microtonal pitch, ornaments, and free rhythm (Seeger, England, List, Ellingson, Nettl, Stanyek; 周凯模 in Chinese).
- *Empirical:* Expert agreement on pitch sequence can be high (κ ≈ 0.7 in Ozaki et al. 2021) when everyone uses the same notational frame (12-TET staff).
- *Inference (the paper's contribution):* disagreement is *structured*. It concentrates on features that (a) the notational tradition under-specifies and (b) carry regional style, such as 润腔 and neutral intervals. If that holds, the disagreement pattern is a fingerprint of the region, not noise. No study I found tests this directly on Chinese material. This is a genuine gap.

---

## A2. Chinese folk-song transcription conventions: history and assumptions

### A2.1 Notation systems

**工尺谱 (gongche notation).** A solmization-character system (合 四 一 上 尺 工 凡 六 五 乙). Beats are marked with 板眼 signs (板 for strong beats, 眼 for weak). Yang Yinliu 1962 [V] is the standard introduction. *What it encodes:* relative pitch degree, 板眼 metric frame, and sometimes ornament signs. *What it discards:* exact durations within a beat, intonation, timbre, and most 润腔. **Encoding assumption:** the performer already knows the tune's 腔. A 2023 review of 《中国工尺谱集成》 on 华音网 [V] describes the large mid-century collecting effort by Yang Yinliu's generation and its continuation since the 1980s.

**简谱 (jianpu, numbered notation).** It comes from the French Galin–Paris–Chevé cipher system and reached China via Japan around 1900. The first Chinese-compiled jianpu songbook is 沈心工 (Shen Xingong)'s 《学校唱歌集》 (1904). It spread through the 学堂乐歌 (school song) movement and, in the 1930s, the 救亡歌咏 (national-salvation singing) movement [V: French Wikipedia; Baidu/encyclopaedic entries; a HAL thesis lists six origin hypotheses]. *What it encodes:* scale degree relative to a movable tonic (1 = 宫 or a stated key), duration as Western divisions (underlines and dots), barlines, time signatures, and a few diacritics. *What it discards or distorts:*
1. **Tuning.** Jianpu implicitly assumes 12-TET or a diatonic frame. Neutral and characteristic pitches are written as accidentals or arrows. In the 苦音 (*kuyin*, "bitter tone") mode of 秦腔 and northwestern song, 4 is slightly sharp and 7 slightly flat, written ↑4 and ↓7. Secondary sources say 欢音 (*huanyin*, "joyful tone") 4 sits "slightly above natural 4 but short of #4" [V: 信阳师范学院学报 2021 PDF; 华音网 2026 article on 秦派葫芦丝]. The *magnitude* of these deviations is absent from the score.
2. **Metre.** Jianpu forces barring. **散板 (sanban, free metre)** is marked only by a sign, "サ", for which there is a Unicode encoding proposal: Eiso Chan, "Proposal to encode the Sanban Sign for Chinese folk music and local operas," L2/22-207 / L2/22-207R, 2022 [V]. Durations inside 散板 passages are nominal.
3. **润腔 (runqiang, "melodic moistening": ornaments, slides, vibrato, dynamic and timbral inflection).** Only partly captured, by grace notes, slur signs, and a few symbols (for example 波音 mordents and 滑音 slides). Most of it is left to the singer.
4. **Text-setting.** Lyrics are underlaid syllable by syllable. 衬词 (*chenci*, vocables and filler syllables) are usually printed in smaller type or parentheses. Dialect pronunciation is glossed in notes, not in the score itself.

A 华音网 2023 essay on 散板 aesthetics [V] states the native principle directly: "所谓'谱简腔繁'，中国的传统记谱法习惯于只记录骨干音" (so-called "sparse score, rich performance": traditional Chinese notation habitually records only the skeletal pitches).

### A2.2 The 集成 (anthology) project and its editorial assumptions

**《中国民间歌曲集成》 (*Zhongguo minjian gequ jicheng*, Anthology of Chinese Folk Songs). 总编辑部 (general editorial board), chief editor 吕骥 (Lü Ji). Published by province from the late 1980s (Macau volume later), by 中国ISBN中心 / 人民音乐出版社. [V for structure; exact series publisher varies by volume]**
- Verified facts (from the Macau-volume front matter on macaudata.mo and from cefla.org.cn):
  - It is one of four music 集成 (anthologies): folk song, instrumental music, 曲艺 (narrative singing) music, and opera music.
  - An earlier 1960s attempt was interrupted. Work restarted in 1979 under 吕骥.
  - There are 31 provincial volumes (including Taiwan), each typically selecting **800–1,500 songs**.
  - Each volume adds an overview (概述), genre explanations (歌种释文), and dialect glosses.
  - The editorial principle is that included songs "原则上要求配有原始录音资料" (should in principle be backed by original recordings).
  - Each volume is organized as images, text, scores, and singer biographies.
- *Implicit assumptions (inference; check against a volume's 凡例 / editorial guidelines, which I could not access online):*
  1. Classification is **by genre first** (号子 work songs, 山歌 mountain songs, 小调 ditties, plus 灯歌 lantern songs, 风俗歌 ritual songs, and so on) **within administrative province**. It is *not* by 色彩区. Any region label in the dataset therefore inherits province boundaries, which may not match style boundaries.
  2. One "representative" variant is chosen and normalized into 简谱. Variant multiplicity is collapsed.
  3. Transcribers were often local cultural-bureau (文化馆) workers, of varying training. Volume and transcriber are therefore confounds.
  4. Scores were edited toward legibility (barring, tonic choice, 调式 / mode labels such as 徵调式 *zhi* mode).
- **Gap:** I could not find the 集成's internal 编辑方案 / 编辑规格 / 记谱 rules online. They exist as internal 总编辑部 documents. *Recommendation:* quote the 凡例 page of each provincial volume in the dataset, and treat "volume" as a random effect in the models.

**Bu Fan, Rongfeng Li, Zijin Li, Ya Li, Linfeng Fan & Pei Huang. 2025. "The Renaissance of Expert Systems: Optical Recognition of Printed Chinese Jianpu Musical Scores with Lyrics." arXiv:2512.14758. [V]**
- *Claim:* A modular, largely unsupervised OMR pipeline for jianpu with lyrics, producing MusicXML and MIDI. Evaluated on "The Anthology of Chinese Folk Songs," it digitized more than 5,000 melodies (over 300,000 notes) and a lyric-aligned subset of more than 1,400 songs (BUPT with the Central Conservatory).
- *Relevance:* **Directly overlaps with the paper's OCR layer.** Either the pipeline is the same, or this is the closest prior work and must be cited. It also shows what OMR can carry over (pitch digits, octave dots, durations, ties) and what it cannot (handwritten 润腔 annotations, dialect glosses).

### A2.3 Theories of the "note" itself: 音腔, 腔音, 润腔

**沈洽 (Shen Qia). 1982–1983. 《音腔论》 (*Yinqiang lun*, "On the tone-cavity / pitch-inflected tone"). 《中央音乐学院学报》 1982(4): 12–21; 续 (continuation) 1983. Reissued as a book (ISBN 9787552316339; publisher and year R). [V for the 1982 article and the book's existence]**
- *Claim:* The minimal unit of Han music is not a fixed pitch but a 音腔: a tone with a head, body, and tail (头/腹/尾) whose pitch, dynamics, and timbre move. The 音腔 is the irreducible "cell" of Chinese musical sound, in contrast to the Western note as point-pitch. (Koizumi Prize citation, Tokyo University of the Arts [V].)
- *Relevance:* **This is the most important native theoretical warrant for the paper's noisy-layer argument.** A MIDI note is ontologically a Western note. AMT "errors" at note onsets and offsets, insertions of extra notes, and pitch-bend drift are, in Shen's terms, failures to represent 音腔. This predicts *where* AMT should fail: the 头 and 尾 of 音腔, and slides.

**王耀华 (Wang Yaohua). 《中国传统音乐结构学》 (*Zhongguo chuantong yinyue jiegouxue*, "Structure of Chinese traditional music"). 福建教育出版社. [V-partial: the content (腔音 → 腔音列 → 腔节/腔韵 → … → 腔系, eight levels) was confirmed via 云村寨 and 李志成 2025; publisher and year (c. 2005) R]**
- *Claim:* Builds a hierarchy of structural units on 腔音 (equivalent to Shen's 音腔). Among them, **腔音列** (*qiangyin lie*, three-note interval cells) are regionally diagnostic.
- *Relevance:* Gives a native feature set for regional style that can be operationalized as n-gram cells of scale-degree intervals.

**于会泳 (Yu Huiyong). 1963 (mimeograph). 《腔词关系研究》 (*Qiang ci guanxi yanjiu*, "Study of tune–text relations"). About 120,000 characters and 230+ musical examples. [V for the work and date (Chinese Wikipedia)]. Also 1959, 《关于我国民间音乐调式的命名》 ("On naming the modes of Chinese folk music"), 《音乐研究》. [V]**
- *Claim:* Tune–text relations (腔词关系) systematically shape melody. Yu named modes by 宫商角徵羽 (*gong shang jue zhi yu*) and introduced "主宰音程关系" ("dominant interval relations"). **The attribution of "腔音列" to 于会泳 as its originator is widely repeated but [R]. I did not verify it.**
- *Relevance:* Tone-language text-setting is a strong regional feature in Han song, because dialect tones constrain melodic contour. It is absent from MIDI unless lyrics are aligned.

**董维松 (Dong Weisong). 2004. 《论润腔》 (*Lun runqiang*, "On runqiang"). 《中国音乐》 2004(4). [V]**
- *Claim:* A systematic typology of 润腔: pitch-type (音高性), rhythmic-type (节奏性), dynamic-type (力度性), and timbral-type (音色性). It builds on 于会泳's earlier categories (a 华音网 2022 guqin study [V] attributes the four-way typology to both Yu and Dong). A 中国人民大学 lecture by 郭克俭 [V] reviews sixty years of 润腔 research and names 薛良 as a key earlier contributor.
- *Relevance:* A ready-made taxonomy for *where AMT should fail*. Pitch-type 润腔 shows up as pitch-bend and insertion errors. Rhythmic-type shows up as onset and segmentation error. Timbral-type is invisible to MIDI. This gives a per-feature failure-mode hypothesis.

**Synthesis for Q2.** Both Chinese notation traditions are *prescriptive skeletons*. They encode: scale degree relative to a movable 宫; a 板眼 or bar metric frame; text underlay; and the genre label. They discard or under-specify: absolute intonation and neutral intervals; 润腔; 散板 timing; timbre and vocal production (for example 真假声 true/falsetto alternation, and 甩腔 flung phrase-endings); and dialect phonetics. The 集成 adds an editorial layer: province-by-genre classification, single-variant selection, and possible normalization toward conservatory theory. **Consensus:** the skeleton principle (谱简腔繁). **Inference:** that the normalization is *regionally uneven*, i.e. that some provinces' editors notated more 润腔 than others. This is testable (count ornament and grace-note density per volume) and is a key confound for any 色彩区 claim made from notation alone.

---

## A3. 色彩区 theories and their computational testing

### A3.1 The core theory

**苗晶 (Miao Jing) & 乔建中 (Qiao Jianzhong). 1987. 《论汉族民歌近似色彩区的划分》 (*Lun Hanzu minge jinsi secaiqu de huafen*, "On the division of Han folk song into approximate colour regions"). 北京：文化艺术出版社. [V for authors, title, and 1987 publisher. It received the first Chinese Academy of Arts research award (third class), per CASS 2024 [V]. An earlier journal version is commonly mentioned; venue and date R]**
- *Claim:* Han folk song divides into **ten approximate colour regions plus one "special region" (特区, the Hakka 客家)** [V from two independent sources]:
  1. 东北部平原区 (Northeastern Plains: Hebei, Shandong, NE Henan, N Jiangsu, Liaoning, Jilin, Heilongjiang)
  2. 西北部高原区 (Northwestern Plateau: Shanxi, W Inner Mongolia, most of Ningxia, N Shaanxi, Gansu, Guanzhong, E Qinghai)
  3. 江淮区 (Jiang–Huai: N Jiangsu, N Anhui, SE Henan), explicitly described as **transitional** ("南北兼及、互有交融": partaking of both north and south, mutually blended)
  4. 江浙平原区 (Jiangsu–Zhejiang Plains)
  5. 闽台区 (Fujian–Taiwan)
  6. 粤区 (Cantonese)
  7. 江汉区 (Jiang–Han: Hubei and adjacent areas)
  8. 湘区 (Hunan)
  9. 赣区 (Jiangxi)
  10. 西南高原区 (Southwestern Plateau)
  11. 客家区 (Hakka, as 特区)
- *Method:* Qualitative, expert synthesis. The **defining factors are mostly extra-musical**: geography and landform, ancient culture zones, **dialect**, social custom, population movement, and folk-song diffusion ("地理分布、古代文化、语言、社会、人口变迁和民歌传播") [V: secondary summary in 美篇 / meipian; 明立國 (Ming Li-kuo), 南華大學 (Nanhua University) PDF]. Musical evidence consists of exemplary tunes, characteristic 音调 (tune-types), modal preferences, and genre distributions. **The secondary sources do not show explicit measurable criteria or a decision rule for boundaries.** The word "近似" (approximate) is itself a hedge.
- *Relevance:* This is the thesis's anchor. **Important for framing:** because the regions were defined partly by *dialect and geography*, a model that "recovers" them from melody could be detecting dialect-driven text-setting (Q2: 腔词关系). That is a mechanism, not a confound, but it must be said explicitly. Also, the boundaries do not follow provinces, while the 集成 does. Assigning songs to regions needs county-level metadata, and Hakka songs need a separate flag.

**乔建中 (Qiao Jianzhong). 1998 (rev. 2009). 《土地与歌——传统音乐文化及其历史地理研究》 (*Tudi yu ge*, "Land and song: traditional music culture and its historical geography"). 济南：山东文艺出版社. Includes 〈音地关系探微：从民间音乐的分布作音乐地理学的一般探讨〉 ("Exploring music–land relations: a general music-geographical inquiry from the distribution of folk music"). [V]**
- *Claim:* Develops 音乐地理学 (music geography): the distribution of musical traits follows land, water systems, and historical migration. It includes a case study of 信天游 (*xintianyou*, the Northern Shaanxi mountain-song genre).
- *Relevance:* The theoretical bridge from 色彩区 (static region) to diffusion (Q5). Qiao's framing already treats region and contact as two sides of one geography.

**杨匡民 (Yang Kuangmin). 1987. 《民歌旋律地方色彩的形成及色彩区的划分》 ("The formation of local colour in folk-song melody and the division of colour regions"). 《中国音乐学》 1987(1). [V]**
- *Claim (content R):* A parallel, partly earlier, division from the Hubei / Jiang–Han perspective. Yang is associated with the **三声腔** (three-tone cell) concept: regional colour comes from characteristic three-note cells (for example 宫–角–徵 vs. 徵–宫–商). He later wrote, with 周耘 (Zhou Yun), *巴音、吴乐和楚声——长江流域的传统音乐文化* (Ba sounds, Wu music and Chu voices: traditional music culture of the Yangtze basin) [V].
- *Relevance:* **The most operationalizable 色彩区 theory.** Three-note cells map directly onto interval trigrams that can be extracted from symbolic data. Strongly recommended as the feature definition for H-tests.

**Other region-division works** listed in a 台灣師大 (NTNU, Taiwan) thesis's literature review [V for existence; details R]: 江明惇 〈试论江南民歌的地方色彩〉 ("On local colour in Jiangnan folk song"); 黄允箴 (Huang Yunzhen) 〈论北方汉族民歌的色彩划分〉 ("On colour division in northern Han folk song").

**江明惇 (Jiang Mingdun). 1982. 《汉族民歌概论》 (*Hanzu minge gailun*, "Introduction to Han folk song"). 上海：上海文艺出版社. [V; won the first national State Education Commission prize for outstanding textbooks]**
- *Claim (R for detail):* The standard textbook. Organizes Han folk song by genre (号子, 山歌, 小调) and by regional style. Treats local colour (地方色彩) as coming from dialect, 音调, mode, and 润腔.
- *Relevance:* A canonical description of features per region. It is the conservatory "ground truth" that anthology editors and many Bilibili singers were trained on. That is a possible source of circularity: trained singers performing textbook regional style.

**杜亚雄 (Du Yaxiong).**
- 1993. Article on the "music dialect areas" (音乐方言区) of Han folk song, 《中央音乐学院学报》 1993. **[V-partial: cited in English by Luo et al. 2019 as "Y. Du, 'The music dialect area and its division of Han Chinese folk songs', *Journal of Central Conservatory of Music*, 1993." I could not verify the Chinese title. Possibly 《汉族民歌的音乐方言区及其划分》 (unverified), which is a guess and must not be cited without checking CNKI.]**
- 2011. Proposal for a morphological classification of Han folk songs, 《乐府新声》 2011(1). [V via a library abstract] The paper rejects the 号子 / 山歌 / 小调 (performance-context) taxonomy as a basis for morphology. It proposes a three-level classification: **(1) metre (节拍), (2) range (音域), (3) phrase-final notes (乐句结音)**.
- *Relevance:* The 2011 scheme is **directly computable from symbolic data**, so it gives the humanities warrant for a feature set that is not the 集成 genre label. The "music dialect" metaphor makes the dialect–melody coupling explicit.

**周青青 (Zhou Qingqing).**
- 2003. 《中国民间音乐概论》 (*Zhongguo minjian yinyue gailun*, "Introduction to Chinese folk music"). 北京：人民音乐出版社. [V]
- 2009. 《我国民歌调式分布的统计与阐释》 ("Statistics and interpretation of the distribution of modes in Chinese folk song"). 《音乐研究》 2009(2): 1–20. [V]
- 2011. 《从房陵民歌看民歌旋律的"底层"、"借用"与"交融"》 ("'Substratum', 'borrowing' and 'blending' in folk-song melody: the case of Fangling folk songs"). 《中国音乐》 2011(1). [V]
- Also 《北京通州运河号子中的山东音乐渊源》 ("Shandong musical origins in the Tongzhou Grand Canal work songs of Beijing"). [V title]
- *Claim:* The 2009 paper is **a quantitative, statistical study of mode distribution across Chinese folk song by region**, arguing that mode follows 音调结构 (tune structure). The 2011 paper separates a melodic *substratum*, *borrowings*, and *blending* in a border area (Fangling, NW Hubei, on the Shaanxi–Sichuan–Henan border).
- *Relevance:* **Zhou 2009 is a Chinese-language pre-computational test of regional feature distributions and should be cited as the closest native precedent.** Zhou 2011 gives the exact vocabulary the "feature-sharing as cultural interaction" thesis needs: 底层 / 借用 / 交融 (substratum / borrowing / blending). The canal work-song paper is a diffusion case along a trade route.

**沈洽 (Shen Qia) 音腔论** (see §A2.3). It is not a region theory, but 音腔 shapes (slide types, head and tail inflections) are claimed to be regionally variable. That gives a sub-note feature dimension notation cannot carry.

### A3.2 Can notation or AMT capture the defining features?

| 色彩区 feature (native term) | In 集成 jianpu? | In AMT-MIDI? | Notes |
|---|---|---|---|
| Mode / scale (调式, 五声 pentatonic and 七声 heptatonic, 清角 *qingjue* / 变宫 *biangong*) | Yes (degrees and mode label) | Partly (pitch classes; tonic inference is fragile) | Zhou 2009 statistics are a baseline |
| 腔音列 / 三声腔 (three-note cells) | Yes | Yes, if note segmentation is right | Most robust symbolic feature |
| Characteristic intervals (e.g. Northern Shaanxi 4ths, Hunan major/minor 3rd mixing) | Yes | Yes | Luo et al. 2019 cite these |
| Neutral / inflected pitches (苦音 ↑4 / ↓7, 中立音 neutral tones) | Only as sign; magnitude lost | **Better** in cents, if pitch tracking is kept | Audio has an advantage here |
| 润腔 (four types per 董维松) | Sparse grace notes | As insertions or pitch-bend; often "errors" | Prime failure locus |
| 散板 timing | Nominal durations | Real timing, but beat-tracking fails | Exclude from metric features |
| 衬词 vocables, text-setting (腔词关系) | Lyrics present | Absent | Needs lyric alignment |
| Timbre / vocal production (真假声, 高腔 *gaoqiang* high-register singing) | No | No (MIDI) | Outside both layers; needs audio features |
| Phrase-final notes (结音), range (音域), metre (节拍) (杜亚雄 2011) | Yes | Range and finals yes; metre fragile | Directly computable |

### A3.3 Computational work on Chinese folk-song regions

**Luo, Jing, Xinyu Yang, Shulei Ji & Juan Li. 2019. "MG-VAE: Deep Chinese Folk Songs Generation with Specific Regional Style." arXiv:1909.13287 (CSMT 2019). [V]**
- *Claim and method:* A VAE that disentangles pitch and rhythm style from content, conditioned on region, trained on a MIDI dataset of more than 2,000 Chinese folk songs across regions. It cites Du 1993 and Miao & Qiao. It states that Han regional style "is mainly reflected in rhythm and pitch-interval patterns" and follows dialect divisions.
- *Relevance:* Shows region is learnable from symbolic melody. Labels are province or ethnicity, not 色彩区. Generation, not hypothesis testing.

**Luo Jing et al. *MGD: Large-Scale Chinese Folk Songs Dataset* (2014–2023; project page chinglohsiu.github.io). [V]**
- More than 31,000 Chinese folk songs in symbolic format, organized by 31 provinces, from four named reference collections. The same page lists a separate 2021–2022 resource of **1,214 Han folk songs from seven regions with five annotations and partial audio–score alignment**.
- *Relevance:* **Possibly the largest overlapping corpus. Check whether its source is the 集成.** The 1,214-song, five-annotation subset could provide multi-annotator data for the disagreement analysis. Its provenance and licence need checking.

**Li, Juan, Jianhang Ding & Xinyu Yang. 2017. "The Regional Style Classification of Chinese Folk Songs Based on GMM-CRF Model." ACM conference proceedings, doi:10.1145/3057039.3057069. [V]**
- Temporal model on symbolic features for regional classification. A follow-up "Regional classification of Chinese folk songs based on CRF model" (Multimedia Tools and Applications; authors and year R) [V title].

**Khoo, Suisin, Zhihong Man & Zhenwei Cao. 2012. "Automatic Han Chinese Folk Song Classification Using the Musical Feature Density Map." *Proc. 6th ICSPCS*, pp. 1–9; and "…Using Extreme Learning Machines," Springer, 2012/2013 chapter. [V]**
- Five Han regions; symbolic encoding as a "musical feature density map." Most likely drawn from Essen *han*.

**Essen Folksong Collection, Chinese subsets (*han*, *natmin*), encoded under Helmut Schaffrath. About 2,231–2,240 Chinese tunes. [V: Dahlig-Turek / Sapp, *Muzyka*; emusicology.org]. Morrison, Demorest & Pearce (2019, OUP chapter "Cultural Distance: A Computational Approach…", book title R) used 858 Essen Chinese songs to train IDyOM. [V]**
- *Relevance:* The default "Chinese folk song" corpus in MIR. Sources are Chinese anthologies of the 1950s–80s (R). Encoded in EsAC by German encoders, which adds yet another transcription layer. Region labels are coarse. Useful as an external replication set and as a cautionary example.

**Zhou, Monan, Shenyang Xu, Zhaorui Liu, Zhaowen Wang, Feng Yu, Wei Li & Baoqiang Han. 2025. "CCMusic: An Open and Diverse Database for Chinese Music Information Retrieval Research." *TISMIR* 8(1): 22–38. doi:10.5334/tismir.194. [V]**
- Includes a "Bel Canto & Chinese Folk Singing" dataset (for singing-style classification) and a Chinese pentatonic-mode dataset. 韩宝强 (Han Baoqiang, Central Conservatory acoustics) is a co-author.
- *Relevance:* An audio resource. It does not test 色彩区.

**Repetto, Rafael Caro & Xavier Serra. 2014. "Creating a Corpus of Jingju (Beijing Opera) Music and Possibilities for Melodic Analysis." *Proc. ISMIR 2014*. [V]**
- The CompMusic model for a culture-specific corpus (audio, scores, lyrics, metadata) on a Chinese genre. Shows the value of native analytical concepts (板式 *banshi* metrical-tempo types, 行当 *hangdang* role types) as labels.

**Assessment.** The Chinese MIR work on regional classification exists but is **thin on hypothesis testing**. Labels are province- or ethnicity-level. Feature sets are generic (pitch histograms, interval n-grams). Studies report accuracy, not which features carry region, and **none I found evaluates against the Miao–Qiao 色彩区 boundaries or models transcriber or source variance.** The closest native quantitative work is 周青青 2009. **Gap and opportunity:** the first explicit, feature-attributed test of 色彩区 with source and transcriber as random effects.

---

## A4. Epistemic bias of Western-trained MIR tools on non-Western music

**Serra, Xavier. 2011. "A Multicultural Approach in Music Information Research." *Proc. 12th ISMIR*, pp. 151–156. [V]**
- *Claim:* MIR tools embed Western concepts (equal temperament, chords, metre). The paper launches CompMusic (2011–2017), covering Hindustani, Carnatic, Turkish makam, Arab-Andalusian, and Beijing opera. It calls for culture-specific corpora, models, and collaboration with musicologists.
- *Relevance:* The programmatic MIR ancestor. Jingju was one of its five traditions, so there is direct Chinese precedent.

**Tzanetakis, George, Ajay Kapur, W. Andrew Schloss & Matthew Wright. 2007. "Computational Ethnomusicology." *Journal of Interdisciplinary Music Studies* 1(2): 1–24. [V for authors, venue, pp.; issue number R]**
- *Claim:* Defines computational ethnomusicology. Warns that tools should serve ethnomusicological questions, not impose MIR task definitions.

**Cornelis, Olmo, Micheline Lesaffre, Dirk Moelants & Marc Leman. 2010. "Access to Ethnic Music: Advances and Perspectives in Content-Based Music Information Retrieval." *Signal Processing* 90(4): 1008–1031 (pages R). [V]**
- *Claim and method:* Surveyed ISMIR proceedings and found ethnic music in only about 5.5% of papers. A questionnaire to 44 European archives drew 7 responses. Argues content-based MIR rests on Western assumptions. Explicitly notes that transcriptions are reductions and the same music is represented very differently by different transcribers.
- *Relevance:* An early empirical bias statement, and it already links transcriber variation to the problem.

**Holzapfel, André, Bob L. Sturm & Mark Coeckelbergh. 2018. "Ethical Dimensions of Music Information Retrieval Technology." *TISMIR* 1(1): 44–55. doi:10.5334/tismir.13. [V]**
- *Claim:* MIR technology is not value-neutral. Design choices (data, representations, evaluation) have ethically relevant effects, including on non-Western music communities.

**Born, Georgina. 2020. "Diversifying MIR: Knowledge and Real-World Challenges, and New Interdisciplinary Futures." *TISMIR* 3(1): 193–204. doi:10.5334/tismir.58. [V]**
- *Claim:* Advocates an "agonistic" interdisciplinarity in which the humanities are not service disciplines to MIR.
- *Relevance:* Supports the paper's stance of giving humanities and technical analysis equal weight.

**Huang, Rujing Stacy, Andre Holzapfel, Bob L. T. Sturm & Anna-Kaisa Kaila. 2023. "Beyond Diverse Datasets: Responsible MIR, Interdisciplinarity, and the Fractured Worlds of Music." *TISMIR* 6(1): 43–59. doi:10.5334/tismir.141. [V]**
- *Claim and method:* A thematic analysis of 78 ISMIR papers mentioning "ethnomusicology" (25 coded in depth). It argues that adding datasets is not enough: MIR must re-examine its **ontology, epistemology, methodology, and axiology**. Case studies on Asian philosophical ethics and Irish traditional music.
- *Relevance:* **The main critical frame for TISMIR reviewers.** The paper's "three-system tension" (music / Chinese notation / Western models) is an ontological argument in exactly this sense. Cite it, and show the paper doesn't just "add a Chinese dataset."

**Panteli, Maria, Emmanouil Benetos & Simon Dixon. 2018. "A Review of Manual and Computational Approaches for the Study of World Music Corpora." *Journal of New Music Research* 47(2): 176–189. doi:10.1080/09298215.2017.1418896. [V]**
- *Claim:* Reviews corpus studies. Reports that Western music is measurably more equal-tempered, and that features designed for Western music bias world-music comparison. See also Panteli et al., "A computational study on outliers in world music" (PLOS ONE 2017; 8,200 recordings from 137 countries) [V title].

**Morreale, Fabio, Marco A. Martínez-Ramírez, Raul Masu, WeiHsiang Liao & Yuki Mitsufuji. 2025. "Reductive, Exclusionary, Normalising: The Limits of Generative AI Music." *TISMIR* 8(1): 300–312. doi:10.5334/tismir.256. [V]**
- *Claim:* Representation, tokenization, and training data in ML music systems reproduce the reductions of earlier rule-based systems and normalize toward Western content.
- *Relevance:* A recent TISMIR statement. MIDI tokenization (12-TET, quantized onsets) is a "reductive" step in their sense.

**"A Bibliometric Analysis of the First 25 Years of ISMIR Authorship." *TISMIR* (doi:10.5334/tismir.265; authors and year R). [V title and finding]**
- ISMIR authorship remains Western-centric and Global-North-dominated.

**Holzapfel, André, Florian Krebs & Ajay Srinivasamurthy. 2014. "Tracking the 'Odd': Meter Inference in a Culturally Diverse Music Corpus." *Proc. ISMIR 2014*. [V title; authors R]**
- *Claim:* Beat trackers trained on Western data fail on non-Western metres. Adapting them to the style helps.
- *Relevance:* Predicts AMT and beat-tracking failure on 散板 and on 号子 call-and-response.

**Synthesis for Q4.**
- *Consensus in recent MIR:* tools embed 12-TET, metrical, and note-ontology assumptions, and their failures on non-Western music are partly *category* failures, not only accuracy failures (Serra; Cornelis; Panteli; Huang et al.; Morreale et al.).
- *The paper's contribution:* name the specific mismatch for Han song, 音腔 vs. note (沈洽), and test whether failures *cluster where native theory says the note ontology breaks* (润腔, 苦音 intervals, 散板).
- *Thin spot:* there is almost no published critique of MIR bias **written from within Chinese musicology**. The Chinese critiques address *Western music theory* (e.g. 周凯模 2004; 李志成 2025 on "欧洲音乐评价标准"), not computational tools. The paper can explicitly bridge this.

---

## A5. Musical features as evidence of cultural contact, migration, and exchange

### A5.1 Global comparative and phylogenetic precedent

**Lomax, Alan. 1968. *Folk Song Style and Culture*. Washington, DC: AAAS (Publication 88). [V]** Followed by **Savage, Patrick E. 2018. "Alan Lomax's Cantometrics Project: A Comprehensive Review." *Music & Science* 1. doi:10.1177/2059204318786084. [V]**, and **Wood, Anna L. C., et al. 2022. "The Global Jukebox: A Public Database of Performing Arts and Culture." *PLOS ONE* 17(11): e0275469. [V]** (5,776 songs from 1,026 societies, 37 cantometric features).
- *Claim:* Song style co-varies with social structure and maps onto culture areas.
- *Critiques:* problems with the song sample, inter-coder reliability, and statistical non-independence (Galton's problem). Savage 2018 notes published critiques were "generally balanced and constructive" (e.g. Dubinskas 1983).
- *Relevance:* The template, and the warning. Lomax's coders disagreed, and reliability was a central critique. **The paper's "disagreement as fingerprint" can be presented as turning the Cantometrics weakness into a measured quantity.**

**Savage, Patrick E., Steven Brown, Emi Sakai & Thomas E. Currie. 2015. "Statistical Universals Reveal the Structures and Functions of Human Music." *PNAS* 112(29): 8987–8992. [V]**
- *Claim:* No absolute universals, but many statistical universals consistent across nine regions. Uses phylogenetic comparative controls.
- *Relevance:* Methodological model for controlling non-independence (shared ancestry and contact) when comparing regions. Note: the author list here was recalled; the search confirmed the article and venue. Confirm the authors on the PNAS page.

**Brown, Steven, Patrick E. Savage, Albert Min-Shan Ko, Mark Stoneking, Ying-Chin Ko, Jun-Hun Loo & Jean A. Trejaut. 2014. "Correlations in the Population Structure of Music, Genes and Language." *Proceedings of the Royal Society B* 281(1774): 20132072 (article number R). [V]**
- *Claim:* Across Taiwanese Indigenous populations, musical distances (cantometric song features) correlate with genetic distances at magnitudes comparable to language–gene correlations. Music and language were not significantly correlated with each other.
- *Relevance:* The strongest precedent that musical features carry population history. Note that they used group song-type frequencies, not individual melodies.

**Savage, Patrick E. & Steven Brown. 2014. "Mapping Music: Cluster Analysis of Song-Type Frequencies within and between Cultures." *Ethnomusicology* 58(1): 133–155. [V]** 259 songs from 12 Taiwanese Indigenous groups, which form five "cantogroups."
- *Relevance:* A within-region, song-type-frequency approach that fits 色彩区 (regions as frequency mixtures of song types, not hard classes).

**Savage, Patrick E. & Quentin D. Atkinson. 2015. "Automatic Tune Family Identification by Musical Sequence Alignment." *Proc. 16th ISMIR*, pp. 162–168. [V]** And **Savage, P. E., et al. 2022. "Sequence Alignment of Folk Song Melodies Reveals Cross-Cultural Regularities of Musical Evolution." *Current Biology* 32(6) (pages R). [V]**
- *Claim:* Pitch-class sequence alignment identifies tune families. In Japanese and English folk songs, melodic change is constrained: rhythmically and functionally strong notes change less.
- *Relevance:* **A directly reusable method for 同宗民歌 (same-ancestor folk songs, e.g. 茉莉花 / Jasmine Flower variants).**

**Nishikawa, Yuri & Yasuo Ihara. 2025. "Exploring Factors for Melodic Diversification of Folk Songs in the Ryukyu Archipelago." *Evolutionary Human Sciences* 7: e23. doi:10.1017/ehs.2025.10010. [V]**
- *Claim and method:* Using Savage–Atkinson alignment and **linear mixed models**, they found that "sister songs" diverge more when sung on different islands and in different social contexts. Geographic distance and recording year were *not* significant.
- *Relevance:* A close methodological precedent for "feature-sharing ~ contact," with mixed effects. It also shows that *barriers* (sea crossing), not distance, drive divergence, which is analogous to dialect or mountain boundaries between 色彩区.

**Pamjav, Horolma, Zoltán Juhász, Andrea Zalán, Endre Németh & Bayarlkhagva Damdin. 2012. "A Comparative Phylogenetic Study of Genetics and Folk Music." *Molecular Genetics and Genomics* 287: 337–349. [V]**
- *Claim:* Across 31 Eurasian populations, folk-music similarity (Juhász's self-organizing-map melody clustering) predicts close genetic distance (below 0.05) with about 82% probability.
- *Relevance:* A precedent on a Eurasian scale. Juhász's earlier work on Hungarian and Central Asian melody "contour types" (several papers in *J. New Music Research*, 2000s; R) is relevant to Chinese northern and steppe contact.

**Morrison, Demorest & Pearce 2019** (see §A3.3). Cultural distance is operationalized as divergence between the statistical models of two traditions. This offers one way to quantify "distance between 色彩区."

### A5.2 Chinese contact, migration, and diffusion studies

**杜亚雄 (Du Yaxiong). c. 1981 (MA thesis, Nanjing Arts Institute 1980 conference era); book 《裕固族西部民歌研究》 ("Study of Western Yugur folk songs"). [V for the work and its comparison with Hungarian song; exact year and publisher R]**
- *Claim:* Western Yugur folk songs share pentatonicism, fifth-transposition structure, and short–long rhythmic figures with Hungarian folk song, more than with neighbouring Turkic song. This supports Bartók's thesis of old Turkic layers in Hungarian song.
- *Relevance:* **The landmark Chinese-language case of melodic features as evidence of historical contact and migration.** It is also a cautionary example: a reviewer will see it as feature similarity read as ancestry without controls.

**冯光钰 (Feng Guangyu).** Works on 音乐传播 (music transmission): 《中国传统音乐传播论》 ("On the transmission of Chinese traditional music") and the 同宗民歌 concept. [V-partial: Baidu's 音乐传播学 entry lists his channels of transmission, 移民传播 (by migration), 宗教传播 (by religion), 商道传播 (by trade routes), 战争传播 (by war), and he wrote on 曲牌 transmission (2007). The exact title, year, and publisher of the monograph and of any 《中国同宗民歌》 book are R.]
- *Relevance:* The native typology of diffusion channels. These map onto testable predictors: migration corridors, Grand Canal / trade routes, and garrison or military settlement.

**走西口 (*Zou Xikou*, "going beyond the western pass": Shanxi and Shaanxi migration into western Inner Mongolia, Qing–Republic).**
- Several million migrants moved from central-northern Shanxi and Yulin into western Inner Mongolia (国家民委 / National Ethnic Affairs Commission feature [V]).
- Musical outcomes: **漫瀚调** (*manhan diao*), which fuses Ordos Mongolian short-song melody with Jin–Shaan lyrics, and **二人台** (*errentai*, a two-person song-and-dance theatre form) [V, 国家民委 2026].
- One study compares three variants (Hequ, Shanxi; Fugu, Shaanxi; Inner Mongolian 漫瀚调) of the song 《走西口》 [V, fcipub; a low-tier venue].
- *Relevance:* **The best-documented Han–Mongol contact case**, with known direction and approximate dates. It suggests a testable hypothesis: 漫瀚调 in the corpus should sit *between* the 西北高原 and Mongolian feature distributions.

**湖广填四川 (*Huguang tian Sichuan*, "Huguang fills Sichuan": the early-Qing repopulation of Sichuan from Hubei, Hunan, Jiangxi, and Guangdong).**
- The NOPSS project report 《大变迁："湖广填四川"影响解读》 [V] documents effects on dialect, opera (川剧 Sichuan opera: 高腔 from 江西弋阳腔), and folk custom. There is a chapter on "江西移民与弋阳腔入川" (Jiangxi migrants and the entry of Yiyang tunes into Sichuan) [V, title from a Hubei library PDF].
- *Relevance:* Predicts that 西南高原区 (Sichuan) song shares features with 江汉, 湘, and 赣 regions above what geography alone predicts. **Folk-song-specific studies were not found in this session.** Opera is better documented, so the folk-song inference is mine.

**茉莉花 (*Molihua*, "Jasmine Flower") / 鲜花调 (*Xianhua diao*, "Fresh Flower Tune") variants.**
- Dozens of regional versions: Hebei, Northeast, Shandong, Jiangsu, Liuhe, and others [V, 华夏网 2024].
- The origin is disputed: Yangzhou vs. Wutaishan vs. Fengyang flower-drum [V, 安徽文联 2010].
- John Barrow's 1804 *Travels in China* transcription is the European-mediated variant [V, chinesefolklore.org.cn].
- *Relevance:* **The ideal 同宗 test case.** Variants with known regions allow alignment-based phylogeny (Savage–Atkinson) and a direct test of whether variant distance follows 色彩区 boundaries. The Barrow version is also a historical *inter-transcriber* datum (a European transcriber vs. Chinese versions).

**花儿 (*hua'er*, the Hehuang / northwestern song genre).** Officially described as "共创共享" (co-created and co-shared) by Han, Hui, Tibetan, Dongxiang, Bao'an, Salar, Tu, Yugur, and Mongol peoples across Gansu, Qinghai, and Ningxia, and sung in Chinese. Inscribed by UNESCO in 2009 (R; listed on ihchina.cn [V]).
- *Relevance:* A case of *feature-sharing across ethnic groups within one genre*. It tests whether shared features show interaction rather than common origin. It also carries political framing (民族团结 "ethnic unity" rhetoric) that the paper must handle critically.

**周青青 2011 (房陵, 底层 / 借用 / 交融) and the 通州 canal work songs** (see §A3.1): granular Chinese case studies of border blending and trade-route diffusion.

**Schimmelpenninck, Antoinet. 1997. *Chinese Folk Songs and Folk Singers: Shan'ge Traditions in Southern Jiangsu*. Leiden: CHIME Foundation. 442 pp. [V]**
- *Claim:* Shows **monothematism**: "one-tune areas" where singers perform most lyrics to one or a few related tunes. It is based on extensive fieldwork transcriptions.
- *Relevance:* **The most important English-language fieldwork monograph for this paper.** It shows that local style can be a *tune family*, not a feature bundle. That affects how 色彩区 should be modelled (tune-family mixture vs. feature distribution). Its transcriptions can be compared with the 江苏卷 anthology versions, which gives a real inter-transcriber test.

**Synthesis for Q5.**
- *Consensus:* musical features correlate with population history at group level (Brown et al. 2014; Pamjav et al. 2012), and melodic change is regular enough to model (Savage et al. 2022).
- *Contested:* whether shared features show *contact* rather than *common origin* or *convergent function*. Lomax and Du Yaxiong are both criticized on this point.
- *Chinese diffusion scholarship (走西口, 湖广填四川, 茉莉花)* is rich in historical documentation but almost entirely **qualitative and case-based**.
- **Inference to test:** feature-sharing between non-adjacent 色彩区 exceeds a geographic-distance null specifically along documented migration corridors.

---

## A6. Where English literature is thin and Chinese work is essential

1. **色彩区 theory itself.** There is no English monograph. 苗晶 & 乔建中 1987, 杨匡民 1987, 杜亚雄 1993 / 2011, 周青青 2009 / 2011, and 乔建中 1998 are Chinese-only. English MIR papers cite them only by translated title. **Essential to read in the original.**
2. **The ontology of the tone (音腔, 腔音, 润腔).** 沈洽, 王耀华, 董维松, and 于会泳 have no adequate English equivalent. The closest Western parallels are Seeger's melograph and Abraham–Hornbostel, but these come from outside the tradition.
3. **集成 editorial practice.** Internal guidelines (编辑方案, 记谱 rules) are not online. Provincial 凡例 pages and editors' memoirs are Chinese-only. Yang Mu 1994 is the main English critique.
4. **Migration-and-song studies (走西口, 湖广填四川, 同宗民歌).** These are Chinese-only and mostly published in provincial journals or conservatory 学报 (journals).
5. **Intonation measurement of Han folk singing (苦音, 中立音).** There is a Chinese acoustics tradition (韩宝强 and others), but I found no comprehensive measured study in this session. **This is a gap in both languages.**
6. **Where English is adequate:** transcription theory (Q1), MIR bias critique (Q4), and global phylogenetic method (Q5). There is **no** Chinese-language critique of MIR / AMT bias. The paper fills that bridge.

---

## A7. Consensus vs inference: summary table

| Proposition | Status |
|---|---|
| Transcription is selective; experts disagree most on microtones, ornaments, free rhythm | **Consensus** (Seeger; England; List; Ellingson; Nettl; 周凯模) |
| Expert agreement on pitch sequence can be high under a shared frame (κ ≈ 0.7) and AMT–human agreement is low (κ < 0.4) | **Empirical**, one study (Ozaki et al. 2021, 32 songs) |
| Chinese traditional notation records a skeleton (谱简腔繁) | **Consensus** (native principle) |
| 集成 classifies by province and genre and selects single variants | **Verified fact**; the effect on style signal is **inference** |
| Han folk song has approximate regional colour zones (10 + Hakka) | **Disciplinary consensus in China** (Miao–Qiao; textbooks), but **expert-qualitative, defined partly by extra-musical criteria, never formally validated** |
| Regional style is carried by mode, interval cells, 润腔, dialect text-setting | **Consensus in Chinese theory**; the relative weights are **unknown** |
| Musical features track population history | **Supported at group level** (Brown 2014; Pamjav 2012) |
| Feature-sharing shows *contact* (vs. common origin or convergence) | **Contested; requires controls** |
| Disagreement among transcribers is structured by region | **Novel inference; untested** |
| AMT failure locates the 音腔 / note ontological mismatch | **Novel inference; theoretically grounded (沈洽), untested** |

---

## A8. Strongest humanities-side reviewer objections

1. **Circularity of 色彩区.** Miao–Qiao defined regions partly from dialect and geography and from the same kind of anthology material. If the paper recovers them from 集成 scores, that may show the anthology editors' (and textbook-trained transcribers') categories, not the music. *Mitigation:* use features the regional theory did not explicitly rely on. Hold out Bilibili audio and non-集成 sources. Test against geographic and dialect nulls. Report what is *not* recovered.
2. **Reification and the politics of region.** 色彩区 is a 1980s PRC disciplinary construct tied to the 集成 nation-building project. Treating it as "real" naturalizes it. *Mitigation:* frame 色彩区 as a scholarly hypothesis to be tested, cite Yang Mu 1994 / 2003, and allow graded, overlapping regions (Miao–Qiao's own "近似" hedge, and the transitional 江淮区).
3. **The anthology is not a sample of practice.** Selection, censorship, normalization, and single variants all distort it. *Mitigation:* treat volume and transcriber as random effects. Measure per-volume ornament density. Compare with fieldwork transcriptions (e.g. Schimmelpenninck 1997 for southern Jiangsu).
4. **Disagreement as "fingerprint" may be a fingerprint of transcribers, not of music.** Regional differences in disagreement could reflect provincial training cultures (local 文化馆 staff vs. conservatory staff). *Mitigation:* this is partly the point (notation tradition is one of the three systems), but the model must separate transcriber/school variance from song-intrinsic ambiguity. Use songs transcribed more than once, and acoustic ambiguity measures from audio.
5. **Bilibili recordings are not "field recordings" in the ethnographic sense.** Many are staged, conservatory-trained 民族唱法 (national singing style), revival, or tourist performances, so they reproduce textbook regional style. *Mitigation:* code performer type and context. Treat "trained vs. tradition-bearer" as a factor. Do not equate audio with authenticity.
6. **Feature-sharing ≠ interaction.** Shared pentatonic cells may come from common Han origin, convergent function (work-song constraints), or modern media diffusion (radio-era 茉莉花). Du Yaxiong's Yugur–Hungarian argument is the cautionary example. *Mitigation:* use phylogenetic and spatial nulls (Savage et al. 2015; Nishikawa & Ihara 2025). Test sharing *along documented corridors* (走西口, 湖广填四川) against matched non-corridor pairs. Date-stratify where possible.
7. **Ontological mismatch is assumed, not shown.** Saying AMT "fails" on 音腔 presumes MIDI is the wrong ontology, while a reviewer may say the model is simply bad. *Mitigation:* show that failure *location* is predicted by native theory (润腔 type, 散板, 苦音 degrees) better than by generic difficulty (SNR, tempo, polyphony).
8. **Dialect and text are missing.** Han regional style is tightly bound to 腔词关系 and dialect tones (于会泳; 杜亚雄's "music dialect"). A melody-only analysis may miss the main carrier. *Mitigation:* align lyrics where the OMR pipeline provides them (Bu et al. 2025), and add dialect-zone covariates.
9. **Han-centrism.** 色彩区 covers only Han song. Minority regions appear as "blank" areas on the Miao–Qiao map. Cultural interaction is most visible exactly at Han–minority boundaries (花儿, 漫瀚调). *Mitigation:* state the scope explicitly, and treat contact zones as a separate analysis.
10. **English-only engagement.** TISMIR reviewers from Chinese musicology will expect original-language engagement with 苗晶 / 乔建中, 沈洽, 杨匡民, and 周青青, not secondary MIR citations. Cite Chinese titles with pinyin and translation, and read the originals (via CNKI).

---

## A9. Priority reading list (to acquire via CNKI or libraries)

1. 苗晶、乔建中 1987, full book. Extract per-region musical criteria.
2. 杨匡民 1987, 《中国音乐学》(1). 三声腔 as features.
3. 周青青 2009, 《音乐研究》(2): 1–20. Mode statistics as a baseline.
4. 杜亚雄 1993 (verify the Chinese title) and 2011, 《乐府新声》(1).
5. 沈洽 1982, 《中央音乐学院学报》(4): 12–21, and its 1983 continuation.
6. 董维松 2004, 《中国音乐》(4).
7. The 凡例 (editorial guidelines) of each 集成 provincial volume in the dataset.
8. Schimmelpenninck 1997. Comparison with the 江苏卷.
9. Ozaki et al. 2021, and Bu et al. 2025 (OMR overlap check).
10. Huang et al. 2023 (TISMIR framing).

---

# Part B — Technical / MIR annotated survey (Q6–Q10)

Verification: untagged items were confirmed this session via search, publisher/arXiv pages or Crossref; [UNVERIFIED] / [DOI unverified] items were not.

## B6. State-of-the-art AMT for non-Western, ornamented, heterophonic, and monophonic vocal material

### B6.1 General-purpose note transcription

**Bittner, R. M., Bosch, J. J., Rubinstein, D., Meseguer-Brocal, G., & Ewert, S. (2022).** A Lightweight Instrument-Agnostic Model for Polyphonic Note Transcription and Multipitch Estimation. *ICASSP 2022.* DOI: [10.1109/ICASSP43922.2022.9746549](https://doi.org/10.1109/ICASSP43922.2022.9746549). arXiv: [2203.09893](https://arxiv.org/abs/2203.09893). Code: [spotify/basic-pitch](https://github.com/spotify/basic-pitch).
- **Claim:** A small, instrument-agnostic CNN that jointly predicts onsets, notes, and multipitch generalizes across instruments, including voice.
- **Method:** Harmonic-stacked CQT input, trained on mixed datasets, evaluated with note F-measure.
- **Relevance:** It is the default "naive pipeline" baseline. It also outputs **pitch bends**, which keeps some sub-semitone information. That matters for intermediate pitches such as the "neutral" 7th and 4th in 苦音 (bitter-tone) modes. Report both the bend-preserving and the quantized output.

**Gardner, J., Simon, I., Manilow, E., Hawthorne, C., & Engel, J. (2022).** MT3: Multi-Task Multitrack Music Transcription. *ICLR 2022.* [ICLR page](https://iclr.cc/virtual/2022/poster/6969). Code: [magenta/mt3](https://github.com/magenta/mt3).
- **Claim:** A sequence-to-sequence T5-style model transcribes many instruments at once from a multi-dataset mixture.
- **Method:** Spectrogram in, MIDI-like tokens out.
- **Relevance:** MT3 was trained mostly on Western instrumental datasets and the original release handles voice poorly. It is useful as a "maximally Western-trained" contrast arm.

**Chang, S., Benetos, E., Kirchhoff, H., & Dixon, S. (2024).** YourMT3+: Multi-instrument Music Transcription with Enhanced Transformer Architectures and Cross-dataset Stem Augmentation. arXiv: [2407.04822](https://arxiv.org/abs/2407.04822). [Venue (IEEE MLSP 2024) UNVERIFIED.]
- **Claim:** An MT3 extension that adds a **singing** token class and uses cross-dataset stem augmentation.
- **Relevance:** It is the only MT3-family model that transcribes voice without separation, so it is a natural arm for heterophonic voice-plus-instrument recordings.

**Hawthorne, C., et al. (2018).** Onsets and Frames: Dual-Objective Piano Transcription. *ISMIR 2018*, pp. 50–57. [PDF](https://ismir2018.ircam.fr/doc/pdfs/19_Paper.pdf).
- **Relevance:** This is the historical reference for the onset/frame design and the source of the default 50 ms onset convention. It is piano-only, so cite it as background and do not run it as a pipeline.

### B6.2 F0 (pitch-contour) trackers: the layer to keep before any quantization

**Kim, J. W., Salamon, J., Li, P., & Bello, J. P. (2018).** CREPE: A Convolutional Representation for Pitch Estimation. *ICASSP 2018.* DOI: [10.1109/ICASSP.2018.8461329](https://doi.org/10.1109/ICASSP.2018.8461329). Code: [marl/crepe](https://github.com/marl/crepe).
- **Claim:** A time-domain CNN reaches state-of-the-art monophonic F0 accuracy.
- **Relevance:** Strong on clean monophony. Ozaki et al. (2021) report that CREPE **struggled on some monophonic traditional recordings**, which is direct evidence of a domain-shift failure.

**Mauch, M., & Dixon, S. (2014).** PYIN: A fundamental frequency estimator using probabilistic threshold distributions. *ICASSP 2014.* DOI: [10.1109/ICASSP.2014.6853678](https://doi.org/10.1109/ICASSP.2014.6853678). Implemented in `librosa.pyin` and in Tony.
- **Relevance:** A transparent, training-free baseline. Because it is not trained on data, its errors cannot come from training-domain bias. That makes it the key **control** for separating "Western-trained bias" from acoustic difficulty.

**Wei, H., Cao, X., Dan, T., & Chen, Y. (2023).** RMVPE: A Robust Model for Vocal Pitch Estimation in Polyphonic Music. *Interspeech 2023.* DOI: [10.21437/Interspeech.2023-528](https://doi.org/10.21437/Interspeech.2023-528). Code: [Dream-High/RMVPE](https://github.com/Dream-High/RMVPE).
- **Claim:** Estimates vocal F0 directly from mixtures, with no separation step.
- **Relevance:** A good fit for Bilibili clips with accompaniment, and widely used in the Chinese singing-voice-synthesis community.

**Luo, Y., Zhang, R., Liu, L.-C., Li, T., & Liu, H. (2025).** FCPE: A Fast Context-based Pitch Estimation Model. arXiv: [2509.15140](https://arxiv.org/abs/2509.15140) (under review). Code: [CNChTu/FCPE](https://github.com/CNChTu/FCPE).
- **Claim:** 96.79% raw pitch accuracy (RPA) on MIR-1K, at a real-time factor of 0.0062 on an RTX 4090.
- **Relevance:** Fast and noise-tolerant. MIR-1K is Mandarin pop karaoke, so the training-domain caveat applies.

**Riou, A., Lattner, S., Hadjeres, G., & Peeters, G. (2023).** PESTO: Pitch Estimation with Self-supervised Transposition-equivariant Objective. *ISMIR 2023.* arXiv: [2309.02265](https://arxiv.org/abs/2309.02265). Extended in *TISMIR*: [10.5334/tismir.251](https://transactions.ismir.net/articles/10.5334/tismir.251).
- **Relevance:** It is self-supervised and needs no pitch labels. You can **fine-tune it on unlabeled folk recordings**, which is a principled domain-adaptation arm.

### B6.3 Singing-voice note transcription (vocal-to-MIDI)

**Hsu, J.-Y., & Su, L. (2021).** VOCANO: A note transcription framework for singing voice in polyphonic music. *ISMIR 2021.* [PDF](https://archives.ismir.net/ismir2021/paper/000036.pdf). Zenodo: [10.5281/zenodo.5624383](https://zenodo.org/records/5624383). Code: [B05901022/VOCANO](https://github.com/B05901022/VOCANO). [Author list from memory.]
- **Method:** Separation, then F0 and note segmentation with semi-supervised and multi-task learning.
- **Relevance:** An open pipeline whose stages (separation, F0, segmentation) can be audited **one at a time**. That suits "where does it fail" analysis.

**Wang, J.-Y., & Jang, J.-S. R. (2021).** On the Preparation and Validation of a Large-Scale Dataset of Singing Transcription (MIR-ST500). *ICASSP 2021.* DOI: [10.1109/ICASSP39728.2021.9414601](https://doi.org/10.1109/ICASSP39728.2021.9414601). Code and data: [york135/singing_transcription_ICASSP2021](https://github.com/york135/singing_transcription_ICASSP2021).
- **Data:** 500 **Chinese pop** songs (about 30 hours) with note labels.
- **Relevance:** The main training-domain anchor for "Chinese-language but non-folk" singing transcription. Cite it explicitly when you argue that the model's prior is pop, not folk.

**Li, R., Zhang, Y., Wang, Y., Hong, Z., Huang, R., & Zhao, Z. (2024).** Robust Singing Voice Transcription Serves Synthesis (ROSVOT). *ACL 2024* (long). [ACL Anthology](https://aclanthology.org/2024.acl-long.526/). arXiv: [2405.09940](https://arxiv.org/abs/2405.09940). Code: [RickyL-2000/ROSVOT](https://github.com/RickyL-2000/ROSVOT).
- **Method:** Multi-scale note boundary and pitch prediction, tuned for annotating singing-voice-synthesis corpora.
- **Relevance:** Currently the strongest open Mandarin singing transcriber. It is trained on Mandarin singing-synthesis corpora such as M4Singer.

**openvpi. SOME: Singing-Oriented MIDI Extractor** (software; v0.0.1 released 2023-10-06). [github.com/openvpi/SOME](https://github.com/openvpi/SOME).
- **Claim (README):** Outputs **non-integer MIDI** values, and can be retrained with about 3 hours of data.
- **Relevance:** Keeping non-integer pitch makes it attractive for intonation work. There is no peer-reviewed paper and the pretrained training data is not documented on the repo page, so label it a community tool.

**Wang, J.-C., Lu, W.-T., & Chen, J. (2024).** Mel-RoFormer for Vocal Separation and Vocal Melody Transcription. *ISMIR 2024*, pp. 454–461. arXiv: [2409.04702](https://arxiv.org/abs/2409.04702). Open re-implementations are in [ZFTurbo/Music-Source-Separation-Training](https://github.com/ZFTurbo/Music-Source-Separation-Training) (key `mel_band_roformer`). The ByteDance original weights are not confirmed open.
- **Relevance:** Currently the strongest open approach for **vocal separation** before F0 extraction.

**Rouard, S., Massa, F., & Défossez, A. (2023).** Hybrid Transformers for Music Source Separation (HT-Demucs). *ICASSP 2023.* arXiv: [2211.08553](https://arxiv.org/abs/2211.08553). Code: facebookresearch/demucs.
- **Relevance:** An alternative separator. Separation artifacts are a **failure mode in their own right**: in heterophonic mixtures, voice and instrument share pitch content, so a separator can leak the instrument into the voice stem or delete the voice.

**Training-domain corpora (for the "whose prior?" argument):**
- **Opencpop** (Wang et al., Interspeech 2022): 100 Mandarin pop songs, one female professional singer. [arXiv 2201.07429](https://arxiv.org/abs/2201.07429); [repo](https://github.com/wenet-e2e/opencpop).
- **M4Singer** (Zhang et al., NeurIPS 2022 Datasets & Benchmarks): [paper](https://proceedings.neurips.cc/paper_files/paper/2022/hash/2de60892dd329683ec21877a4e7c3091-Abstract-Datasets_and_Benchmarks.html); [repo](https://github.com/M4Singer/M4Singer).

Neither corpus contains regional folk singing styles. (First-author names are from the papers; I did not cross-check the full author lists.)

### B6.4 Non-Western traditions: precedents and failure analyses

**Ozaki, Y., McBride, J., Benetos, E., Pfordresher, P. Q., Six, J., Tierney, A. T., Proutskova, P., Sakai, E., Kondo, H., Fukatsu, H., Fujii, S., & Savage, P. E. (2021).** Agreement among human and automated transcriptions of global songs. *ISMIR 2021*, pp. 500–508. [PDF](https://archives.ismir.net/ismir2021/paper/000062.pdf). Code and data: [comp-music-lab/agreement-human-automated](https://github.com/comp-music-lab/agreement-human-automated). Audio: [10.5281/zenodo.4941863](https://doi.org/10.5281/zenodo.4941863).
- **Design:** 32 excerpts of 14 s each, drawn from 8 regions, half solo voice and half voice plus instruments. Three experts transcribed each one, and 10 automatic methods were run.
- **Method:** 12-TET quantization, Needleman–Wunsch alignment, a transposition search over ±2 semitones, Fleiss' κ, and percent identity.
- **Results:** Humans: median κ ≈ .74 and PID ≈ 88%. Automatic methods: κ < .4 and agreement < 60%, with no overall winner. SPICE and an NNMF method had median κ below 0; CREPE and SPICE failed on some monophonic items.
- **Relevance:** The **template design** for your envelope study. Its limits — 12-TET quantization, a small n, and Western-staff-trained raters — are exactly where your paper can extend it: notators trained in Chinese jianpu conventions, cents-level analysis, and many more items per region.

**Holzapfel, A., & Benetos, E. (2019).** Automatic music transcription and ethnomusicology: a user study. *ISMIR 2019*, pp. 678–684. [PDF](https://archives.ismir.net/ismir2019/paper/000082.pdf).
- **Design:** 16 transcribers worked on Cretan *sousta* excerpts, transcribing either manually or starting from an automatic draft.
- **Metrics:** pitch, extra-note, missing-note, and onset error rates.
- **Results:** No significant difference in quality, time, or effort between the two conditions. Rhythm and duration, added or omitted notes, and melody–accompaniment confusion were the main complaints.
- **Relevance:** Precedent for a **typed error taxonomy** and for asking whether AMT changes expert behavior.

**Holzapfel, A., Benetos, E., Killick, A., & Widdess, R. (2022).** Humanities and engineering perspectives on music transcription. *Digital Scholarship in the Humanities*, 37(3), 747–764. DOI: [10.1093/llc/fqab074](https://doi.org/10.1093/llc/fqab074). Materials: [kth.box.com/v/DSH2021Transcription](https://kth.box.com/v/DSH2021Transcription).
- **Design:** 18 transcribers, and 140 transcriptions rated by two senior ethnomusicologists.
- **Results:** Expert ratings were **only partly captured** by the computational metrics, because analytic purpose and notational choices matter.
- **Relevance:** The key citation for "metric ≠ musicological validity". It bridges the humanities and technical lines.

**Benetos, E., & Holzapfel, A. (2015).** Automatic transcription of Turkish microtonal music. *JASA*, 138(4). DOI: [10.1121/1.4930187](https://doi.org/10.1121/1.4930187). Code and data: [SoundSoftware project](https://code.soundsoftware.ac.uk/projects/automatic-transcription-of-turkish-makam-music).
- **Claim:** Transcription on a **microtonal (sub-semitone) pitch grid**, evaluated against makam reference transcriptions.
- **Relevance:** Precedent for **not quantizing to 12-TET**, and for using a tradition-specific tuning grid in evaluation.

**Kroher, N., & Gómez, E. (2016).** Automatic Transcription of Flamenco Singing From Polyphonic Music Recordings. *IEEE/ACM TASLP*, 24(5). DOI: [10.1109/TASLP.2016.2531284](https://doi.org/10.1109/TASLP.2016.2531284). arXiv: [1510.04039](https://arxiv.org/abs/1510.04039).

**Gómez, E., & Bonada, J. (2013).** Towards Computer-Assisted Flamenco Transcription: An Experimental Comparison of Automatic Transcription Algorithms as Applied to A Cappella Singing. *Computer Music Journal*, 37(2). DOI: [10.1162/COMJ_a_00180](https://doi.org/10.1162/COMJ_a_00180). Dataset: TONAS ([Zenodo](https://zenodo.org/records/1290722)).
- **Relevance of both:** The closest analogue to heavily **melismatic, ornamented solo singing**. They assign note pitch from contour statistics plus a global pitch-class prior, and document segmentation errors on melisma.

**CompMusic corpora and analyses (Serra, MTG-UPF).**
- **Overview:** Serra, X. (2014). *Creating Research Corpora for the Computational Study of Music: the case of the CompMusic Project.* AES 53rd Int. Conf. [PDF](http://mtg.upf.edu/system/files/publications/Serra-Xavier-AES-Conf-2014.pdf).
- **Carnatic intonation:** Koduri, G. K., Ishwar, V., Serrà, J., & Serra, X. (2014). Intonation Analysis of Rāgas in Carnatic Music. *JNMR*, 43(1). DOI: [10.1080/09298215.2013.866145](https://doi.org/10.1080/09298215.2013.866145). They model intonation as **pitch-distribution shape per svara**, not as discrete notes. That is a direct methodological model for regional intonation fingerprints.
- **Saraga:** Srinivasamurthy, A., Gulati, S., et al. (2021). Saraga: Open Datasets for Research on Indian Art Music. [emusicology.org](https://emusicology.org/article/id/4793/) (published on the *Empirical Musicology Review* site; full author list not cross-checked). Data: [mtg.github.io/saraga](https://mtg.github.io/saraga/).
- **Turkish makam review:** Bozkurt, B., Ayangil, R., & Holzapfel, A. (2014). Computational analysis of Turkish makam music: review of state-of-the-art and challenges. *JNMR*. [UPF repository](https://repositori.upf.edu/bitstreams/241e6a71-63c9-4de5-976e-7ff968a579c1/download). [Co-authors and DOI UNVERIFIED.]

**Jingju (Beijing opera) — the closest Chinese vocal tradition with open data.**
- **Repetto, R. C., & Serra, X. (2014).** Creating a Corpus of Jingju (Beijing Opera) Music and Possibilities for Melodic Analysis. *ISMIR 2014.* [PDF](https://archives.ismir.net/ismir2014/paper/000237.pdf).
- **Gong, R., Repetto, R. C., & Serra, X. (2017).** Creating an A Cappella Singing Audio Dataset for Automatic Jingju Singing Evaluation Research. arXiv: [1708.03986](https://arxiv.org/abs/1708.03986). Data: [Zenodo 1323561](https://zenodo.org/records/1323561). Contents: 120 arias and 1,265 melodic lines. [Published venue, believed to be DLfM 2017, not confirmed.]
- **Gong, R., & Serra, X. (2018).** Singing voice phoneme segmentation by hierarchically inferring syllable and phoneme onset positions. arXiv: [1806.01665](https://arxiv.org/abs/1806.01665).
- **Relevance:** This work shows that, for Chinese sung traditions, **syllable/lyric structure is the natural segmentation unit**, not the Western note. That is a strong argument for adding syllable-aligned metrics (§B7) for 民歌, where one syllable often spans a melisma or a 拖腔 (prolonged melismatic tail).

**Chinese music MIR datasets.**
- **Zhou, M., Xu, S., Liu, Z., Wang, Z., Yu, F., Li, W., & Han, B. (2025).** CCMusic: An Open and Diverse Database for Chinese Music Information Retrieval Research. *TISMIR*, 8(1), 22–38. DOI: [10.5334/tismir.194](https://doi.org/10.5334/tismir.194). Data on HuggingFace (`ccmusic-database`).
  - Includes an **erhu playing-technique** dataset (about 1,500 clips; also [Zenodo 4320991](https://zenodo.org/record/4320991)) and a **bel canto vs. Chinese national/folk singing** a cappella set (203 recordings). It has **no note-level folk transcription ground truth**.
  - Co-author Han Baoqiang (韩宝强) is a leading Chinese music acoustician, so this is a good bridge to the Chinese-language acoustics literature.
- **Erhu technique detection:** Wang, Z., et al. (2019). Musical Instrument Playing Technique Detection Based on FCN. arXiv: [1910.09021](https://arxiv.org/abs/1910.09021). [Author list UNVERIFIED.]
- **Guqin jianzipu OCR and generation:** [wds-seu/guqinMM](https://github.com/wds-seu/guqinMM) (repo only; paper not checked). This is notation-side, not audio transcription.
- **Jianpu OMR for the 集成-type anthology — highly relevant to your symbolic layer:** **Bu, F., Li, R., Li, Z., Li, Y., Fan, L., & Huang, P. (2025).** The Renaissance of Expert Systems: Optical Recognition of Printed Chinese Jianpu Musical Scores with Lyrics. arXiv: [2512.14758](https://arxiv.org/abs/2512.14758).
  - Evaluated on *The Anthology of Chinese Folk Songs*: more than 5,000 melody-only songs (over 300,000 notes) and a 1,400-song lyrics subset.
  - Note-wise melody F1 = 0.951; character-wise lyric F1 = 0.931. No code link on the arXiv page.
  - **Implication:** roughly 5% note-level OCR error in the "human" layer. You must estimate it per volume or region (see objections).
- **Jianpu in digital humanities:** Yang, R., Giraud, M., & Levé, F. (2025). Jianpu Number-Based Music Notation in Cultural Heritage and Digital Humanities. *Music Encoding Conference 2025.* [HAL](https://hal.science/hal-05029666/file/Music-with-numbers-Jianpu--Yang--MEC-2025.pdf). They note that **no standard native Jianpu encoding exists**. Relevant to the claim that MusicXML/MIDI encoding loses jianpu-specific information, such as movable-do degree identity and ornament signs.

**Chinese folk-song regional-style computation (symbolic or audio).** These are mostly small, mostly classification-only, and mostly without released data.
- **Li, J., Ding, J., & Yang, X. (2017).** The Regional Style Classification of Chinese Folk Songs Based on GMM-CRF Model. *Proc. ICCAE 2017*, pp. 66–72. DOI: [10.1145/3057039.3057069](https://doi.org/10.1145/3057039.3057069).
- **Yang, X., Luo, J., Wang, Y., Zhao, X., & Li, J. (2018).** Combining auditory perception and visual features for regional recognition of Chinese folk songs. DOI: [10.1145/3192975.3193006](https://doi.org/10.1145/3192975.3193006).
- **Luo, J., et al. (2019).** MG-VAE: Deep Chinese Folk Songs Generation with Specific Regional Styles. arXiv: [1909.13287](https://arxiv.org/abs/1909.13287). A MIDI set of more than 2,000 folk songs from 6 regions; check provenance.
- **Liu, H., Jiang, K., Gamboa, H., Xue, T., & Schultz, T. (2022).** Bell Shape Embodying Zhongyong: The Pitch Histogram of Traditional Chinese Anhemitonic Pentatonic Folk Songs. *Applied Sciences*, 12, 8343. DOI: [10.3390/app12168343](https://doi.org/10.3390/app12168343).
  - 53 target songs from 23 provinces. The 4 songs that are not "bell-shaped" all come from Shanxi or Sichuan, which is a tiny but suggestive region signal.
  - They also report that the Essen "Han" subset has 1,161 songs.
- **Shanahan, D., & Huron, D. (2011).** Interval Size and Phrase Position: A Comparison between German and Chinese Folksongs. *Empirical Musicology Review.* DOI: [10.18061/1811/52948](https://doi.org/10.18061/1811/52948).
- **Cornelissen, B., Zuidema, W., Burgoyne, J. A., & Honing, H. (2026).** Melodic contour does not cluster: Reconsidering contour typology. arXiv: [2604.13119](https://arxiv.org/abs/2604.13119).
  - Uses the Essen Han, Shanxi, and Natmin subsets, and finds **no discrete contour clusters**.
  - **Directly relevant caution:** "regions" defined from continuous features may be gradients, not types. Test for discreteness explicitly; don't assume it.
- **Rashidi (2026)**, arXiv: [2607.12517](https://arxiv.org/abs/2607.12517), reports that Chinese Essen melodies have a larger mean absolute interval (2.77 semitones vs. Germany's 2.17). It is a single-author preprint; treat it as weak.
- **Essen Folksong Collection** (Schaffrath, 1995, kern format via KernScores). [Exact citation UNVERIFIED.] It has Chinese subsets (Han, Natmin, Shanxi), mostly from collections that predate 集成. It is the **only openly reusable symbolic Chinese folk corpus** widely used in English MIR, so you can use it as an external replication set.

**Intonation and drift baselines.**
- **Mauch, M., Frieler, K., & Dixon, S. (2014).** Intonation in unaccompanied singing: Accuracy, drift, and a model of reference pitch memory. *JASA*, 136(1), 401. DOI: [10.1121/1.4881915](https://doi.org/10.1121/1.4881915). Reports a median absolute drift of about 11 cents over roughly 50 s. Use it as the **null amount of drift** to expect before you attribute deviations to regional practice.
- **Six, J., Cornelis, O., & Leman, M. (2013).** Tarsos, a Modular Platform for Precise Pitch Analysis of Western and Non-Western Music. *JNMR*, 42(2). DOI: [10.1080/09298215.2013.797999](https://doi.org/10.1080/09298215.2013.797999). Pitch-class histograms in cents, without a 12-TET assumption.

### B6.5 Failure-mode taxonomy to adopt (synthesis — my inference, not consensus)

| Layer | Failure mode | Expected region or genre link (hypothesis) | Diagnostic |
|---|---|---|---|
| Source | Accompaniment leakage; heterophonic doubling (voice plus 笛 dizi flute, 二胡 erhu, 唢呐 suona) | Ensemble or accompanied genres; staged Bilibili performances | Separation residual energy; compare mixture and separated F0 |
| F0 | Octave errors, voicing dropouts in falsetto, very high tessitura, breathy or shouted 号子 (work-song) styles | Northwest 信天游/花儿 (high, open-throated); work chants | Octave-error rate; voicing recall vs. a hand-checked F0 |
| Segmentation | Glides (滑音) split into multiple notes; 倚音/波音 (grace notes, mordents) either dropped or emitted as spurious notes; melisma over one syllable merged | Regions with dense ornament: e.g., 江南 (Jiangnan) 小调, Shaanxi 苦音 slides — exact regional pattern is a humanities-line question | Molina split, merge, and spurious counts; ornament-insertion rate |
| Quantization | Neutral or intermediate pitches forced to 12-TET; reference/tonic drift misread as a key change | 苦音 modes; minority traditions with non-tempered scales | Cents deviation from nearest semitone; bimodality per scale degree |
| Rhythm/meter | 散板 (free rhythm) yields spurious meter; tempo rubato breaks quantization | Long-tune (长调) and free-meter genres | MV2H meter and value components; onset-only F |
| Domain | Pop-trained models favor stable, sustained pitches | Everywhere, but strongest where style is furthest from pop | Gap between a training-free (pYIN) and a trained model, per region |

---

## B7. Metrics beyond an aggregate F-measure

**Raffel, C., McFee, B., Humphrey, E. J., Salamon, J., Nieto, O., Liang, D., & Ellis, D. P. W. (2014).** mir_eval: A Transparent Implementation of Common MIR Metrics. *ISMIR 2014.* [PDF](https://archives.ismir.net/ismir2014/paper/000320.pdf). Docs: [mir_eval.transcription](https://mir-eval.readthedocs.io/latest/api/transcription.html).
- **Defaults (confirmed in the docs):** onset tolerance ±50 ms; pitch tolerance 50 cents; offset tolerance max(0.2 × reference duration, 50 ms). Setting `offset_ratio=None` gives onset-only matching.
- `mir_eval.melody` provides raw pitch accuracy (RPA), raw chroma accuracy (RCA), overall accuracy (OA), voicing recall, and voicing false alarm, with a configurable cent tolerance.
- **Recommendation:** report a **tolerance sweep** rather than one point. Use pitch tolerances of 25, 50, and 100 cents and onset tolerances of 50, 100, and 150 ms. Region-dependent slopes of F against tolerance are themselves informative: steep slopes mean near-misses (intonation or glides), and flat slopes mean gross errors.

**Molina, E., Barbancho, A. M., Tardón, L. J., & Barbancho, I. (2014).** Evaluation Framework for Automatic Singing Transcription. *ISMIR 2014.* [PDF](https://archives.ismir.net/ismir2014/paper/000298.pdf). Data: [RIUMA](https://riuma.uma.es/xmlui/handle/10630/28486).
- **Error categories:**
  - correct onset/pitch/offset (COnPOff), correct onset and pitch (COnP), and correct onset only (COn);
  - only-bad-onset, only-bad-pitch, and only-bad-offset;
  - **split**, **merged**, **spurious**, and **non-detected** notes.
- **Data and code:** a cross-annotated dataset and a MATLAB toolbox. In this check I found no maintained Python port, so expect to reimplement it (about 200 lines on top of mir_eval matching).
- **Relevance:** The most important metric family for your "where and why" thesis. Split counts measure glide and ornament fragmentation; merge counts measure melisma and legato collapse; spurious counts measure ornament insertion and leakage.

**Salamon, J., Gómez, E., Ellis, D. P. W., & Richard, G. (2014).** Melody Extraction from Polyphonic Music Signals: Approaches, Applications, and Challenges. *IEEE Signal Processing Magazine*, 31(2). DOI: [10.1109/MSP.2013.2271648](https://doi.org/10.1109/MSP.2013.2271648).
- **Relevance:** The canonical definition of the frame-level melody metrics, and an early discussion of evaluation bias toward Western popular music.

**Cents-level deviation (recommended construction — standard practice, no single source).**
- For each matched note (after alignment), compute the median F0 in cents relative to:
  - (a) the transcribed pitch;
  - (b) the nearest 12-TET semitone;
  - (c) the song's estimated tonic (movable-do, matching jianpu).
- Report signed and absolute deviations and the per-scale-degree distributions (as in Koduri et al. 2014).
- For model-vs-reference comparison of continuous values, use **Bland–Altman** limits of agreement: Bland, J. M., & Altman, D. G. (1986). *Lancet*, 327(8476), 307–310. DOI: [10.1016/S0140-6736(86)90837-8](https://doi.org/10.1016/S0140-6736(86)90837-8).

**Ornament and insertion metrics.** The English literature here is thin.
- No standard metric exists. Build one from Molina's categories: ornament-insertion rate = spurious notes shorter than X ms that fall within ±Y ms of a reference ornament sign or note boundary. Also report the ornament recall for notated 倚音 (grace notes).
- Ornament signs are in the jianpu source only if OCR captured them. Bu et al. (2025) report melody F1 only, so check what their pipeline encodes.

**Segmentation and boundary metrics.**
- `mir_eval.segment.detection` gives boundary hit-rate F at ±0.5 s and ±3 s.
- **Nieto, O., Farbood, M. M., Jehan, T., & Bello, J. P. (2014).** Perceptual Analysis of the F-Measure for Evaluating Section Boundaries in Music. *ISMIR 2014.* [PDF](https://ccrma.stanford.edu/~urinieto/MARL/publications/NietoFarboodBelloJehan-ISMIR2014.pdf). Shows that listeners weight precision over recall.
- Use these for **phrase boundaries** (乐句), whose placement often differs between notators.

**Symbolic alignment-based metrics.**
- **Needleman–Wunsch percent identity with a transposition search.** Ozaki et al. 2021, code in their repo. Simple and interpretable, and comparable with the global-song literature.
- **Savage, P. E., Passmore, S., Chiba, G., Currie, T. E., Suzuki, H., & Atkinson, Q. D. (2022).** Sequence alignment of folk song melodies reveals cross-cultural regularities of musical evolution. *Current Biology*, 32(6), 1395–1402.e8. DOI: [10.1016/j.cub.2022.01.039](https://doi.org/10.1016/j.cub.2022.01.039). Alignment-based variant analysis across Japanese and English folk tunes: ornamental and rhythmically weak notes change more readily. This is **the bridge between "transcriber disagreement" and "cultural transmission"**, using the same alignment machinery.
- **Foscarin, F., Fournier-S'niehotta, R., & Jacquemard, F. (2019).** A diff procedure for music score files. *DLfM 2019.* [HAL](https://inria.hal.science/hal-02267454v2/document). Implementation: **musicdiff** ([gregchapman-dev/musicdiff](https://github.com/gregchapman-dev/musicdiff); [PyPI](https://pypi.org/project/musicdiff/)). It is built on music21 and counts edit operations by type (notes, ornaments, lyrics, beams, and so on). It is the best tool for **MusicXML-vs-MusicXML disagreement between anthologies**, because it can give an error profile per notation element.
- **Martinez-Sevilla et al. (2025).** OMR-NED: standardized OMR evaluation. [HF papers 2506.10488](https://huggingface.co/papers/2506.10488). A normalized edit distance with per-element breakdown. Useful for **auditing OCR error** in the 集成 layer.
- **McLeod, A., & Steedman, M. (2018).** Evaluating Automatic Polyphonic Music Transcription (MV2H). *ISMIR 2018.* [PDF](https://ismir2018.ismir.net/doc/pdfs/148_Paper.pdf). Code: [apmcleod/MV2H](https://github.com/apmcleod/MV2H).
  - A joint score over multi-pitch, voice separation, **metrical alignment**, note value, and harmony.
  - The meter and note-value components are exactly where **散板** should fail. Report them separately; don't use only the composite.
- **DTW and synchronization:** Müller, M., Özer, Y., Krause, M., Prätzlich, T., & Driedger, J. (2021). Sync Toolbox: A Python Package for Efficient, Robust, and Accurate Music Synchronization. *JOSS.* DOI: [10.21105/joss.03434](https://doi.org/10.21105/joss.03434). Use it for score-to-audio alignment, so that anthology scores can be compared with Bilibili audio when the same tune is performed.

**Perceptual and musicological validity of metrics.**
- **Ycart, A., Liu, L., Benetos, E., & Pearce, M. (2020).** Investigating the Perceptual Validity of Evaluation Metrics for Automatic Piano Music Transcription. *TISMIR.* DOI: [10.5334/tismir.57](https://doi.org/10.5334/tismir.57). Code: [adrienycart/PEAMT](https://github.com/adrienycart/PEAMT). [Co-authors after Ycart from memory.]
- **Wang, P., Yang, G., Tamer, N. C., Ebert, V., & Smith, N. A. (2026).** A Dual Evaluation for Music Transcription. arXiv: [2608.04511](https://arxiv.org/abs/2608.04511). Notation similarity and playback similarity favor **different** pipelines, and the MIDI-to-score step drives notation scores.
- **Implication:** your symbolic-layer error is partly a **quantization/notation-rendering** artifact. Evaluate at the MIDI (performance) level and at the score level separately.
- **Holzapfel et al. (2022, DSH)** (above): the experts' sense of quality is only partly captured by the metrics.

**Transposition and tonic handling (critical for jianpu).** Jianpu is movable-do. Compare in **tonic-relative scale-degree space**, or do a transposition search (Ozaki: ±2 semitones; more is safer for field recordings). Without that, key choice by the notator inflates disagreement.

---

## B8. Modeling inter-annotator variation as signal

### B8.1 General frameworks

**Uma, A. N., Fornaciari, T., Hovy, D., Paun, S., Plank, B., & Poesio, M. (2021).** Learning from Disagreement: A Survey. *JAIR*, 72, 1385–1470. DOI: [10.1613/jair.1.12752](https://doi.org/10.1613/jair.1.12752).
- **Claim:** Disagreement is often systematic, and models trained or evaluated on soft labels can beat models built on gold labels.
- **Method:** A taxonomy of approaches — aggregation, soft-label training, and multi-task learning across annotators — plus "soft" evaluation metrics such as cross-entropy against a label distribution.
- **Relevance:** The conceptual license for "disagreement as fingerprint", and the source for soft evaluation.

**Plank, B. (2022).** The "Problem" of Human Label Variation: On Ground Truth in Data, Modeling and Evaluation. *EMNLP 2022.* DOI: [10.18653/v1/2022.emnlp-main.731](https://aclanthology.org/2022.emnlp-main.731/).
- **Claim:** "Human label variation" should be separated from annotation noise and treated as legitimate information. Plank argues for evaluating against the full distribution.
- **Relevance:** Use her term **"human label variation"** to name your construct. It sets the stance for the paper.

**Dawid, A. P., & Skene, A. M. (1979).** Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm. *Applied Statistics*, 28(1), 20–28. DOI: [10.2307/2346806](https://doi.org/10.2307/2346806).
- **Method:** Latent true class plus a per-annotator confusion matrix, fitted by EM.
- **Relevance:** Use it for **categorical per-note decisions** after alignment: scale degree, ornament present or absent, and phrase boundary present or absent. A per-transcriber confusion matrix is a literal "fingerprint". **Caveat:** Dawid–Skene assumes one latent truth. Under your thesis, part of the "error" is interpretation, so present its outputs as *systematic tendencies*, not error rates.

**Paun, S., Carpenter, B., Chamberlain, J., Hovy, D., Kruschwitz, U., & Poesio, M. (2018).** Comparing Bayesian Models of Annotation. *TACL*, 6, 571–585. DOI: [10.1162/tacl_a_00040](https://doi.org/10.1162/tacl_a_00040).
- **Method:** Compares pooled, unpooled, and hierarchical annotator models, some with item-difficulty terms, in Stan.
- **Relevance:** The **hierarchical annotator model with item difficulty** maps onto transcriber (annotator) × song/passage (item difficulty) × region (a covariate on difficulty).

**Further frameworks:**
- **Raykar, V. C., et al. (2010).** Learning From Crowds. *JMLR*, 11, 1297–1322. [UNVERIFIED in this session.] Jointly learns a classifier and annotator reliabilities.
- **Passonneau, R. J., & Carpenter, B. (2014).** The Benefits of a Model of Annotation. *TACL*, 2. [UNVERIFIED in this session.] Argues that a probabilistic annotation model is more informative than agreement coefficients.
- **Peterson, J. C., Battleday, R. M., Griffiths, T. L., & Russakovsky, O. (2019).** Human uncertainty makes classification more robust. *ICCV 2019.* arXiv: [1908.07086](https://arxiv.org/abs/1908.07086). Training on human label distributions (CIFAR-10H) improves generalization and robustness, which is evidence that the distribution carries signal.
- **Aroyo, L., & Welty, C. (2015).** Truth Is a Lie: Crowd Truth and the Seven Myths of Human Annotation. *AI Magazine*, 36(1). DOI: [10.1609/aimag.v36i1.2564](https://doi.org/10.1609/aimag.v36i1.2564).
- **Gordon, M. L., Zhou, K., Patel, K., Hashimoto, T., & Bernstein, M. S. (2021).** The Disagreement Deconvolution: Bringing Machine Learning Performance Metrics In Line With Reality. *CHI 2021.* DOI: [10.1145/3411764.3445423](https://doi.org/10.1145/3411764.3445423). Separates annotator-level from population-level disagreement, so evaluation is not dominated by noisy single-annotator labels. A good model for **per-region envelope estimation**.

### B8.2 MIR precedents

- **Koops, H. V., de Haas, W. B., Burgoyne, J. A., Bransen, J., Kent-Muller, A., & Volk, A. (2019).** Annotator subjectivity in harmony annotations of popular music. *JNMR*, 48(3), 232–252. DOI: [10.1080/09298215.2019.1613436](https://doi.org/10.1080/09298215.2019.1613436).
  - Four expert annotators per song; they disagree substantially and systematically.
  - Agreement depends on the evaluation vocabulary (root vs. full chord).
  - **Relevance:** Precedent for agreement depending on *feature granularity*, which parallels pitch vs. rhythm vs. ornament in your data.
- **Ni, Y., McVicar, M., Santos-Rodriguez, R., & De Bie, T. (2013).** Understanding Effects of Subjectivity in Measuring Chord Estimation Accuracy. *IEEE TASLP*, 21(12), 2607–2615. DOI: [10.1109/TASL.2013.2280218](https://doi.org/10.1109/TASL.2013.2280218). Inter-annotator agreement **bounds** achievable system scores; systems approach that ceiling.
- **Flexer, A., & Grill, T. (2016).** The Problem of Limited Inter-rater Agreement in Modelling Music Similarity. *JNMR*, 45(3). DOI: [10.1080/09298215.2016.1200631](https://doi.org/10.1080/09298215.2016.1200631). Shows that **upper bounds** on system performance follow from inter-rater agreement, and that MIREX systems hit them. This is the origin of the "human ceiling" argument in MIR.
- **Balke, S., Driedger, J., Abeßer, J., Dittmar, C., & Müller, M. (2016).** Towards Evaluating Multiple Predominant Melody Annotations in Jazz Recordings. *ISMIR 2016.* [PDF](https://balke.at/assets/pdf/2016_BalkeADDM_JazzSoloAnnotations_ISMIR.pdf).
  - Several annotators produced F0 annotations of the *same audio*; their disagreement was concentrated in onsets/offsets, glides, and voicing decisions.
  - It also proposes evaluating systems against several references.
  - **Closest technical analogue** for your cents/segmentation envelope.
- **Weiß, C., Schreiber, H., & Müller, M. (2020).** Local Key Estimation in Music Recordings: A Case Study Across Songs, Versions, and Annotators. *IEEE/ACM TASLP*, 28. DOI: [10.1109/TASLP.2020.3030485](https://doi.org/10.1109/TASLP.2020.3030485).
  - Separates the **version** (performance) axis from the **annotator** axis.
  - **This is the design you need:** your corpus also has versions (Bilibili performances, anthology variants) and annotators (notators).
- **Volk, A., & van Kranenburg, P. (2012).** Melodic similarity among folk songs: An annotation study on similarity-based categorization in music. *Musicae Scientiae*, 16(3), 317–339. DOI: [10.1177/1029864912448329](https://doi.org/10.1177/1029864912448329). Expert folk-song annotators (Dutch tune families) agree on categorization driven by specific features. A folk-song precedent for feature-level agreement.
- **McKinney, M. F., Moelants, D., Davies, M. E. P., & Klapuri, A. (2007).** Evaluation of audio beat tracking and music tempo extraction algorithms. *JNMR*, 36(1). [DOI unverified.] Many annotators tapped beats, revealing metrical-level ambiguity. A precedent for **rhythm-level variance** (relevant to 散板).

### B8.3 Recommended operationalization (inference)

1. **Align first.** Do a multiple alignment of all transcriptions of a passage: progressive Needleman–Wunsch over tonic-relative scale degree plus duration, following the Savage/Ozaki code.
2. **Derive per-position soft labels.** These give distributions over scale degree, duration class, and ornament presence. Their entropy is a per-position **variance map**.
3. **Fit a hierarchical annotator model** (Paun et al. style, in Stan, brms, or PyMC). It should include transcriber bias and noise terms, item difficulty, and region and feature covariates. Test whether **item difficulty depends on region**: that is the "disagreement as fingerprint of the music" hypothesis. Test whether **transcriber or edition terms dominate**: that is the "fingerprint of the notation tradition" hypothesis.
4. **Treat AMT as an extra "annotator"** in the same model. Its bias and noise parameters, compared with the human distribution, *are* the envelope test (§B10).

---

## B9. Statistics: mixed-effects models and alternatives

### B9.1 Core references

- **Bates, D., Mächler, M., Bolker, B., & Walker, S. (2015).** Fitting Linear Mixed-Effects Models Using lme4. *JSS*, 67(1). DOI: [10.18637/jss.v067.i01](https://doi.org/10.18637/jss.v067.i01).
- **Kuznetsova, A., Brockhoff, P. B., & Christensen, R. H. B. (2017).** lmerTest. *JSS*, 82(13). [DOI 10.18637/jss.v082.i13 from memory.] Satterthwaite and Kenward–Roger degrees of freedom; these matter with few groups.
- **Barr, D. J., Levy, R., Scheepers, C., & Tily, H. J. (2013).** Random effects structure for confirmatory hypothesis testing: Keep it maximal. *J. Memory and Language*, 68(3), 255–278. DOI: [10.1016/j.jml.2012.11.001](https://doi.org/10.1016/j.jml.2012.11.001). Random-intercept-only models inflate Type I error.
- **Matuschek, H., Kliegl, R., Vasishth, S., Baayen, H., & Bates, D. (2017).** Balancing Type I error and power in linear mixed models. *JML*, 94, 305–315. DOI: [10.1016/j.jml.2017.01.001](https://doi.org/10.1016/j.jml.2017.01.001). Maximal models lose power; select a parsimonious structure. Cite both Barr and Matuschek, and preregister your choice.
- **Westfall, J., Kenny, D. A., & Judd, C. M. (2014).** Statistical power and optimal design in experiments in which samples of participants respond to samples of stimuli. *JEP: General*, 143(5). DOI: [10.1037/xge0000014](https://doi.org/10.1037/xge0000014). With **crossed random effects**, power plateaus with the number of the scarcer factor. Here that factor is regions or provinces, not notes.
- **Oberpriller, J., de Souza Leite, M., & Pichler, M. (2022).** Fixed or random? On the reliability of mixed-effects models for a small number of levels in grouping variables. *Ecology and Evolution*, 12, e9062. DOI: [10.1002/ece3.9062](https://doi.org/10.1002/ece3.9062). With fewer than about 5–8 levels, variance estimates are unstable, and singular fits are common but often harmless for the fixed effects.
- **Gelman, A. (2006).** Prior distributions for variance parameters in hierarchical models. *Bayesian Analysis*, 1(3). DOI: [10.1214/06-BA117A](https://doi.org/10.1214/06-BA117A). Half-t or half-Cauchy priors stabilize grouping factors with few levels. This is the main argument for going Bayesian with about 10 regions.
- **Hurlbert, S. H. (1984).** Pseudoreplication and the Design of Ecological Field Experiments. *Ecological Monographs*, 54(2). DOI: [10.2307/1942661](https://doi.org/10.2307/1942661). Notes within songs, and songs within one uploader or volume, are not independent replicates of "region".

### B9.2 Bayesian and distributional alternatives

- **Bürkner, P.-C. (2017).** brms: An R Package for Bayesian Multilevel Models Using Stan. *JSS*, 80(1). DOI: [10.18637/jss.v080.i01](https://doi.org/10.18637/jss.v080.i01). Supports `zero_one_inflated_beta`, `cumulative` (ordinal), `hurdle_*`, `gp()` spatial terms, and distributional (σ ~ predictors) models. The last lets you model **disagreement variance itself** as a function of region.
- **Capretto, T., Piho, C., Kumar, R., Westfall, J., Yarkoni, T., & Martin, O. A. (2022).** Bambi: A Simple Interface for Fitting Bayesian Linear Models in Python. *JSS*, 103(15). DOI: [10.18637/jss.v103.i15](https://doi.org/10.18637/jss.v103.i15).
- **Abril-Pla, O., et al. (2023).** PyMC: a modern, and comprehensive probabilistic programming framework in Python. *PeerJ Computer Science*, 9, e1516. DOI: [10.7717/peerj-cs.1516](https://doi.org/10.7717/peerj-cs.1516).
- **Brooks, M. E., et al. (2017).** glmmTMB Balances Speed and Flexibility Among Packages for Zero-inflated Generalized Linear Mixed Modeling. *R Journal*, 9(2), 378–400. DOI: [10.32614/RJ-2017-066](https://doi.org/10.32614/RJ-2017-066). A frequentist zero-inflated, beta, or negative-binomial GLMM with random effects.
- **Bürkner, P.-C., & Vuorre, M. (2019).** Ordinal Regression Models in Psychology: A Tutorial. *AMPPS*, 2(1). DOI: [10.1177/2515245918823199](https://doi.org/10.1177/2515245918823199). Use it for expert quality ratings (Holzapfel-style).

**Outcome-family guidance (inference):**

| Outcome | Recommended family | Why |
|---|---|---|
| Note matches out of reference notes | **Binomial GLMM** on counts | Better than modeling F as beta: it keeps the denominator and the true precision |
| Per-recording F or PID with exact 0s or 1s | Zero-one-inflated beta | Handles the boundary values |
| Insertion or split counts | Negative binomial with offset log(n_ref_notes) or log(duration), plus a zero-inflation or hurdle term if many recordings are perfect | Counts with exposure |
| Cents deviations | Student-t | Heavy tails from octave errors; or model octave errors as a separate mixture component |
| Disagreement entropy | Distributional model σ ~ region | Tests whether **variance**, not the mean, differs by region |

### B9.3 Random-effects structure for your design (inference)

**Units.** The lowest level is the note, or the aligned position, within a passage, within a song or recording. Examples:
- AMT error: recording × pipeline.
- Human disagreement: song × transcriber/edition.

**Grouping factors:**
- **Recording/song:** random intercept. Each recording is run through all pipelines, so this is **crossed** with pipeline.
- **Pipeline:** only about 4–8 levels, and these are the systems you want to compare. Make it a **fixed effect** and add region × pipeline interactions. Do not make it a random effect.
- **Source collection, volume, or editorial team:** in 集成 this is **nested in province**, which is nested in 色彩区. Use a random intercept for province or volume within region.
- **Uploader/channel (Bilibili):** a random intercept. It is crossed with region when an uploader posts several regions; otherwise it is nested.
- **Singer:** often unknown. Use uploader or performance as a proxy.
- **Transcriber:** crossed with song if one person transcribed songs from several regions, as in the calibration set; otherwise nested in volume.

**Fixed effects:**
- 色彩区 (about 10 levels; sum-to-zero coding).
- Pipeline.
- **Recording-quality covariates** to de-confound region from source quality: an SNR estimate, accompaniment presence or separation-residual ratio, a reverb estimate, codec bitrate, and year.
- Genre (山歌 mountain songs / 小调 ditties / 号子 work songs).
- Singer training style (原生态 "authentic/traditional" vs. 学院派 conservatory; humanities coding).

**Spatial or phylogenetic controls:**
- Add a Gaussian-process or SPDE term on the collection-site location (brms `gp()`, INLA, or spaMM). Also consider a language/ethnicity grouping, such as dialect group or Glottolog family for minority songs.
- **Caution — Hodges, J. S., & Reich, B. J. (2010).** Adding Spatially-Correlated Errors Can Mess Up the Fixed Effect You Love. *The American Statistician*, 64(4), 325–334. DOI: [10.1198/tast.2010.10052](https://doi.org/10.1198/tast.2010.10052). 色彩区 is *itself* a spatial partition, so a smooth spatial term competes with it.
- **Framing:** the question becomes *does a categorical 色彩区 partition explain variance beyond a smooth geographic surface?* Compare three models (region only; spatial GP only; both) with LOO-CV or ELPD. Optionally test **discontinuities at region boundaries**, such as pairs of nearby sites on opposite sides of a boundary. Boundary sharpness is the strongest evidence that "regions are real" and not just distance-decay.
- **Dormann, C. F., et al. (2007).** Methods to account for spatial autocorrelation in the analysis of species distributional data: a review. *Ecography*, 30. [DOI UNVERIFIED.]

**Precedents for controlling phylogeny and space in music:**
- **Brown, S., Savage, P. E., Ko, A. M.-S., Stoneking, M., Ko, Y.-C., Loo, J.-H., & Trejaut, J. A. (2014).** Correlations in the population structure of music, genes and language. *Proc. R. Soc. B*, 281, 20132072. DOI: [10.1098/rspb.2013.2072](https://doi.org/10.1098/rspb.2013.2072). Taiwan: music correlated with genes more than with language. [Full author list from memory.]
- **Passmore, S., Wood, A. L. C., Barbieri, C., Shilton, D., Daikoku, H., Atkinson, Q. D., & Savage, P. E. (2024).** Global musical diversity is largely independent of linguistic and genetic histories. *Nature Communications*, 15, 3964. DOI: [10.1038/s41467-024-48113-7](https://doi.org/10.1038/s41467-024-48113-7). Musical similarity is only weakly tied to language or genetic relatedness, with regional exceptions. **Direct precedent for "feature-sharing as cultural interaction" claims**, and for the needed controls: geographic distance, linguistic phylogeny, and genetic distance. [Exact modelling details, such as Mantel or phylogenetic regression, should be checked in the paper.]
- **Mehr, S. A., et al. (2019).** Universality and diversity in human song. *Science*, 366, eaax0868. DOI: [10.1126/science.aax0868](https://doi.org/10.1126/science.aax0868). Large-scale hierarchical modelling of song features across societies.

### B9.4 Power at about 700 recordings and about 10 regions

- **Green, P., & MacLeod, C. J. (2016).** SIMR: an R package for power analysis of generalized linear mixed models by simulation. *Methods in Ecology and Evolution*, 7(4). DOI: [10.1111/2041-210X.12504](https://doi.org/10.1111/2041-210X.12504).
- **Kumle, L., Võ, M. L.-H., & Draschkow, D. (2021).** Estimating power in (generalized) linear mixed models: An open introduction and tutorial in R. *Behavior Research Methods*, 53, 2528–2543. [PubMed 33954914](https://pubmed.ncbi.nlm.nih.gov/33954914/). Notebooks: [lkumle.github.io/power_notebooks](https://lkumle.github.io/power_notebooks/).
- **Blair, G., Cooper, J., Coppock, A., & Humphreys, M. (2019).** Declaring and Diagnosing Research Designs. *APSR*, 113(3). [Cambridge](https://www.cambridge.org/core/journals/american-political-science-review/article/declaring-and-diagnosing-research-designs/3CB0C0BB0810AEF8FF65446B3E2E4926). Software: [DeclareDesign](https://declaredesign.org/).

**Recommended simulation (inference):**
1. Take ICCs from a pilot (for example 100 recordings): song, uploader, and province variance.
2. Simulate the **realistic unbalanced allocation** across regions. Bilibili availability is very uneven, and some regions may have fewer than 30 recordings.
3. Vary the region effect over plausible ranges, for example a 3–10 point difference in note F, or a 5–15 cent difference in median deviation.
4. Report power for three targets: the omnibus region effect, region × pipeline interactions, and **variance (σ) differences**.

**Rule of thumb from Westfall et al. 2014 (not a guarantee):** if province or uploader variance is non-trivial, power is limited by the roughly 10 regions and their provinces. Adding recordings within over-represented regions helps little; balancing across regions helps a lot.

**Multiplicity across features × regions:** fit one hierarchical model with partial pooling across features. [Gelman, Hill & Yajima (2012), "Why we (usually) don't have to worry about multiple comparisons", *J. Res. Educ. Effectiveness*, is UNVERIFIED in this session.]

---

## B10. Benchmarking model deviation against inter-expert variance

### B10.1 Sources

- **Hayes, A. F., & Krippendorff, K. (2007).** Answering the Call for a Standard Reliability Measure for Coding Data. *Communication Methods and Measures*, 1(1), 77–89. DOI: [10.1080/19312450709336664](https://doi.org/10.1080/19312450709336664).
  - α handles any number of coders, missing data, and nominal, ordinal, interval, or ratio metrics. Use the interval metric for cents.
  - Python: [pln-fing-udelar/fast-krippendorff](https://github.com/pln-fing-udelar/fast-krippendorff) (`pip install krippendorff`).
- **Shrout, P. E., & Fleiss, J. L. (1979).** Intraclass correlations: Uses in assessing rater reliability. *Psychological Bulletin*, 86(2). [UNVERIFIED in this session.] Use ICC for continuous features such as tempo or median deviation.
- **Lakens, D. (2017).** Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses. *Social Psychological and Personality Science*, 8(4), 355–362. DOI: [10.1177/1948550617697177](https://doi.org/10.1177/1948550617697177). R: [Lakens/TOSTER](https://github.com/Lakens/TOSTER).
- **Lakens, D., Scheel, A. M., & Isager, P. M. (2018).** Equivalence Testing for Psychological Research: A Tutorial. *AMPPS.* [UNVERIFIED in this session.]
- **Kruschke, J. K. (2018).** Rejecting or Accepting Parameter Values in Bayesian Estimation. *AMPPS*, 1(2), 270–280. DOI: [10.1177/2515245918771304](https://doi.org/10.1177/2515245918771304). The HDI+ROPE rule is the Bayesian counterpart of TOST; it fits brms output naturally.
- **Flexer & Grill (2016)**, **Ni et al. (2013)**, and **Gordon et al. (2021)**: the human-ceiling and deconvolution arguments (above).
- **Balke et al. (2016)**: evaluation against several references (above).
- **Ozaki et al. (2021)**: human vs. automatic κ and PID within one design (above).
- **Bland & Altman (1986)**: limits of agreement (above).

### B10.2 Recommended protocol (inference; strongest when you have same-audio, multi-expert data)

For each feature *f* (pitch class, cents, onset, duration, ornament, boundary) and each region *r*:

1. **Human envelope.** Compute the distribution of pairwise human–human distances **D_HH(f, r)** on the calibration items, using leave-one-transcriber-out to estimate the spread.
2. **Model distance.** Compute **D_MH(f, r)** between the model and each human, averaged over humans. This is the multi-reference distance; also report the distance to the *closest* human, analogous to multi-reference BLEU.
3. **Quantity of interest.** Δ(f, r) = D_MH − mean(D_HH).
4. **Equivalence margin, preregistered.** For example, ±0.5 × SD of D_HH, or the 90th percentile of D_HH. **Inside the envelope** means a TOST rejects |Δ| ≥ margin, or the 95% HDI lies inside the ROPE.
5. **Rater-substitution test.** Replace one human with the model, recompute Krippendorff's α, and bootstrap over items. The model is **"an indistinguishable additional rater"** if α does not drop beyond the bootstrap interval of human-only substitutions.
6. **Distributional test.** Score the model's note decisions against the per-position soft-label distribution (cross-entropy or Jensen–Shannon divergence, as in Uma et al. 2021). Compare with each held-out human's score against the remaining humans.
7. **Estimate everything hierarchically.** Use one model with feature × region × rater-type (human/model) terms, so that sparse regions shrink.

**Interpretive grid:**

| Model position | Human variance | Interpretation |
|---|---|---|
| Inside the envelope | High | The feature is *intrinsically ambiguous*: the music's property (fingerprint) |
| Outside the envelope | Low | *Model failure* specific to the tradition |
| Outside the envelope | High | Both are uncertain; investigate whether the deviation is "outside" in a *consistent direction*, such as 12-TET snapping. That would be epistemic bias, not noise |

---

## B11. Concrete open-source tool stack

| Stage | Tools (repos) | Notes |
|---|---|---|
| Ingest | `yt-dlp` / Bilibili downloader, ffmpeg | Log codec and bitrate as covariates; keep original audio hashes |
| Separation | [HT-Demucs](https://github.com/facebookresearch/demucs); Mel/BS-RoFormer via [ZFTurbo MSST](https://github.com/ZFTurbo/Music-Source-Separation-Training) | Run the F0 step on both the mixture and the separated vocals; the difference is a diagnostic |
| F0 | `librosa.pyin` (training-free control); [CREPE](https://github.com/marl/crepe); [RMVPE](https://github.com/Dream-High/RMVPE); [FCPE](https://github.com/CNChTu/FCPE); PESTO (fine-tunable) | **Keep the continuous F0 as the primary data layer** |
| Notes | [Basic Pitch](https://github.com/spotify/basic-pitch) (with pitch bends); [ROSVOT](https://github.com/RickyL-2000/ROSVOT); [SOME](https://github.com/openvpi/SOME); [VOCANO](https://github.com/B05901022/VOCANO); [MT3](https://github.com/magenta/mt3) / YourMT3+ | Pipelines form a fixed-effect factor |
| Human correction and annotation | Tony (pYIN-based; Mauch et al. 2015, [TENOR PDF](https://www.tenor-conference.org/proceedings/2015/04-Mauch-Tony.pdf)); Sonic Visualiser | For calibration-set F0 ground truth |
| Symbolic | music21 (Cuthbert & Ariza, ISMIR 2010, [dblp](https://dblp.org/rec/conf/ismir/CuthbertA10.html)); [musicdiff](https://github.com/gregchapman-dev/musicdiff); [MV2H](https://github.com/apmcleod/MV2H); OMR-NED; partitura [repo not checked] | Use a jianpu → tonic-relative representation |
| Alignment | Needleman–Wunsch from [comp-music-lab/agreement-human-automated](https://github.com/comp-music-lab/agreement-human-automated); [synctoolbox](https://pypi.org/project/synctoolbox/); librosa DTW | Run a transposition search |
| Metrics | [mir_eval](https://mir-eval.readthedocs.io/) (transcription, melody, segment); a Molina-category reimplementation; [PEAMT](https://github.com/adrienycart/PEAMT) | Use tolerance sweeps |
| Pitch distributions | Tarsos; custom per-scale-degree KDEs (Koduri et al. 2014 style) | |
| Agreement | [krippendorff](https://github.com/pln-fing-udelar/fast-krippendorff); R `irr` [not checked]; Dawid–Skene via `crowd-kit` [not checked] or Stan | |
| Statistics | lme4 + lmerTest; glmmTMB; brms (`zoib`, `gp`, distributional σ); Bambi/PyMC; DHARMa residual checks [not checked]; LOO via `loo`/ArviZ | |
| Power | [simr](https://cran.r-project.org/web/packages/simr/index.html); [DeclareDesign](https://declaredesign.org/); brms simulate-and-refit | |
| Equivalence | [TOSTER](https://github.com/Lakens/TOSTER); ROPE via bayestestR [not checked] | |

---

## B12. Strongest technical reviewer objections, with mitigations

1. **"Disagreement between anthologies isn't transcriber disagreement — the singers and variants differ."** This is the central confound.
   - *Mitigation:* a calibration subset of the same audio with at least 3 independent expert notators per item (Ozaki design), stratified across regions.
   - Decompose variance into performance/variant and transcriber components (Weiß et al. 2020 design).
   - Use cross-anthology comparisons only for **tune-family-level** claims (Savage 2022 alignment).
2. **"色彩区 is confounded with editorial team, transcriber school, and recording source."** 集成 volumes were compiled province by province.
   - *Mitigation:* add volume/editor as a random effect within region. Use within-province contrasts. Look for transcribers who worked across provinces. Show the region effect survives once recording-quality covariates are added.
3. **"Circularity: the 色彩区 boundaries were drawn from the same anthology material."**
   - *Mitigation:* test region on features *not* used to define the regions, such as cents intonation, ornament density from audio, or AMT failure profiles.
   - Use the Bilibili audio as an out-of-sample set, and use Essen Han/Natmin as an external replication set.
4. **"The OCR layer is not a human reference."** Bu et al. (2025) report about 95% note F1 on similar material.
   - *Mitigation:* run an OCR error audit with OMR-NED on a stratified hand-checked sample, and estimate the OCR error rate per volume or region. Propagate OCR uncertainty, for example as a measurement-error term or a sensitivity analysis.
5. **"12-TET MIDI quantization *builds in* the Western bias you claim to measure."**
   - *Mitigation:* make the continuous F0 and cents the primary layer. Report MIDI-level results as one condition. Use Basic Pitch bends and SOME's non-integer MIDI.
6. **"Your 'Western-trained' models are mostly trained on Mandarin pop."**
   - *Mitigation:* compare the training-free (pYIN plus a heuristic segmenter), pop-Mandarin-trained (ROSVOT/SOME), and Western-multi-instrument-trained (MT3) arms. Fine-tune PESTO without labels as a domain-adapted arm.
   - This turns the objection into a result: three priors, not one.
7. **"AMT failure just tracks recording quality."**
   - *Mitigation:* model quality covariates explicitly; match recordings on quality across regions; and check whether region effects keep the **same direction** on the cleanest quartile.
8. **"Pseudo-replication and too few regions."**
   - *Mitigation:* treat songs or recordings as units, with notes as within-unit observations. Make inferences at the region level with appropriate degrees of freedom or Bayesian partial pooling. Do a preregistered simulation power analysis and report it.
9. **"Bilibili sample bias: conservatory (学院派) performers homogenize regional style; uploader selection is unknown."**
   - *Mitigation:* code performer style (humanities line), and include uploader as a random effect. Restrict the main analyses to field recordings where possible. Report a sensitivity analysis.
10. **"Metrics don't capture musicological validity"** (Holzapfel et al. 2022; Ycart et al. 2020; Wang et al. 2026).
    - *Mitigation:* collect a small expert-rating study of AMT outputs per region with an ordinal model, and show which metrics track the ratings.
11. **"Regions might be gradients, not discrete types"** (Cornelissen et al. 2026; Hodges & Reich 2010).
    - *Mitigation:* compare discrete and continuous spatial models with LOO, and run boundary-discontinuity tests.
12. **Data ethics and licensing** of Bilibili audio and 集成 scans.
    - Release derived features, alignment code, and metadata, not the audio. Follow the SOME README's caution about consent.

---

## B13. Where the English-language literature is strong vs. thin

**Strong (cite liberally):**
- General AMT and F0 tracking.
- mir_eval-style metrics and their limits.
- Annotator disagreement and soft labels (mostly NLP and vision).
- Annotator subjectivity in chords, melody, key, and beat in MIR.
- Mixed models and power analysis; equivalence testing.
- Computational analysis of makam, Carnatic, flamenco, and jingju (CompMusic).
- Phylogenetic and geographic controls in comparative musicology (Savage group).

**Thin (and where Chinese-language work is essential):**
1. **AMT of Chinese folk singing.** I found no peer-reviewed English benchmark. CCMusic has folk-vs-bel-canto *classification* but no note ground truth. Jingju is the nearest analogue.
2. **Computational 色彩区.** The English sources are a handful of small classification papers (Li et al. 2017; Yang et al. 2018; Liu et al. 2022; MG-VAE), with unclear provenance and no released data. The **feature definitions** of 色彩区 (苗晶, 乔建中, 杜亚雄 and others) exist only in Chinese and come from the humanities line. Computational operationalization must start from those definitions.
3. **Jianpu encoding and OMR:** Bu et al. (2025) and Yang et al. (2025) are recent and few. There is no standard encoding.
4. **Ornament (润腔) metrics:** essentially absent in English MIR. Chinese musicology has a detailed 润腔 (ornamentation/vocal inflection) terminology that should drive the ornament taxonomy.
5. **Heterophony in AMT evaluation:** almost no dedicated work.
6. **Chinese-language computational literature** (e.g., in 《中国音乐学》, 《音乐研究》, 《中央音乐学院学报》, 《复旦学报》, and Chinese CS venues). I did **not** verify any specific Chinese-language MIR paper in this pass; CNKI or Wanfang access is needed. Han Baoqiang's (韩宝强) acoustics and pitch-measurement work and Li Wei's (李伟, Fudan) MIR group (CCMusic co-authors) are the obvious entry points.

---

## B14. Technical-side testable sub-hypotheses (for the integrated spine)

| ID | Hypothesis | Main test |
|---|---|---|
| T1 (envelope) | For pitch-class identity, AMT falls **outside** the human envelope in regions with dense glides or ornaments, and **inside** it in regions with plainer syllabic styles | Region × feature TOST or ROPE on Δ |
| T2 (fingerprint of the music) | Human disagreement entropy per aligned position is predicted by local acoustic features (glide extent, note duration < 150 ms, melisma), and its region means differ beyond transcriber or edition effects | Distributional model σ ~ region + local features + (1\|transcriber) |
| T3 (fingerprint of the notation tradition) | Edition or transcriber random effects explain more variance in rhythm and ornament notation than in pitch class | Variance-component comparison by feature |
| T4 (where AMT fails) | AMT split rates are highest where human disagreement over ornaments is highest. This would mean the two struggle with the same phenomena, not that AMT makes random errors | Correlation of the per-position Molina split rate with human entropy, within region |
| T5 (quantization bias) | Cents deviations of sung scale degrees from 12-TET are region-structured (e.g., 苦音 degrees). 12-TET-quantizing pipelines show *systematic*, consistently directed pitch-class errors at exactly those degrees | Per-degree deviation distributions; direction-consistency test |
| T6 (training prior) | The gap between the training-free (pYIN) and pop-trained (ROSVOT/SOME) pipelines varies by region and grows with stylistic distance from Mandarin pop | Region × pipeline interaction |
| T7 (meter) | MV2H meter and value scores collapse for 散板 genres regardless of region; the region effect on rhythm errors is mediated by genre | Mediation or stratification |
| T8 (regions vs. gradients) | A categorical 色彩区 term improves LOO fit over a smooth spatial GP for at least some features, and boundary-straddling site pairs show discontinuities | ELPD comparison; boundary test |
| T9 (interaction or contact) | Error and variance profiles of songs from border or migration zones (e.g., 走西口 "going west of the pass" routes) are mixtures of neighboring regions' profiles | Mixture-membership model on profile vectors, controlling for distance (Passmore 2024-style controls) |

---

---

# Appendix C — Verification to-do before submission

**Humanities items (Part A):**
- 杜亚雄 1993, Chinese title of the "music dialect area" paper (the English title is known only via Luo et al. 2019)
- Whether 于会泳 originated the term 腔音列
- 冯光钰's transmission monograph and any 《中国同宗民歌》 book: title, year, publisher
- 王耀华 《中国传统音乐结构学》: publisher and year
- The earlier journal version of 苗晶 & 乔建中, and the per-region musical criteria in the 1987 book
- Yang Mu 1994 page range; Yang Mu 2003 volume and pages
- Brown et al. 2014 article number; Savage et al. 2015 full author list
- Holzapfel, Krebs & Srinivasamurthy 2014 author list
- Morrison, Demorest & Pearce 2019 book title
- England 1964 symposium full page range; List 1974 detailed findings

**Technical items (Part B):**
- YourMT3+ venue (IEEE MLSP 2024?)
- VOCANO author list; Gong et al. 2017 venue (DLfM?)
- Bozkurt et al. 2014 co-authors and DOI; Wang et al. 2019 erhu author list
- Essen Folksong Collection canonical citation
- lmerTest DOI; Raykar et al. 2010; Passonneau & Carpenter 2014; Shrout & Fleiss 1979; Lakens et al. 2018; Gelman, Hill & Yajima 2012; Dormann et al. 2007 DOI; McKinney et al. 2007 DOI
- Ycart et al. 2020 co-authors; Brown et al. 2014 full author list; Passmore et al. 2024 modelling details

**Not yet searched:** CNKI and Wanfang, for Chinese-language computational studies of 民歌 regional style, measured 苦音 intonation, and 同宗民歌 diffusion.
