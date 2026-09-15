# Gap Filling Plan

Plan for filling modality and metadata gaps in Aquarius. Execution is a separate, human-approved phase. All imputed values carry confidence scores and method tags; nothing overwrites original data.

---

## 1. Current State

| Metric | Value |
|--------|-------|
| Total items | 45,611 |
| Datasets integrated | 11 |
| Audio coverage | 4.0% (1,842 items) |
| MIDI coverage | 22.5% (10,262 items) |
| MusicXML coverage | 19.1% (8,725 items) |
| Lyrics coverage | 7.0% (3,196 items) |
| Title coverage | 94.0% |
| Artist coverage | 3.8% |
| Key coverage | 5.2% |
| Province coverage | 93.8% |
| Chinese mode coverage | 0% |
| Temporal/year coverage | 0% |

Key insight: MGD contributes 31,761 metadata-only items (69.6%), inflating apparent metadata coverage and deflating modality percentages. Excluding MGD, audio coverage rises to ~13%, MIDI to ~74%.

---

## 2. Modality Generation

### 2.1 Audio Synthesis from MIDI/MusicXML

**Target**: 10,262 MIDI items (POP909, Anthology, M4Singer) + 8,725 MusicXML items

**Method**:
- FluidSynth with Chinese instrument soundfonts (erhu, pipa, guzheng, dizi, etc.)
- For folk songs (Anthology): use appropriate regional instruments based on province metadata
- For pop (POP909): use piano + general MIDI instruments
- For vocal (M4Singer): skip synthesis (already has audio); use MIDI for alignment only

**Soundfont sources**:
- Sonatina Symphonic Orchestra (free, includes erhu, pipa via patches)
- Chinese instrument soundfonts from freepats.zenvoid.org and Musical Artifacts
- Custom: record single-note samples from CTIS/ChMusic audio for authentic timbres

**Quality thresholds**:
- Sample rate: 44100 Hz minimum
- Bit depth: 16-bit minimum
- Duration match: synthesized audio within ±2% of MIDI duration
- Tag all synthesized audio with `provenance: "synthesized"` and source MIDI path

**Priority**: Medium — useful for completeness, but synthetic audio is clearly labeled and not a substitute for real recordings.

### 2.2 Audio→MIDI Transcription

**Target**: 1,842 audio-only items (ChMusic, CTIS, GZ_IsoTech, PMEmo, Jingju)

**Method**:
- Basic Pitch (Spotify) for monophonic transcription (erhu, dizi, vocal)
- MT3 (Google) for polyphonic transcription (guzheng, pipa, ensemble)
- Onsets and Frames for piano-heavy items (PMEmo pop music)

**Accuracy expectations**:
- Monophonic Chinese instruments: ~85-90% note-level F1 (well-suited for Basic Pitch)
- Polyphonic/ensemble: ~60-75% F1 (lower confidence)
- Beijing Opera vocal: ~70-80% F1 (ornamented, melismatic — harder)

**Confidence tagging**:
- `confidence: "high"` for monophonic with clean audio
- `confidence: "medium"` for polyphonic or noisy
- `confidence: "low"` for ensemble or highly ornamented

**Priority**: Low — most audio datasets are used for timbre/technique analysis, not melodic content.

### 2.3 Score Generation (MusicXML/Jianpu)

**Target**: MIDI items without MusicXML (POP909: 909, M4Singer: 699)

**Method**:
- music21 MIDI→MusicXML conversion (quantize to nearest 16th note)
- For folk songs: additionally generate numbered musical notation (jianpu) via custom converter
- Jianpu generation requires: key detection → scale degree mapping → jianpu symbols

**Quality thresholds**:
- Quantization tolerance: 50ms
- Human spot-check: 5% random sample per dataset
- Jianpu: validate scale degree accuracy against known key

**Priority**: Low — MIDI is already machine-readable; score is mainly for human visualization.

---

## 3. Metadata Imputation

### 3.1 Key and Mode Detection (Impact: Critical)

**Current coverage**: 5.2% (key), 0% (Chinese pentatonic mode)

**Method — Key detection**:
1. MIDI/MusicXML items (19,000+): pitch-class histogram → Krumhansl-Schmuckler key-finding algorithm
2. Audio items (1,842): Essentia or librosa chromagram → key estimation
3. Cross-validate: if MIDI and audio both available, require agreement

**Method — Chinese pentatonic mode**:
1. Compute pitch-class distribution from MIDI/MusicXML
2. Map to 5 pentatonic modes using template matching:
   - Gong (宫): 1-2-3-5-6 (C-D-E-G-A in C)
   - Shang (商): 2-3-5-6-1
   - Jue (角): 3-5-6-1-2
   - Zhi (徵): 5-6-1-2-3
   - Yu (羽): 6-1-2-3-5
3. Use final note (ending note bias toward tonic) as tiebreaker
4. Confidence based on: distribution fit score, final note match, absence of non-pentatonic notes

