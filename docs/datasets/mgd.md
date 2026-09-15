# MGD (Large-Scale Chinese Folk Songs Dataset)

## Source
- URL: https://chinglohsiu.github.io/files/MGD.html
- Paper: Associated with Chinese folk song research (2014–2023)
- License: Not specified
- Access method: Excel spreadsheets downloadable from project page, organized by province
- Status: downloaded + inspected

## Paper & Description Insights
MGD is a comprehensive collection of 31,000+ traditional Chinese folk songs in symbolic format. Documents music representing Han people and ethnic minorities across 31 regions (provinces/autonomous regions + Taiwan). Organized by nine major folk music categories.

Nine folk song genres: work songs (haozi 号子), mountain songs (shan'ge 山歌), field songs (tian'ge 田歌), small tunes (xiao diao 小调), dance songs (wu'ge 舞歌), fisherman's songs (yu'ge 渔歌), ritual songs, children's songs, vendors' cries. Minority group categories include love songs, narrative songs, and religious songs.

Data from official collections including *Collection of Traditional Chinese Folk Music* and regional anthologies.

A curated subset, MGDplus (1,214 selected Han Chinese folk songs from 7 regions) provides five annotations per song and partial audio-score alignment.

## Content & Taxonomy Analysis
- Time period: Traditional Chinese folk music (historical through 20th century collections)
- Region: 31 Chinese provinces/regions (Hong Kong, Macao, Tibet data not yet available)
- Genre/form: Folk songs — 9 categories covering nearly all traditional folk song types
- Instrumentation: Vocal (folk songs, primarily monophonic)
- Musical system: Chinese traditional (pentatonic and regional modes)
- Language: Chinese (various dialects/minority languages implied by regional scope)
- Modalities: Symbolic (Excel spreadsheets), some audio-score alignment in MGDplus
- Labels: genre/category (9 types), region/province, ethnic group (Han + minorities)
- Notable: 31,000+ songs — one of the largest Chinese folk music collections. Exceptional geographic and genre breadth.

## Download Log
- Date: 2026-09-15
- Size: 1.2 MB (31 Excel files)
- Method: Downloaded from https://chinglohsiu.github.io/files/MGD.html

## Inspection Results
Inspected 2026-09-15 (inline analysis, no separate script needed).

### File Structure
- 31 Excel files: `分省信息-{province_abbreviation}.xlsx`
- One file per province/region

### Column Schema
All 31 files share 9 columns (29 files) or 10 columns (Yunnan and Xinjiang add "Stars"):
1. **Provinces** -- province abbreviation (Chinese)
2. **No.** -- song number within province
3. **Title** -- song title (Chinese)
4. **Sub-Title** -- subtitle or alternate title (Chinese, often null)
5. **Location** -- specific city/county of origin (Chinese)
6. **Genre** -- folk song genre category (EMPTY in current data)
7. **Keys** -- musical key (EMPTY in current data)
8. **Key_Transpose_Postion** -- transposition position (EMPTY in current data)
9. **Regular_TS** -- time signature (EMPTY in current data)
10. **Stars** -- (only Yunnan and Xinjiang; EMPTY)

### Total Songs: 31,761

### Songs per Province (top 10)
| Province | Abbr | Count |
|----------|------|-------|
| Yunnan | 云 | 2,062 |
| Xinjiang | 新 | 1,936 |
| Shanxi | 晋 | 1,402 |
| Hunan | 湘 | 1,394 |
| Jiangsu | 苏 | 1,381 |
| Fujian | 闽 | 1,381 |
| Guizhou | 贵 | 1,270 |
| Shaanxi | 陕 | 1,248 |
| Hebei | 冀 | 1,192 |
| Inner Mongolia | 蒙 | 1,176 |

### Songs per Province (remaining)
| Province | Abbr | Count |
|----------|------|-------|
| Jiangxi | 赣 | 1,170 |
| Sichuan-Chongqing | 川渝 | 1,149 |
| Guangdong | 粤 | 1,042 |
| Heilongjiang | 黑 | 1,036 |
| Hubei | 鄂 | 1,006 |
| Anhui | 皖 | 1,005 |
| Gansu | 甘 | 998 |
| Shandong | 鲁 | 992 |
| Qinghai | 青 | 924 |
| Northern Shaanxi | 陕北 | 905 |
| Hainan | 琼 | 901 |
| Henan | 豫 | 857 |
| Guangxi | 桂 | 811 |
| Liaoning | 辽 | 805 |
| Zhejiang | 浙 | 745 |
| Ningxia | 宁 | 733 |
| Jilin | 吉 | 636 |
| Shanghai | 沪 | 602 |
| Tianjin | 津 | 523 |
| Beijing | 京 | 361 |
| Taiwan | 台 | 118 |

### Annotation Status
- Genre, Keys, Key_Transpose_Position, Regular_TS columns exist but are **completely empty** across all 31 files
- Only metadata fields populated: Province, No., Title, Sub-Title, Location
- This suggests the downloaded version is the "catalog-only" release; musical annotations may come from a different source or the MGDplus subset

## Schema Mapping

## Gap Assessment
- 31,761 songs is one of the largest Chinese folk music datasets by catalog size
- Exceptional geographic coverage: 31 provinces/regions (Hong Kong, Macao, Tibet not yet available)
- Genre and key annotations are empty -- the musical content columns are placeholder-only in this release
- No audio or symbolic music files included -- this is a metadata catalog only
- Location data (city/county level) is populated and valuable for geographic analysis
- For the unified database: can contribute title, province, and location metadata; musical annotations would need to come from the MGDplus subset or other sources
- The MGDplus subset (1,214 songs, 7 regions) reportedly has richer annotations and partial audio-score alignment, but is not included in this download
