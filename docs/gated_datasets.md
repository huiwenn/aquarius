# Gated / Blocked Datasets

Datasets that could not be automatically downloaded. Download these manually and place in `data/raw/<dataset_name>/`, then re-run `src/unify.py` and `src/gap_analysis.py`.

---

## Requires Application / Login

### ~~1. CNPM~~ — RESOLVED (downloaded 2026-09-15, 287 items with mode labels)

### 2. Opencpop
- **URL**: https://wenet.org.cn/opencpop/download/
- **How to access**: Fill out Google Form, download link sent via email
- **Save to**: `data/raw/opencpop/`
- **Why it matters**: 100 Mandarin pop songs with phoneme-level alignment, 5.2 hours audio

### 3. BOPP (Beijing Opera Percussion Patterns)
- **URL**: https://zenodo.org/records/1285593
- **How to access**: Log in to Zenodo, request access to restricted files
- **Save to**: `data/raw/bopp/`
- **Why it matters**: Percussion pattern annotations for Beijing Opera
- requested

CCMUSIC
cannot be published 
requested
### 4. XFID (Chinese Folk Instrument Dataset)
- **URL**: https://ccmusic-database.github.io/en/database/csmtd.html
- **How to access**: Email ccmusic.database@hotmail.com to request access
- **Save to**: `data/raw/xfid/`
- **Why it matters**: 219 Chinese folk instrument classes

### 5. GuzhengMidiWav
- **URL**: https://ccmusic-database.github.io/en/database/csmtd.html
- **How to access**: Email ccmusic.database@hotmail.com to request access
- **Save to**: `data/raw/guzheng_midi_wav/`
- **Why it matters**: Paired MIDI + WAV guzheng recordings

### 6. Jingju Music Corpus (Dunya)
- **URL**: https://dunya.compmusic.upf.edu/developers/
- **How to access**: Register for Dunya developer API access
- **Save to**: `data/raw/jingju_music_corpus/`
- **Why it matters**: Large Beijing Opera corpus with audio and metadata

### 7. KiSing
- **URL**: http://shijt.site/index.php/2021/05/16/kising-the-first-open-source-mandarin-singing-voice-synthesis-corpus/
- **How to access**: Download from website (check availability)
- **Save to**: `data/raw/kising/`
- **Why it matters**: Mandarin singing voice synthesis corpus
- Don't need it 

## Requires Further Investigation

### 8. Chinese Songs MIDI
- **URL**: https://github.com/wyhlovecpp/Chinese-Songs-Midi-Dataset
- **How to access**: GitHub repo — may have been removed or made private
- **Save to**: `data/raw/chinese_songs_midi/`
- contacted

### 9. MADVSD
- **URL**: https://github.com/CarlWangChina/MADVSD
- **How to access**: Currently unavailable due to privacy concerns
- **Save to**: `data/raw/madvsd/`

### 10. Chinese Music Archive
- **URL**: https://chinesemusics.com/en_us/
- **How to access**: Browsing website, not a downloadable dataset — may need scraping or API
- **Save to**: `data/raw/chinese_music_archive/`

### 11. CODS
- **URL**: https://www.sciopen.com/article/10.12141/j.issn.1000-565X.250134
- **How to access**: Check paper for download instructions
- **Save to**: `data/raw/cods/`

### 12. SongSong (OpenSongSong)
- **URL**: https://zcli-charlie.github.io/projects/songsong/
- **How to access**: Not publicly released. Contact authors at Wuhan University (Zuchao Li et al.)
- **Save to**: `data/raw/songsong/`
- **Note**: Only 5 demo WAV files available on project page (model outputs, not training data). Full dataset: 29.9 hours of ancient Chinese SongCi music with phoneme/pitch/lyrics-melody annotations

### 13. Chinese Chorales (9 samples downloaded — full dataset requires author request)
- **URL**: https://github.com/123654ad/Chinese-Chorales-Dataset
- **How to access**: 9 sample MXL files on GitHub. Full 125-song dataset: email pyj17550350072@163.com
- **Save to**: `data/raw/chinese_chorales/`
- **Note**: 125 Chinese choral songs in MusicXML (SATB), 441 segments. GitHub has only 9 sample segments from 3 songs
-  asked! 

---

┌─────────────────────────┬────────────────────────────────────────────────────────┐
│         Dataset         │                        Contact                         │
├─────────────────────────┼────────────────────────────────────────────────────────┤
│ XFID & GuzhengMidiWav   │ ccmusic.database@hotmail.com                           │
├─────────────────────────┼────────────────────────────────────────────────────────┤
│ Chinese Chorales (full) │ pyj17550350072@163.com                                 │
├─────────────────────────┼────────────────────────────────────────────────────────┤
│ Opencpop                │ Fill Google Form at wenet.org.cn/opencpop/download/    │
├─────────────────────────┼────────────────────────────────────────────────────────┤
│ BOPP                    │ Request via Zenodo login at zenodo.org/records/1285593 │
├─────────────────────────┼────────────────────────────────────────────────────────┤
│ Jingju (Dunya)          │ Register at dunya.compmusic.upf.edu/developers/        │
├─────────────────────────┼────────────────────────────────────────────────────────┤
│ KiSing                  │ Check website availability first                       │
└─────────────────────────┴────────────────────────────────────────────────────────┘

Project summary: We are compiling and unifying metadata, audio, symbolic, and annotation data from publicly available Chinese music datasets — spanning traditional instruments, folk music, Beijing Opera, singing voice, and contemporary pop — into a single, standardized resource for the MIR community. Our goal is to create a comprehensive, gap-analyzed dataset that makes Chinese music more accessible for computational musicology and MIR research.

We have currently integrated 16 datasets covering 46,000+ items, and [Dataset Name] would be a valuable addition because [customize per dataset]:

## After Downloading

1. Place data in the corresponding `data/raw/<dataset_name>/` directory
2. Run `conda activate py312`
3. Run `python src/unify.py` — add a loader for any new dataset first
4. Run `python src/gap_analysis.py` to regenerate reports and figures
