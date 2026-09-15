# Guqin Dataset

## Source
- URL: https://github.com/lukewys/Guqin-Dataset
- Paper: CSMT2019 (Chinese paper by Wu Yusong, included in repo at `paper/CSMT2019-古琴数据集-吴雨松.pdf`)
- License: Not specified in repository (no LICENSE file, no license mentioned in README)
- Access method: GitHub clone
- Status: downloaded

## Paper & Description Insights
A symbolic music dataset containing MusicXML transcriptions of Guqin (古琴) music. The Guqin is one of the most ancient Chinese instruments — a seven-string plucked zither with over 3,000 years of history, closely associated with literati culture and Confucian philosophy.

Scores were collected from published Guqin score collections that include numbered notation (jianpu/简谱) alongside the traditional reduced notation (jianzipu/减字谱). The numbered notation was transcribed using a custom Excel-based fast-entry system and converted to MusicXML via Python (music21 v5.5.0). Content transcribed: melody and overtone (泛音/fanyin) notation only; expressive markings, fingering, and parallel voices were ignored.

The dataset was presented at CSMT2019 (Conference on Sound and Music Technology).

## Content & Taxonomy Analysis
- Time period: Traditional Chinese — sources span historical qin score collections from Ming dynasty (神奇秘谱, 1425) through Qing and modern compilations
- Region: Han Chinese literati tradition
- Genre/form: Guqin solo — qin music (琴曲)
- Instrumentation: Guqin (seven-string zither, silk/metal-nylon strings)
- Musical system: Traditional Chinese pentatonic/heptatonic modal system with distinctive Guqin tuning conventions
- Modalities: Symbolic — MusicXML 3.0 (.xml), single-part (Guqin melody)
- Labels: piece title (曲谱名称), score source collection (琴谱来源), tuning (定弦), original historical source (琴曲来源), performer (演奏者), arranger/transcriber (打谱/记谱者)

### Taxonomy details

**Tuning system (定弦)** — 13 distinct tunings across 71 pieces:
- 1=F 正调定弦 (standard tuning in F): 31 pieces (43.7%)
- 1=C 正调定弦 (standard tuning in C): 17 pieces (23.9%)
- 1=bB 紧五弦定弦 (raised 5th string in Bb): 7 pieces (9.9%)
- 1=F (F, unspecified method): 6 pieces
- 1=bB 紧二五弦定弦 (raised 2nd+5th strings): 2 pieces
- Other: 1=G variants, 1=bE, 1=C 慢三弦, 1=bB 紧五慢一, 1=G 慢一三六, 1=G 慢三六 (1 each)

**Score source collections (琴谱来源)** — 6 published score books:
- 古琴考级曲集1 (Guqin Exam Collection vol.1): 25 pieces
- 古琴考级经典作品示范 (Guqin Exam Classic Works): 19 pieces
- 古琴秘谱遗存第一卷 (Secret Scores vol.1): 9 pieces
- 古琴名师琴谱集录 (Master Scores Collection): 7 pieces
- 古琴考级曲集2 (vol.2): 6 pieces
- 古琴考级曲集3 (vol.3): 5 pieces

**Original historical sources (琴曲来源)** — 38 distinct original sources, top ones:
- 琴学入门 (Introduction to Qin Study): 8
- 梅庵琴谱 (Meian Qinpu): 8
- 自远堂琴谱 (Ziyuantang Qinpu): 5
- 神奇秘谱 (Shenqi Mipu, 1425): 5
- 天闻阁琴谱 (Tianwenge Qinpu): 3
- 风宣玄品 (Fengxuan Xuanpin): 3
- 五知斋琴谱 (Wuzhizhai Qinpu): 3
- Also includes: modern compositions (傅庚辰, 谭盾, 王立平, 杨青, 金湘)

**Notable performers**: 许光毅 (9), 管平湖 (7), 吴景略 (3), 詹澄秋 (2), 喻绍泽 (2), 刘景韶 (2)

**Notable arrangers/transcribers**: 许光毅 (9), 王迪 (9), 许健 (6), 管平湖 (4)

## Download Log
- Date: 2026-09-15
- Method: `git clone https://github.com/lukewys/Guqin-Dataset data/raw/guqin_dataset/`
- Script: `src/downloaders/guqin_dataset_download.py`
- Commit: e7feb0c (latest as of download)
- Result: Success. 487 files total, 28 MB including .git.
- Integrity: All expected directories present (Guqin_Dataset_v1/xml, xml_no_split, reference.csv)

## Inspection Results

