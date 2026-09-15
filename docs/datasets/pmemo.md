# PMEmo

## Source
- URL: https://github.com/HuiZhangDB/PMEmo
- Paper: "The PMEmo Dataset for Music Emotion Recognition" (ACM ICMR 2018) — https://dl.acm.org/doi/10.1145/3206025.3206037
- License: Research use (check paper for specifics)
- Access method: GitHub repository
- Status: ready
- Parent: Listed under CSMTD (see `csmtd.md`)

## Paper & Description Insights
PMEmo contains 794 songs with emotion annotations from 457 subjects. Designed for music emotion recognition/retrieval benchmarking.

Data includes: song metadata (title, artists, chorus timestamps), manually selected chorus clips (MP3), pre-computed audio features, manually annotated emotion labels (static labels for whole clips AND dynamic labels per 0.5-second segment), EDA physiological signals, song lyrics, and song comments from online Chinese and English music websites.

Notable for combining audio with physiological signals (EDA) — rare in MIR datasets. The dynamic emotion labeling at 0.5s granularity enables time-varying emotion analysis. Contains Chinese popular music, making it relevant for Chinese music emotion research.

## Content & Taxonomy Analysis
- Time period: Contemporary Chinese pop
- Region: Mainland China
- Genre/form: C-pop (popular music)
- Instrumentation: Full pop arrangements (not separated)
- Musical system: Western diatonic (Chinese pop)
- Language: Chinese (lyrics and comments), English (some comments)
- Modalities: Audio (MP3 chorus clips), pre-computed audio features, EDA physiological signals, lyrics text, online comments text
- Labels: emotion (static valence-arousal + dynamic per-0.5s), song metadata (title, artist, chorus timestamps)
- Notable: 457 annotators, physiological signals, time-varying emotion labels

## Download Log

## Inspection Results

## Schema Mapping

## Gap Assessment
