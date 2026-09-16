# Jingju A Cappella Singing Pitch Contour Dataset

## Source
- URL: https://zenodo.org/record/832736
- Paper: CompMusic project, UPF Barcelona
- License: Check Zenodo
- Access method: Zenodo download
- Status: downloaded + inspected

## Paper & Description Insights
Ground truth dataset for melodic transcription and pitch contour segmentation in 39 recordings of Beijing Opera a cappella singing. Designed for evaluating pitch tracking and melodic analysis algorithms on jingju vocal music.

## Content & Taxonomy Analysis
- Time period: Traditional Beijing Opera
- Region: Beijing / northern China
- Genre/form: Jingju a cappella singing
- Instrumentation: Vocal only
- Musical system: Traditional jingju melodic system
- Language: Mandarin Chinese
- Modalities: Audio (39 recordings), pitch contour annotations
- Labels: pitch contour ground truth, melodic transcription annotations
- Related: See `jingju_singing_audio.md`, `jingju_phoneme_annotation.md`

## Download Log
- Date: 2026-09-15
- Size: 59 MB
- Method: Zenodo download (record 832736), extracted as SMC2016-master/

## Inspection Results
Inspected 2026-09-15 via `src/inspectors/jingju_pitch_contour_inspect.py`.

### Ground Truth Annotations (dataset/groundtruth/)
- 41 unique recordings, each with up to 6 annotation types (245 CSV files total):
  - **pitchtrack**: frame-level pitch values (time, frequency in Hz), 41 files
  - **melodicTrans**: note-level melodic transcription (onset, pitch, duration, ornament flag), 40 files (male_12_pos_1 missing)
  - **monoNoteOut**: monophonic note output from pYIN (onset, duration, pitch), 41 files
  - **monoNoteOut_midi**: same as above, MIDI pitch values, 41 files
  - **coarseSeg**: coarse segmentation boundaries (timestamp, label), 41 files
  - **refinedSeg**: refined segmentation boundaries (timestamp, class label, duration), 41 files

### Recording Sources
- bcnRecording: 6 recordings (Barcelona)
- londonRecording_Dan: 4 recordings (London, dan role)
- londonRecording_Laosheng: 4 recordings (London, laosheng role)
- fem (female/dan): 11 recordings
- male (laosheng): 16 recordings

### MusicXML Scores (dataset/scores/)
- 62 MusicXML (.xml) score files for jingju arias
- Plus 1 Excel catalog: "0. Score corpus.xlsx"
- Score names encode role-type and shengqiang: daxp, daeh, lsxp, lseh, jieh, jixp, lsdaxp

### Code
- `code/pyin_noteTransition/`: modified pYIN algorithm with jingju bigram note transition probabilities (C++ VAMP plugin)
- `code/melodic_transcription/`: Python evaluation scripts for melodic transcription
- `code/pitch_contour_segmentation/`: Python code for pitch contour segmentation + trained KNN model

## Schema Mapping

| Jingju Pitch Contour field | Unified schema field | Notes |
|---|---|---|
| Recording ID (e.g. "fem_01_pos_1") | `original_id` | Extracted from groundtruth CSV filenames |
| Recording prefix (fem/londonRecording_Dan) | `role_type` | dan for fem/Dan, laosheng for male/Laosheng |
| Score corpus "File name" | `original_id` (prefixed "score_") | For MusicXML score entries |
| Score corpus "Work" | `title` | Aria title in Chinese |
| Score corpus "Role type" | `role_type` | dan/laosheng/jing/xiaosheng/laodan |
| Score corpus "Shengqiang" | `shengqiang` | erhuang/xipi |
| Groundtruth CSVs | pitch contour annotations | pitchtrack, melodicTrans, segmentation |
| (dataset-level, groundtruth) | `has_audio` = false | Audio not included |
| (dataset-level, scores) | `has_musicxml` = true | 62 MusicXML scores |
| (dataset-level) | `genre` = "Beijing Opera" | |

## Gap Assessment
- No audio included (must contact authors: rong.gong@upf.edu) -- annotations only
- 41 recordings is moderate; covers both dan and laosheng roles
- Rich multi-level pitch annotations: frame-level pitch, note-level transcription, segmentation
- 62 MusicXML scores provide symbolic ground truth for the jingju melodic system
- Complements the singing audio dataset (boundary annotations) with pitch/melodic annotations
- Valuable for pitch tracking evaluation, melodic transcription, and singing training applications