**Confidence levels**:
- `high`: distribution clearly matches one mode, final note confirms, >90% pentatonic notes
- `medium`: best-fit mode, but 2nd-best within 0.1 correlation, or 10-20% non-pentatonic notes
- `low`: ambiguous distribution, chromatic/modulating passages, short excerpt

**Validation**:
- Anthology (MusicXML, folk songs): most should be clearly pentatonic — expect >80% high-confidence
- POP909 (pop): many will be Western-influenced, mixed modes — expect more `low` confidence
- Cross-reference with Kaggle folk music `pitch_key` labels (2,374 items with ground truth)

**Priority**: **HIGHEST** — this is the defining contribution of a Chinese music database.

### 3.2 Genre Classification (Impact: High)

**Current coverage**: 100% (but only because unify.py assigns dataset-level genre)

The 100% coverage is misleading — most items have a coarse genre from their dataset context (e.g., all MGD items are "folk"), not a fine-grained label. True fine-grained genre coverage is much lower.

**Method**:
1. **Dataset-level assignment** (already done): folk, pop, traditional instrumental, Beijing Opera, etc.
2. **Sub-genre inference** from metadata:
   - MGD: 9 folk song types already in data (shan'ge, haozi, xiaodiao, etc.)
   - Kaggle: style_label (3 categories) and theme_label (4 categories)
   - Jingju: shengqiang (xipi/erhuang) + banshi as sub-genre
3. **Title-based classification** for Anthology/MGD: keyword patterns in Chinese titles map to song types
4. **Instrument-based inference**: guzheng pieces → traditional instrumental; erhu solo → traditional; MIDI arrangements → pop

**Confidence**: Medium-high for dataset-level, low-medium for sub-genre inference from titles.

**Priority**: Medium — coarse genre is already complete; sub-genre adds value but is harder to validate.

### 3.3 Artist/Performer Attribution (Impact: Medium)

**Current coverage**: 3.8% (1,741 items)

**Method**:
1. **POP909**: cross-reference 909 Chinese pop songs with MusicBrainz/NetEase Music databases by title
2. **MGD**: metadata Excel files may contain artist info in unused columns — re-inspect
3. **Anthology**: folk songs generally anonymous; mark as `artist: "traditional/anonymous"`
4. **M4Singer**: has singer_id but not singer name — map IDs to names from paper supplement
5. **Jingju Arias**: 34 arias have artist in TextGrid annotations — extract

**Confidence**: High for database lookups with exact title match, low for inferred.

**Priority**: Medium — important for musicological analysis but not for computational tasks.

### 3.4 Temporal/Year Metadata (Impact: Medium)

**Current coverage**: 0%

**Method**:
1. **POP909**: look up release year from MusicBrainz/Chinese music databases by song title + artist
2. **Guqin**: map 琴曲来源 (score source) to historical periods (e.g., 神奇秘谱 → Ming dynasty, ~1425)
3. **Folk songs (Anthology/MGD)**: assign collection period from dataset publication date (2019-2023)
4. **Jingju**: assign "traditional" + approximate era based on aria repertoire studies
5. **PMEmo**: release year available from MusicBrainz by musicId

**Confidence**:
- `high`: database lookup with confirmed match
- `medium`: score source → dynasty mapping (Guqin)
- `low`: genre-era inference, collection date as proxy

**Priority**: Medium — temporal dimension is important for musicological analysis.

### 3.5 Instrument Identification (Impact: Medium)

**Current coverage**: 5.5% (2,508 items)

**Method**:
1. **Dataset-level inference**: all ChMusic items get their instrument code; all CTIS items already have 219 instrument labels
2. **Audio classification**: use CTIS training data (219 Chinese instruments) to train/apply classifier on unlabeled audio
3. **MIDI program mapping**: POP909 MIDI program numbers → General MIDI instrument names
4. **Title/filename parsing**: many Chinese music files contain instrument name in title (e.g., "二胡独奏_xxx")

**Confidence**: High for labeled datasets, medium for MIDI programs, low for audio classification.

**Priority**: Medium — instrument is a core organizing dimension for Chinese music.

### 3.6 Province/Region (Impact: Low)

**Current coverage**: 93.8% (already high due to MGD + Anthology)

**Method**: For the remaining 6.2% (2,822 items):
1. **Instrument-origin mapping**: guzheng → Henan/Guangdong tradition; erhu → widespread; guqin → literati tradition (no single province)
2. **Title keyword extraction**: province/city names in Chinese titles
3. **Genre-region mapping**: Beijing Opera → Beijing; Kunqu → Jiangsu

**Priority**: Low — already well-covered.

---

## 4. Confidence Tracking

Every imputed value in the master table gets two additional columns:

| Column pattern | Type | Values |
|----------------|------|--------|
| `{field}_confidence` | float | 0.0–1.0 |
| `{field}_method` | string | Method tag |

### Method tags

| Tag | Meaning |
|-----|---------|
| `source` | Original value from dataset |
| `key_profile` | Krumhansl-Schmuckler key-finding |
| `pentatonic_template` | Chinese pentatonic mode template matching |
| `midi_program` | MIDI program number lookup |
| `audio_classifier` | Audio-based instrument/genre classification |
| `db_lookup` | External database cross-reference (MusicBrainz, etc.) |
| `title_parse` | Keyword extraction from title/filename |
| `dataset_level` | Assigned from dataset-level metadata |
| `genre_era` | Inferred from genre→era mapping |
| `score_source` | Inferred from historical score attribution |
| `synthesis` | Generated via FluidSynth/other synthesis |
| `transcription` | Generated via audio→MIDI transcription |

### Storage

- Original `master_table.parquet` preserved as `master_table_v1_source_only.parquet`
- Imputed table saved as `master_table_v2_imputed.parquet`
- Provenance matrix: `data/unified/provenance_matrix.csv` tracks source vs. imputed per cell

---

## 5. Validation

### 5.1 Sample-Based Human Review

| Imputation type | Sample size | Accept threshold |
|-----------------|-------------|-----------------|
| Key detection (MIDI) | 50 items | >90% correct |
| Pentatonic mode | 100 items | >80% correct |
| Key detection (audio) | 30 items | >80% correct |
| Genre sub-type | 50 items | >85% correct |
| Artist lookup | 30 items | >95% correct |
| Year lookup | 30 items | >90% correct |

### 5.2 Cross-Validation

- Key: compare MIDI-derived key vs. audio-derived key on items with both modalities
- Mode: compare pentatonic mode from MIDI vs. MusicXML on Anthology items (both available)
- Genre: compare inferred genre vs. dataset-level genre (should be consistent)
- Province: compare title-inferred province vs. MGD metadata province

### 5.3 Consistency Checks

- Key and mode should be compatible (e.g., C-gong and C-major share the same tonic)
- Instrument should match genre (erhu unlikely in pop; piano unlikely in folk)
- Province should match genre (Beijing Opera → Beijing area; shan'ge → mountainous provinces)
- Year should match genre/artist era (pop songs after 1980; traditional pre-1949)

---

## 6. Prioritization

Ordered by impact × confidence × feasibility:

| Rank | Task | Impact | Confidence | Items affected | Effort |
|------|------|--------|------------|----------------|--------|
| 1 | Pentatonic mode detection | Critical | Medium | ~19,000 (MIDI/XML) | Medium |
| 2 | Key detection (MIDI/XML) | High | High | ~19,000 | Low |
| 3 | Key detection (audio) | High | Medium | ~1,800 | Medium |
| 4 | Artist lookup (POP909) | Medium | High | 909 | Low |
| 5 | Year lookup (POP909) | Medium | High | 909 | Low |
| 6 | Instrument from MIDI programs | Medium | High | 909 | Low |
| 7 | Sub-genre from MGD types | Medium | High | 31,761 | Low |
| 8 | Guqin dynasty mapping | Medium | Medium | 71 | Low |
| 9 | Audio→MIDI transcription | Low | Medium | 1,842 | High |
| 10 | MIDI→audio synthesis | Low | Medium | 10,262 | High |

### Execution phases

**Phase A (Quick wins, ~2 days)**:
- Key detection on all MIDI/MusicXML items
- Pentatonic mode detection on all MIDI/MusicXML items
- MGD sub-genre extraction (already in data, just map to unified field)
- POP909 artist/year lookup via MusicBrainz
- MIDI instrument program extraction

**Phase B (Medium effort, ~3 days)**:
- Key/mode detection on audio items
- Guqin dynasty/era mapping
- Jingju artist extraction from TextGrids
- Title-based instrument and province inference
- Human validation sampling for Phase A outputs

**Phase C (Heavy computation, ~5 days)**:
- Audio→MIDI transcription (1,842 items)
- Audio instrument classification using CTIS training data
- MIDI→audio synthesis (10,262 items, if desired)
- Score generation (MusicXML from MIDI)
- Full validation pass

---

## 7. Implementation Notes

### Dependencies
- `music21` — MIDI/MusicXML parsing, key detection, score generation
- `librosa` or `essentia` — audio feature extraction, chromagram
- `fluidsynth` + `pyfluidsynth` — audio synthesis
- `basic-pitch` — monophonic audio→MIDI
- `musicbrainzngs` — MusicBrainz API for artist/year lookup
- `scipy` — correlation for template matching

### Pentatonic mode detection algorithm (pseudocode)
```
pitch_classes = extract_pitch_class_histogram(midi_or_xml)
templates = {
    "gong":  [1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],  # C D E G A
    "shang": [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0],  # D E G A C
    "jue":   [0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1],  # E G A C D  (shifted)
    ...rotate for all 12 tonics × 5 modes
}
best_match = argmax(correlate(pitch_classes, template) for template in all_templates)
final_note_bonus = check_final_note(midi_or_xml)
confidence = correlation_score * (1 + final_note_bonus * 0.1)
```

### File outputs
- `data/unified/master_table_v2_imputed.parquet`
- `data/unified/provenance_matrix.csv`
- `data/unified/imputation_log.json` (per-field statistics: attempted, succeeded, confidence distribution)
- `docs/imputation_report.md` (human-readable summary with validation results)
