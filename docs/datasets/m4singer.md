# M4Singer

## Source
- URL: https://m4singer.github.io/
- Paper: "M4Singer: A Multi-Style, Multi-Singer and Musical Score Provided Mandarin Singing Corpus" (NeurIPS 2022)
- License: Custom license (see dataset_license.md in repo); free-to-use with terms
- Access method: Google Drive download via https://github.com/M4Singer/M4Singer; HuggingFace demo available
- Status: ready

## Paper & Description Insights
M4Singer is a multi-style, multi-singer Mandarin singing corpus for SVS research. Contains 700 Chinese pop songs recorded by 20 professional singers covering all four SATB voice types (soprano, alto, tenor, bass). Includes manual musical score annotations and audio-score alignment information.

Compared to Opencpop (single singer, 100 songs), M4Singer offers significantly more diversity: 20 singers across voice types, 700 songs with style variety. This makes it valuable for multi-speaker SVS and style transfer research.

## Content & Taxonomy Analysis
- Time period: Contemporary Chinese pop
- Region: Mainland China
- Genre/form: C-pop / Mandopop (multiple styles)
- Instrumentation: Vocal only (20 professional singers, SATB voice types)
- Musical system: Western diatonic (Chinese pop songs)
- Language: Mandarin Chinese
- Modalities: Audio (singing recordings), MIDI musical scores, TextGrid alignment, JSON metadata
- Labels: singer identity, voice type (SATB), phoneme sequences (pinyin initials/finals), MIDI note pitches, phoneme durations, note durations, slur markers, lyric text (Chinese characters), word-level and phoneme-level time alignment
- Notable: Multi-singer (20) with diverse voice types -- much larger than Opencpop. 137 songs shared across multiple singers enables cross-singer comparison. Rich phoneme-level annotation with 56 pinyin phonemes + 2 special tokens (<AP> aspiration pause, <SP> silence pause).

## Download Log
- Date: 2026-09-15
- Source: Google Drive via gdown (file ID: 1xC37E59EWRRFFLdG3aJkVqwtLDgtFNqW)
- Note: Initial gdown attempt failed with FileURLRetrievalError (quota/permission issue). Succeeded on retry using direct `gdown.download()` with `id=` parameter.
- Archive: m4singer_download.zip, 8.2 GB compressed
- Extracted to: data/raw/m4singer/m4singer/
- Extraction size: 10.45 GB (62,689 files)
- Archive removed after extraction
- Download script: src/downloaders/m4singer_download.py
- HuggingFace mirrors available (AKRTR/m4singer has audio only, no metadata; umoubuton/m4singer has combined zip)

## Inspection Results
- Inspection script: src/inspectors/m4singer_inspect.py

### Directory Structure
```
data/raw/m4singer/m4singer/
  meta.json                           # Global metadata (20,896 entries)
  {Singer}-{N}#{SongName}/            # 699 song directories (e.g. Alto-5#云烟成雨/)
    {NNNN}.wav                        # Audio segment (mono WAV)
    {NNNN}.TextGrid                   # Praat TextGrid (word + phoneme alignment)
    {NNNN}.mid                        # MIDI file (musical score for segment)
```

### Singer & Song Counts
- 20 singers, 699 song directories, 419 unique song titles
- 137 songs performed by multiple singers (enables cross-singer comparison)
- Voice type breakdown:
  - Soprano: 3 singers (Soprano-1 to 3), 73 songs
  - Alto: 7 singers (Alto-1 to 7), 272 songs
  - Tenor: 7 singers (Tenor-1 to 7), 212 songs
  - Bass: 3 singers (Bass-1 to 3), 142 songs

### Audio Analysis
- Total WAV segments: 20,896
- Total duration: 29.70 hours (106,904 seconds)
- Segment duration range: 0.83s -- 11.98s (avg 5.12s)
- Sample rates: 44,100 Hz (15,808 segments), 96,000 Hz (2,915), 48,000 Hz (2,173)
- Format: mono, 16-bit PCM WAV
- Per-singer duration range: 37.3 min (Soprano-2, 460 segments) to 158.0 min (Alto-5, 1,938 segments)

