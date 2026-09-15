# Traditional Chinese Folk Music Composition Dataset (Kaggle)

## Source
- URL: https://www.kaggle.com/datasets/ziya07/traditional-chinese-folk-music-composition-dataset
- Paper: Possibly associated with MusicMamba (arXiv: 2409.02421) — FolkDB dataset
- License: CC0-1.0
- Access method: Kaggle CLI (`kaggle datasets download`)
- Status: downloaded + inspected

## Paper & Description Insights
A pre-computed audio feature dataset for traditional Chinese folk music classification. Contains MFCC features (13 coefficients × mean/std + first/second deltas = 78 features) plus metadata labels. No raw audio or MIDI included — only the feature CSV.

Associated with research on Chinese traditional music style classification and generation (MusicMamba, FolkDB).

## Content & Taxonomy Analysis
- Time period: Traditional Chinese folk music
- Region: 4 provinces — Inner Mongolia (632), Gansu (590), Ningxia (585), Jiangsu (567)
- Genre/form: Folk music — 3 style labels: Hua'er (824), Mongolian (780), Jiangnan (770)
- Instrumentation: 3 instruments — Morin Khuur (801), Voice (790), Flute (783)
- Musical system: Chinese traditional — 6 pitch keys: F, E, C, G, A, D
- Modalities: Pre-computed features only (MFCC + deltas), no raw audio
- Labels: region (4), instrument (3), tempo_bpm (int), theme_label (4: Epic/Folk tale/Celebration/Love), noise_level (3: Low/Medium/High), pitch_key (6), style_label (3)
- Notable: 2,374 samples with balanced label distributions

## Download Log
- Date: 2026-09-15
- Method: `kaggle datasets download ziya07/traditional-chinese-folk-music-composition-dataset`
- Size: 339 KB compressed, 1.1 MB unzipped
- Contents: single CSV file (`traditional_music_dataset.csv`)

## Inspection Results
- **Shape**: 2,374 rows × 86 columns
- **Columns**: file_name, region, instrument, tempo_bpm, theme_label, noise_level, pitch_key, style_label, + 78 MFCC feature columns (mfcc1-13 mean/std, delta1-13 mean/std, delta2_1-13 mean/std)
- **Label distributions** (roughly balanced):
  - region: Inner Mongolia 632, Gansu 590, Ningxia 585, Jiangsu 567
  - instrument: Morin Khuur 801, Voice 790, Flute 783
  - style_label: Hua'er 824, Mongolian 780, Jiangnan 770
  - theme_label: Epic 643, Folk tale 595, Celebration 584, Love 552
  - noise_level: Medium 848, High 772, Low 754
- **Tempo**: integer values, range TBD
- **File names**: sample_1.wav through sample_2374.wav (referenced but NOT included)

## Schema Mapping
| Kaggle column | Aquarius concept | Notes |
|---|---|---|
| region | region | 4 Chinese provinces |
| instrument | instrument | 3 traditional instruments |
| style_label | genre/style | Hua'er, Mongolian, Jiangnan |
| theme_label | theme | 4 thematic categories |
| pitch_key | key | Western key letters |
| tempo_bpm | tempo | Integer BPM |

## Gap Assessment
- **Critical: No audio or MIDI data** — only pre-computed MFCC features in a CSV. Cannot reconstruct audio or use for any task requiring raw data
- **Limited instrument coverage**: only 3 instruments (Morin Khuur, Voice, Flute) vs. 219 in CTIS
- **Limited geographic coverage**: only 4 provinces vs. 31 in MGD
- **Synthetic labels possible**: the very balanced distributions (±10%) and round numbers suggest labels may be synthetically generated or augmented
- **No provenance**: file_name references WAV files not included; unclear if original recordings exist or were synthesized
- **Low value for Aquarius**: pre-computed features without raw data cannot be integrated into a unified database; useful only as a reference for classification label schema
