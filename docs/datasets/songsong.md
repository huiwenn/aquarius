# SongSong / OpenSongSong

## Source
- URL: https://ojs.aaai.org/index.php/AAAI/article/view/34820
- Paper: "SongSong: A Time Phonograph for Chinese SongCi Music from Thousand of Years Away" (AAAI 2025) — https://arxiv.org/abs/2602.24071
- Project page: https://zcli-charlie.github.io/projects/songsong/ (demo samples only)
- GitHub Pages source: https://github.com/zcli-charlie/zcli-charlie.github.io/tree/main/projects/songsong
- Authors: Jiliang Hu, Jiajia Li, Ziyi Pan, Chong Chen, Zuchao Li, Ping Wang, Lefei Zhang (Wuhan University; Shenyang Conservatory of Music)
- DOI: https://doi.org/10.1609/aaai.v39i25.34820
- License: Not specified (no public release found)
- Access method: NOT publicly available — full OpenSongSong dataset (29.9 hours) has not been released; only 5 demo audio samples on the project page
- Status: not_available (demo samples only)

## Paper & Description Insights
SongSong is a music generation model for restoring ancient Chinese SongCi (宋词) music. OpenSongSong is the dataset created to train this model — a comprehensive collection of ancient Chinese SongCi music.

OpenSongSong contains 29.9 hours of compositions by various renowned SongCi music masters. Features diverse annotations covering all Chinese phonemes, wide pitch distribution. Suitable for singing voice generation, accompaniment generation, and lyrics-melody alignment.

This is unique in the Chinese MIR landscape — the only dataset focused specifically on ancient Chinese SongCi music, bridging historical musicology with modern generation techniques. SongCi refers to a classical Chinese poetic form from the Song Dynasty (960–1279) that was originally sung.

## Content & Taxonomy Analysis
- Time period: Ancient Chinese — Song Dynasty (宋朝, 960–1279) SongCi tradition, though recordings are modern interpretations
- Region: Pan-China (Song Dynasty court and literati tradition)
- Genre/form: SongCi (宋词) — classical Chinese art song based on ci poetry
- Instrumentation: Vocal + accompaniment
- Musical system: Traditional Chinese (reconstructed ancient modes)
- Language: Classical Chinese (文言文)
- Modalities: Audio (29.9 hours), lyrics, melody annotations, accompaniment
- Labels: phoneme annotations, pitch, lyrics-melody alignment
- Notable: Only dataset for ancient SongCi music. 29.9 hours. Historically significant content.

## Download Log
- Date: 2026-09-15
- Method: curl from GitHub raw content (zcli-charlie.github.io project page resources)
- What was downloaded: 5 demo WAV audio samples + 1 framework diagram (JPG) from the project page
- Total size: 90 MB
- Location: data/raw/songsong/
- Note: The full OpenSongSong dataset (29.9 hours, with phoneme annotations, pitch, lyrics-melody alignment) is NOT publicly released. The paper PDF, arXiv page, AAAI proceedings page, and project website contain no download link, no GitHub repository for code or data, and no Hugging Face/Zenodo/Google Drive hosting. The only URL in the paper is the project page (https://zcli-charlie.github.io/songsong/, which 404s; the working URL is under /projects/songsong/). Searched: GitHub (zcli-charlie repos, general search), Hugging Face datasets, Zenodo, Papers With Code. None host the dataset. Contacting the authors at Wuhan University would be needed to obtain the full dataset.

## Inspection Results
### Downloaded files (demo samples only, NOT the full dataset)
- 5 WAV audio files (generated SongCi music demos), 1 JPG (model architecture diagram)
- Total: 6 files, 90 MB

### Audio file details
| File | Format | Channels | Sample Rate | Bit Depth | Duration |
|------|--------|----------|-------------|-----------|----------|
| 徵招.wav | PCM | 2 (stereo) | 44100 Hz | 16-bit | 85.0s |
| 惜红衣.wav | IEEE Float | 2 (stereo) | 32000 Hz | 32-bit | 91.8s |
| 水调歌头.wav | IEEE Float | 2 (stereo) | 32000 Hz | 32-bit | 92.9s |
| 翠楼吟.wav | PCM | 2 (stereo) | 44100 Hz | 16-bit | 84.0s |
| 鬲溪梅令.wav | PCM | 2 (stereo) | 44100 Hz | 16-bit | 95.9s |

- Total audio duration: ~7.5 minutes (449.6 seconds)
- Mixed formats: 3 files are PCM 16-bit/44.1kHz, 2 files are IEEE Float 32-bit/32kHz
- These are model output demos, not raw training data
- framework.jpg: 173 KB, model architecture diagram

### What the full OpenSongSong dataset contains (per paper, not available)
- 29.9 hours of ancient Chinese SongCi music
- Compositions by renowned SongCi music masters
- Annotations: phoneme-level, pitch (F0), lyrics-melody alignment
- Covers all Chinese phonemes with wide pitch distribution
- Suitable for: singing voice generation, accompaniment generation, lyrics-melody alignment

## Schema Mapping

## Gap Assessment