### Directory structure
```
guqin_dataset/
  README.md
  Guqin_Dataset_v1/
    reference.csv                     # Metadata for all 71 pieces
    xml/                              # Phrase-split MusicXML (408 files)
      古琴名师琴谱集录/               # 10 files
      古琴秘谱遗存第一卷/              # 97 files
      古琴考级经典作品示范/             # 84 files
      古琴考级曲集1/                   # 111 files
      古琴考级曲集2/                   # 65 files
      古琴考级曲集3/                   # 41 files
    xml_no_split/                     # Full-piece MusicXML (71 files)
      古琴名师琴谱集录/               # 7 files
      古琴秘谱遗存第一卷/              # 9 files
      古琴考级经典作品示范/             # 19 files
      古琴考级曲集1/                   # 25 files
      古琴考级曲集2/                   # 6 files
      古琴考级曲集3/                   # 5 files
  paper/
    CSMT2019-古琴数据集-吴雨松.pdf     # Associated paper
  简谱速录/                            # Fast transcription tools
    README.md                         # Transcription method documentation
    xlsx2xml.py                       # Excel-to-MusicXML converter
    add_harmonic.py                   # Harmonic marker tool
    pics/                             # Documentation images
```

### File type summary
| Extension | Count | Description |
|-----------|-------|-------------|
| .xml      | 479   | MusicXML 3.0 score files |
| .md       | 2     | README files |
| .py       | 2     | Transcription tools |
| .png      | 2     | Documentation images |
| .pdf      | 1     | Conference paper |
| .csv      | 1     | Metadata file |

### MusicXML content analysis (71 full pieces in xml_no_split)
- **Total notes**: 39,623
- **Harmonic notes** (marked with staccato): 4,253 (10.7% of all notes)
- **Total measures**: 9,859
- **Measures per piece**: min 15, max 594, mean 138.9
- **Encoding**: MusicXML 3.0 Partwise, generated by music21 v5.5.0
- **Parts**: Single part per file (part-name: "Guqin")
- **Clef**: Bass clef (F clef, line 4)

**Time signatures** — highly varied, reflecting free-rhythm Guqin tradition:
- 2/4: 1,152 measures (most common)
- 3/4: 1,001
- 4/4: 432
- 5/4: 133
- 5/8: 91
- Also: 3/8, 1/4, 7/8, 6/4, 9/8, 7/4, and many irregular meters (17/16, 44/4, etc.)
- Note: Time signatures were auto-generated during conversion, not from original scores

**Pitch range**: A2 to G5 (approximately 3 octaves), centered around C3-E5.
- Most frequent pitches: D4, C4, E4, G4, A3 — consistent with pentatonic modality

### Phrase-split analysis (xml directory)
- 408 phrase files from 71 unique pieces
- Phrases per piece: min 1, max 19, mean 5.7
- File naming: `{piece_title}_{phrase_number}.xml`
- Phrase boundaries correspond to musical sections/paragraphs in original scores

### Metadata schema (reference.csv)
| Column | Chinese | Type | Description | Example |
|--------|---------|------|-------------|---------|
| 曲谱名称 | Piece title | string | Traditional Chinese title | 梅花三弄 |
| 琴谱来源 | Score source | string (6 values) | Published collection name | 古琴考级曲集1 |
| 定弦 | Tuning | string (13 values) | Key + tuning method | 1=F 正调定弦 |
| 琴曲来源 | Original source | string (38 values) | Historical qinpu name | 神奇秘谱 |
| 演奏者 | Performer | string | Qin player name (may be empty) | 管平湖 |
| 打谱/记谱者 | Arranger | string | Score transcriber (may be empty) | 王迪 |

## Schema Mapping
- Piece identification: 曲谱名称 (title) + 琴谱来源 (source collection)
- Tuning/mode: 定弦 encodes both key center and string-tuning method
- Provenance chain: 琴曲来源 (historical source) -> 琴谱来源 (modern collection) -> performer/arranger
- Musical content: MusicXML provides pitch, duration, time signature, overtone markers
- No tempo, dynamics, lyrics, or fingering annotations

## Gap Assessment
- **No audio**: Purely symbolic dataset — no recordings paired with scores
- **No MIDI**: Only MusicXML format (MIDI can be derived via music21 or other tools)
- **No lyrics/text**: Song texts not included even for vocal-accompanied pieces
- **No fingering**: Jianzipu fingering notation was explicitly excluded from transcription
- **No expressive markings**: Ties, slurs, dynamics stripped during conversion
- **No temporal alignment**: No performance timing or tempo markings
- **Limited metadata**: No piece dating, no mode/diao classification, no difficulty grading
- **Incomplete performer data**: 33 of 71 pieces have no performer listed
- **License unclear**: No license file or statement in repository
- **Single version**: Each piece has one arrangement — no comparison across different qinpu versions
- **Scale**: 71 pieces is modest compared to the thousands of pieces in the Guqin repertoire (e.g., Qinqu Jicheng contains ~3,000 pieces)
- **Transcription limitations**: Cannot represent parallel voices, tied notes across barlines, or multi-layer lyrics (documented in 简谱速录/README.md)