### Metadata (meta.json)
- Format: JSON array of 20,896 entries (one per audio segment)
- Fields per entry:
  - `item_name`: str -- segment identifier (e.g. "Alto-1#newboy#0000")
  - `phs`: list[str] -- phoneme sequence (pinyin initials/finals + special tokens)
  - `txt`: str -- Chinese character lyrics for the segment
  - `is_slur`: list[int] -- slur flag per phoneme (0=normal, 1=slur); 39,699 slurred / 407,031 normal
  - `ph_dur`: list[float] -- phoneme durations in seconds
  - `notes`: list[int] -- MIDI note numbers per phoneme (0=rest)
  - `notes_dur`: list[float] -- note durations in seconds per phoneme
- Phoneme inventory: 56 regular phonemes (pinyin initials: b,c,ch,d,f,g,h,j,k,l,m,n,p,q,r,s,sh,t,x,z,zh; pinyin finals: a,ai,an,ang,ao,e,ei,en,eng,er,i,ia,ian,iang,iao,ie,in,ing,iong,iou,o,ong,ou,u,ua,uai,uan,uang,uei,uen,uo,v,van,ve,vn) + 2 special tokens (<AP>=aspiration pause, <SP>=silence pause)
- MIDI pitch range: 35--78 (excluding rests at 0); corresponds approximately to B1--F#5

### TextGrid Annotations
- Format: Praat TextGrid, 2 tiers per file
  - Tier 1: word-level alignment (Chinese characters + <SP>/<AP> tokens with xmin/xmax timestamps)
  - Tier 2: phoneme-level alignment (pinyin initials/finals with xmin/xmax timestamps)

### MIDI Files
- 20,896 MIDI files (one per audio segment)
- File sizes: 71--247 bytes (small; contain single-voice melodic line)

## Schema Mapping
| M4Singer field | Aquarius concept | Notes |
|---|---|---|
| Singer ID (e.g. Alto-5) | performer_id | 20 anonymous professional singers |
| Voice type prefix (Soprano/Alto/Tenor/Bass) | voice_type | SATB classification |
| Song name (Chinese) | work_title | 419 unique C-pop song titles |
| WAV audio | audio | Mono, 16-bit, mixed sample rates (44.1/48/96 kHz) |
| TextGrid tier 1 | word_alignment | Word-level timestamps |
| TextGrid tier 2 | phoneme_alignment | Phoneme-level timestamps |
| meta.json phs | phoneme_sequence | 56 pinyin phonemes + 2 special tokens |
| meta.json txt | lyrics | Chinese character lyrics per segment |
| meta.json notes | midi_pitch | MIDI note numbers, 0=rest |
| meta.json ph_dur / notes_dur | duration_annotation | Per-phoneme and per-note durations |
| meta.json is_slur | slur_annotation | Binary slur flag per phoneme |
| MIDI files | musical_score | Melodic line per segment |

## Gap Assessment
- **Sample rate inconsistency**: Three different sample rates across the dataset (44.1, 48, 96 kHz). Will need resampling to a common rate for unified analysis.
- **No explicit style labels**: Despite being described as "multi-style," the dataset has no explicit style/genre tags per song. Style must be inferred from song titles or external metadata.
- **No pitch (f0) contours**: Raw audio only; f0 extraction needed for pitch analysis.
- **No explicit tempo/BPM annotations**: MIDI files are minimal (melody only); tempo must be derived from note durations.
- **Segment-level only**: Songs are pre-segmented into phrases (avg 5.12s); full-song audio not provided. 699 songs broken into 20,896 segments.
- **Anonymous singers**: Singer identities are anonymized (Alto-1, etc.); no demographic or training background information.
- **Imbalanced voice types**: Alto and Tenor have 7 singers each; Soprano and Bass only 3 each. Per-singer duration varies 3x (37--158 min).
- **Chinese-only lyrics**: All text in Chinese characters; no romanization in lyrics field (though phoneme sequences use pinyin).
- **No explicit song-level metadata**: No song duration, key, or genre tags at the song level.
- **Strong for Aquarius**: Rich phoneme-level alignment + MIDI scores make this dataset highly valuable for singing voice analysis, pitch contour studies, and phoneme-level music-language research in Mandarin pop.
