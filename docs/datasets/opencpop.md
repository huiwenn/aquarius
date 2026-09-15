# Opencpop

## Source
- URL: https://github.com/wenet-e2e/opencpop
- Website: https://wenet-e2e.github.io/opencpop/ (also mirrored at xinshengwang.github.io/opencpop/)
- Paper: Wang et al. (2022). "Opencpop: A High-Quality Open Source Chinese Popular Song Corpus for Singing Voice Synthesis." INTERSPEECH 2022. https://arxiv.org/abs/2201.07429
- License: CC BY 4.0 (non-commercial use per terms of access form)
- Contact: zpcoftts@gmail.com
- Access method: Gated — Google Form application, download link sent via email
- Status: blocked-by-form

## Paper & Description Insights
Opencpop is a high-quality Mandarin singing corpus designed for singing voice synthesis (SVS) systems. Contains 100 unique Chinese pop songs with 3,756 utterances totaling ~5.2 hours of audio. Recorded by a professional female singer in studio conditions at 44,100 Hz.

Provides phonetic annotations with utterance/note/phoneme boundaries and pitch types. Includes baseline synthesized results for evaluation. The dataset is important as a foundational resource for Mandarin SVS — several derivative datasets build on it (ACE-OpenCpop, ACE-OpenCpop segments).

## Content & Taxonomy Analysis
- Time period: Contemporary Chinese pop
- Region: Mainland China
- Genre/form: C-pop / Mandopop (singing voice)
- Instrumentation: Vocal only (single professional female singer)
- Musical system: Western diatonic (Chinese pop songs use Western temperament)
- Language: Mandarin Chinese
- Modalities: Audio (WAV, 44,100 Hz), MIDI, Praat TextGrid annotations, phonetic transcriptions
- Labels: utterance boundaries, note boundaries (pitch + duration), phoneme boundaries (with durations), slur flags (0/1)
- Time signatures: Mostly 4/4, three songs in 3/4 (songs 005, 076, 097)
- BPM range: 40-130 BPM across 100 songs
- Note: Single-singer dataset — limited speaker/timbre diversity
- Derivative datasets: ACE-OpenCpop, ACE-OpenCpop segments (extended versions)

## Download Log
- Date attempted: 2026-09-15
- Method: Investigated all available download routes
- Official download page: https://wenet-e2e.github.io/opencpop/download
- Download requires Google Form submission: https://forms.gle/LnsbLqE6GcExhT5U6
  - Fields: email, full name, organization, address (country/province/city)
  - Terms: non-commercial research only, must cite paper, cannot share download link
  - After submission, download link is emailed (typically a Google Drive link)
- Alternative domain wenet.org.cn/opencpop/ has expired SSL certificate (unreachable)
- No public mirrors found on Hugging Face, Zenodo, or GitHub
- No direct Google Drive file ID found in public code repositories
- DiffSinger, Amphion, and other projects that use Opencpop all redirect to the official form
- Script: `src/downloaders/opencpop_download.py` — accepts the emailed URL as `--url` argument
- **Status: BLOCKED** — requires manual form submission and email-based link delivery
- **Action needed**: Submit the Google Form, receive download link, then run:
  `python src/downloaders/opencpop_download.py --url "<link_from_email>" --output-dir data/raw/opencpop`

## Inspection Results
**Status: Not yet inspected (awaiting download)**

Inspection script ready at `src/inspectors/opencpop_inspect.py`. Once data is downloaded, run:
```
python src/inspectors/opencpop_inspect.py --data-dir data/raw/opencpop --output-json data/raw/opencpop/inspection_results.json
```

### Expected Directory Structure (from Amphion documentation)
```
opencpop/
  midis/               -- MIDI files (one per song: 2001.midi, 2002.midi, ...)
  textgrids/           -- Praat TextGrid annotation files (2001.TextGrid, ...)
  wavs/                -- Full song WAV files (2001.wav, 2002.wav, ...)
  segments/
    wavs/              -- Utterance-level WAV files (2001000001.wav, ...)
    transcriptions.txt -- All utterance labels (pipe-delimited, 7 fields)
    train.txt          -- Training split labels
    test.txt           -- Test split labels
  TERMS_OF_ACCESS
  readme.md
```

### Expected Annotation Format
Pipe-delimited (`|`), 7 fields per line in transcriptions.txt / train.txt / test.txt:

| Field | Description | Example |
|-------|-------------|---------|
| 1. utterance_wav | Segment WAV filename (no extension) | 2001000001 |
| 2. text | Chinese text/lyrics | lyrics characters |
| 3. phonemes | Space-separated phoneme sequence | b a n g w o |
| 4. notes | Space-separated note names | C4 D4 E4 rest |
| 5. note_durations | Space-separated durations (seconds) | 0.3 0.2 0.5 |
| 6. phoneme_durations | Space-separated durations (seconds) | 0.1 0.2 0.1 0.1 0.2 0.2 |
| 7. slur_flags | Space-separated 0/1 flags (1 = slurred note) | 0 0 0 0 |

### Expected Phoneme Set
Mandarin pinyin-based system: consonant initials (b, p, m, f, d, t, n, l, g, k, h, j, q, x, zh, ch, sh, r, z, c, s) + vowel finals (a, e, i, o, u, v [for u-umlaut], plus compound finals: ai, ei, ao, ou, an, en, ang, eng, ong, ia, ie, iu, iao, ian, in, iang, ing, iong, ua, uo, uai, ui, uan, un, uang, ueng, ve, van, vn). Special phoneme: SP (silence/pause), AP (aspiration).

### Song Naming Convention
- Song IDs: 4-digit numbers (2001-2100 based on known file patterns)
- Segment IDs: 10-digit numbers — first 4 digits = song ID, last 6 = segment index

### Expected Scale
- 100 songs
- 3,756 utterances (segments)
- ~5.2 hours total audio
- 5 test songs, 95 training songs
- WAV format, 44,100 Hz, studio quality

## Schema Mapping

## Gap Assessment
### Coverage Strengths
- High-quality studio recordings (professional singer, controlled environment)
- Rich multi-level annotation: phoneme + note + duration + slur at utterance level
- MIDI alignment provides precise pitch ground truth
- TextGrid files enable Praat-based phonetic analysis
- Well-defined train/test split (95/5 songs)
- Active community usage (DiffSinger, Amphion, etc.)

### Coverage Gaps for Aquarius
- **Single singer**: Only one female voice — no speaker diversity, no male voices
- **Pop only**: Limited to Mandopop/C-pop — no traditional Chinese music genres
- **Western tonality**: Songs use Western diatonic system, not traditional Chinese scales
- **Vocal only**: No instrumental accompaniment in the recordings
- **Mandarin only**: No coverage of other Chinese languages/dialects
- **Contemporary only**: No historical or classical repertoire
- **SVS-focused annotations**: Phoneme/note/duration labels are designed for synthesis, not musicological analysis (no lyrics meaning, emotional labels, or structural annotations)

### Relevance to Aquarius
- Useful as reference for Mandarin singing voice characteristics
- Phoneme inventory provides standardized Mandarin phoneme set for cross-dataset alignment
- Note/pitch annotations could complement pitch contour datasets (e.g., jingju_pitch_contour)
- Limited traditional Chinese music content reduces direct relevance to core Aquarius scope
