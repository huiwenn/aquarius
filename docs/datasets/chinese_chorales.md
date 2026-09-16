# Chinese Chorales Dataset

## Source
- Paper URL: https://link.springer.com/chapter/10.1007/978-981-97-0576-4_10
- Paper: "Chinese Chorales Dataset: A High-Quality Music Dataset for Score Generation" (Yongjie Peng, Lei Zhang, Zhenyu Wang — SOMI 2023, published 2024)
- GitHub: https://github.com/123654ad/Chinese-Chorales-Dataset
- License: Not specified
- Access method: Partial sample on GitHub; full dataset requires email request to pyj17550350072@163.com
- Status: partially-available (9 of 125 songs publicly available; full dataset by email request)

## Paper & Description Insights
The Chinese Chorales Dataset is designed as a Chinese music counterpart to the JSB Chorales Dataset (commonly used for Bach-style choral composition generation). Intended for score generation research with Chinese musical characteristics.

Published at the Second Summit on Music Intelligence (SOMI 2023), proceedings published by Springer in 2024. The full dataset comprises 125 Chinese choral songs stored in MusicXML format, divided into 441 musical segments. The paper also describes a compressed .npz version containing pitch, fermata, tempo, and chord information, split into training/validation/test sets. The .npz files are NOT included in the GitHub repo.

## Content & Taxonomy Analysis
- Time period: Chinese choral music (modern arrangements of traditional melodies)
- Region: China
- Genre/form: Choral music / harmonized melodies (Chinese style)
- Instrumentation: Choral — 4 parts per score (SATB arrangement)
- Musical system: Chinese (pentatonic harmonization, contrasting with Western Bach chorales)
- Modalities: Scores/symbolic (MusicXML .mxl format; also .npz in full dataset)
- Labels: pitch, fermata, tempo, chord (in .npz version)

## Download Log
- Date: 2026-09-15
- Method: `git clone https://github.com/123654ad/Chinese-Chorales-Dataset.git`
- Downloaded to: `data/raw/chinese_chorales/`
- Size: 29 KB (9 .mxl files) — this is only a sample; full dataset = 125 songs / 441 segments
- Note: GitHub README states "Parts of the dataset are shown above, for the full dataset please contact: pyj17550350072@163.com"

## Inspection Results
- 9 .mxl files (compressed MusicXML), numbered 422-430
- Each .mxl contains one MusicXML file (.xml or .musicxml) + META-INF/container.xml
- All files have 4 parts (SATB choral arrangement)
- Song titles extracted from internal XML filenames:
  - 422-423: 追寻 (Zhuixun / "Pursuit") — 2 segments (60 + 20 measures)
  - 424-426: 闪光的记忆 (Shanguang de Jiyi / "Shining Memories") — 3 segments (60 + 60 + 16 measures)
  - 427-430: 闹红火 (Nao Honghuo / "Making Merry", a cappella, staff notation) — 4 segments (60 + 16 + 60 + 20 measures)
- Total measures across sample: 312
- File sizes range from 1.4 KB to 6.5 KB (.mxl compressed); uncompressed XML ranges 10-138 KB

## Schema Mapping

| Chinese Chorales field | Unified schema field | Notes |
|---|---|---|
| MXL filename (e.g. "422") | `original_id` | Segment number from full dataset (422–430 in sample) |
| (inferred from XML) | `title` | Not set — song titles available from inspection but not encoded in loader |
| (dataset-level) | `has_musicxml` = true | Compressed MusicXML (.mxl), 4-part SATB |
| (dataset-level) | `has_audio` = false | No audio provided |
| (dataset-level) | `has_midi` = false | No MIDI provided |
| (dataset-level) | `genre` = "choral" | Chinese choral arrangements |
| (dataset-level) | `language` = "Chinese" | |
| Key signature (fifths) | not extracted | Available in some MXL files (e.g. fifths=2 → D major, fifths=1 → G major) |
| Time signature | not extracted | Available in some MXL files (e.g. 4/4, 2/4) |

## Gap Assessment
- Only 9 of 441 segments (from 3 of 125 songs) are publicly available
- The .npz processed version (with pitch/fermata/tempo/chord labels) is not on GitHub
- To obtain the full dataset, email the corresponding author at pyj17550350072@163.com
