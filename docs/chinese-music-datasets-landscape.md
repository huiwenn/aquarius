# Landscape Survey: Existing Chinese Music Datasets for MIR / Musicology Research

*Compiled 2026-09-17 to support a TISMIR dataset paper on Chinese music data. Sources are web searches conducted September 2026; access details and licenses should be re-verified before publication, as hosting can change.*

**Key predecessor to cite:** Zhou et al., "CCMusic: An Open and Diverse Database for Chinese Music Information Retrieval Research," *Transactions of the ISMIR* 8(1), 2025 — itself a TISMIR dataset article that aggregates six Chinese-music datasets with unified evaluation. Positioning a new dataset paper relative to CCMusic is essential.

---

## 1. Aggregator platforms

### CCMusic Database (Zhou et al., 2025)
- **Description:** The most comprehensive open aggregation of Chinese-music MIR datasets, published as a TISMIR dataset article.
- **Size/scope:** Six datasets: four instrument-focused (CTIS, GZ IsoTech, Guzheng Tech99, Erhu Playing Technique), one on Chinese pentatonic modes, one on Bel Canto vs. Chinese folk singing. Unified data structures, cleaning, label refinement, and benchmark evaluations.
- **Repertoire:** Chinese traditional instruments, pentatonic modes, Chinese/Western vocal styles.
- **Access/license:** Open; hosted on HuggingFace and ModelScope (also mirrored for China access). No manual application required.
- **URL:** https://ccmusic-database.github.io/en/database/ccm.html · Paper: https://transactions.ismir.net/articles/194/files/67e15b5aa6352.pdf

### CCMusic Dataset / Music Data Sharing Platform (Zenodo, v1.1, 2021)
- **Description:** Earlier large-scale sharing platform from the China Conservatory of Music for computational musicology.
- **Size/scope:** Three databases: Chinese Traditional Instrument Sound Database (CTIS), Midi-wav Bi-directional Database of Pop Music, and a multi-functional MIR database.
- **Repertoire:** Chinese traditional instruments; Chinese pop music (audio + MIDI).
- **Access/license:** Free for computational musicology researchers; "Dataset Open" on Zenodo.
- **URL:** https://zenodo.org/records/5676893

---

## 2. Traditional instrument audio (recordings & recognition)

### CTIS — Chinese Traditional Instrument Sound Database (Liang et al., 2019; integrated into CCMusic)
- **Description:** Reference sound database of Chinese traditional instruments, built over many years by Prof. Baoqiang Han's team.
- **Size/scope:** 287 instrument varieties originally (209 retained after CCMusic cleaning → 219 labels incl. variants); 4,956 clips, 32.63 hours, 44.1 kHz.
- **Repertoire:** Traditional, reformed, and ethnic-minority instruments across bowed, plucked, wind, and percussion families.
- **Access/license:** Open via Zenodo and via CCMusic (HuggingFace/ModelScope); recorded by conservatory professionals, no commercial copyright issues claimed.
- **URL:** https://zenodo.org/records/5676893

### ChMusic (Gong et al., 2021)
- **Description:** Benchmark dataset for traditional Chinese instrument recognition.
- **Size/scope:** 55 excerpts (11 instruments × 5 pieces), 25–280 s each, stereo WAV at 44.1 kHz.
- **Repertoire:** Erhu, pipa, sanxian, dizi, suona, zhuiqin, zhongruan, liuqin, guzheng, yangqin, sheng.
- **Access/license:** Download via Baidu Wangpan or Google Drive (links in paper); verify current availability.
- **URL:** https://arxiv.org/pdf/2108.08470

### Polyphonic Chinese instrument dataset (PLOS ONE, 2026)
- **Description:** High-caliber real-world polyphonic recordings with role-sensitive labels (lead / accompaniment / ornamental) for instrument recognition and source separation.
- **Size/scope:** 1,612 segments, 10–60 s each.
- **Repertoire:** Guzheng, pipa, xiao, dizi in varied ensemble configurations.
- **Access/license:** See paper for availability; verify before use.
- **URL:** https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0327442&type=printable

### Virtual-instrument multi-track dataset (Eurasip J. Audio, Speech & Music Proc., 2025)
- **Description:** Multi-track source-separation dataset built from high-quality sample-based virtual instruments (Kong Audio, Ample Sound), MIDI-programmed in DAWs.
- **Size/scope:** Multi-track stems (solo + accompaniment tracks); exact count in paper.
- **Repertoire:** Guzheng, dizi, pipa, xiao across Chinese-style lyricism, rock, electronic, epic, ambient genres.
- **Access/license:** See paper; verify before use.
- **URL:** https://link.springer.com/article/10.1186/s13636-025-00423-4

---

## 3. Playing-technique datasets (instrument-specific, fine-grained)

### Guzheng Tech99 (Li et al., 2023; in CCMusic)
- **Description:** Frame/note-level playing-technique detection dataset; the most richly annotated guzheng corpus.
- **Size/scope:** 99 solo guzheng compositions recorded by professionals in studio; 63,352 note-level labels (onset, offset, pitch, technique); 7 technique classes (vibrato, plucks, upward/downward portamento, glissando, tremolo, point note).
- **Repertoire:** Solo guzheng.
- **Access/license:** Open via CCMusic (HuggingFace/ModelScope).
- **URL:** https://ccmusic-database.github.io/en/database/ccm.html

### GZ IsoTech (Li et al., 2022; in CCMusic)
- **Description:** Clip-level guzheng playing-technique classification dataset.
- **Size/scope:** 2,824 clips, ~64 min total, 8 technique classes (vibrato, upward/downward/returning portamento, glissando, tremolo, harmonic, plucks); mix of virtual sound banks and real recordings.
- **Repertoire:** Solo guzheng techniques.
- **Access/license:** Open via CCMusic.
- **URL:** https://ccmusic-database.github.io/en/database/ccm.html

### ErhuPT — Erhu Playing Technique Dataset (Wang et al., 2019/2020)
- **Description:** Fine-grained taxonomy of erhu bowing and left-hand techniques recorded by multiple professional players.
- **Size/scope:** ~1,500 clips (221.8 MB), 11 top-level technique categories (détaché, diangong, harmonics, legato/slide/glissando, percussive effects, pizzicato, ricochet, staccato, tremolo, trill, vibrato) with subcategories.
- **Repertoire:** Erhu solo techniques.
- **Access/license:** Open on Zenodo.
- **URL:** https://zenodo.org/records/4320991 · Paper: http://arxiv.org/pdf/1910.09021

### CCOM-HuQin (Zhang et al., 2023)
- **Description:** Annotated *multimodal* (audio + multi-camera video) dataset of the huqin fiddle family; the richest resource for Chinese bowed strings.
- **Size/scope:** 12,000+ single playing-technique clips and 57 annotated classical excerpts with scores, note-level onset/technique annotations, and frame-level pitch tracks validated by professionals.
- **Repertoire:** Erhu, gaohu, zhonghu, banhu family, zhuihu.
- **Access/license:** CC BY-NC-SA 4.0; open on Zenodo (full v2; v1.1 subset also open).
- **URL:** https://zenodo.org/records/11387046

### GQ39 (Huang et al., 2020)
- **Description:** Guqin performance dataset with event-by-event annotations.
- **Size/scope:** 39 prevalent solo guqin compositions with note-level annotations.
- **Repertoire:** Solo guqin.
- **Access/license:** Listed in CCMusic's Table 1 as publicly available; verify current hosting.
- **URL:** See CCMusic paper Table 1: https://transactions.ismir.net/articles/194/files/67e15b5aa6352.pdf

### CBFdataset (Wang et al., 2022)
- **Description:** Monophonic recordings of classic Chinese bamboo-flute pieces plus isolated playing techniques, with annotations.
- **Size/scope:** Not quantified in surveyed sources; verify in paper.
- **Repertoire:** Dizi (Chinese bamboo flute).
- **Access/license:** Listed as publicly available in CCMusic Table 1; verify hosting.
- **URL:** See CCMusic paper Table 1: https://transactions.ismir.net/articles/194/files/67e15b5aa6352.pdf

### PipaSet (Wang et al.)
- **Description:** The first *multimodal* dataset for automatic pipa transcription: audio recordings, notated scores, and multi-camera video, with pitch, onset/duration, and playing-technique annotations.
- **Size/scope:** Not quantified in surveyed sources; verify in paper.
- **Repertoire:** Solo pipa.
- **Access/license:** Verify hosting before use.
- **URL:** Cited in recent literature (e.g., PLOS ONE 2026 lead-instrument paper above); locate canonical release via the original publication.

---

## 4. Chinese opera

### CompMusic Jingju (Beijing Opera) Corpus (Caro Repetto & Serra, 2014)
- **Description:** Foundational research corpus for computational analysis of jingju, from the CompMusic project.
- **Size/scope:** 78 releases / 113 CDs of single-aria tracks (+ 19 accompaniment-only CDs); 74 singers across 7 role types; audio + editorial metadata + lyrics + scores.
- **Repertoire:** Jingju (Beijing/Peking opera) arias.
- **Access/license:** Research corpus via MTG-UPF; see publication for access.
- **URL:** http://mtg.upf.edu/system/files/publications/Caroetal-ISMIR2014_0.pdf

### Jingju A Cappella Singing Dataset (Gong et al., 2017)
- **Description:** A cappella jingju singing dataset built for automatic singing evaluation and synthesis research; widely reused (DurIAN, OperaSinger, VITS-based works).
- **Size/scope:** 120 arias, 1,265 melodic lines, professional + amateur singers; 71 arias (1.71 h) with phoneme annotations in a 38-phoneme X-SAMPA set; note transcriptions via pYIN + jingju music-language model.
- **Repertoire:** Jingju solo singing.
- **Access/license:** Openly available online per the authors; verify current hosting.
- **URL:** https://arxiv.org/abs/1708.03986v1

### KunquDB (Zhou et al., 2024)
- **Description:** Large-scale well-annotated *audio-visual* dataset for Chinese opera, built for speaker verification and role-centric acoustic studies.
- **Size/scope:** 339 speakers, 128 hours; structured by dialogue lines with character/speaker names, gender, vocal-manner labels (stage speech vs. singing), and preliminary text transcriptions. Source: *Kunqu Opera Art Canon*.
- **Repertoire:** Kunqu opera.
- **Access/license:** See project page for access terms.
- **URL:** https://arxiv.org/abs/2403.13356v2 · Project: https://hualizhou167.github.io/KunquDB

### Traditional Chinese Opera dataset (Zhang et al., 2021)
- **Description:** Genre-recognition dataset spanning the most popular opera types, with music/song/speech annotations.
- **Size/scope:** Songs from the 14 most popular types of Chinese opera; exact counts in paper.
- **Repertoire:** Multi-regional Chinese opera (beyond jingju).
- **Access/license:** Listed as publicly available in CCMusic Table 1; verify hosting.
- **URL:** See CCMusic paper Table 1: https://transactions.ismir.net/articles/194/files/67e15b5aa6352.pdf

---

## 5. Chinese pop music

### MIR-1K (Hsu & Jang, 2010)
- **Description:** Classic benchmark for singing-voice separation.
- **Size/scope:** 1,000 clips (4–13 s each, 133 min total) from 110 karaoke songs; stereo with voice and accompaniment on separate channels; manual pitch contours, unvoiced-frame labels, lyrics, vocal/non-vocal segments; sung by 19 amateur singers.
- **Repertoire:** Chinese pop songs.
- **Access/license:** Zenodo record marked "Restricted"; also mirrored on Kaggle and mirlab.org — verify terms before use.
- **URL:** https://zenodo.org/records/3532216 · http://mirlab.org/dataset/public/

### MIR-ST500 (Wang & Jang, 2021)
- **Description:** Largest manually annotated singing-transcription dataset; benchmark for vocal melody transcription.
- **Size/scope:** 500 Chinese pop songs (~30 h), 400 train / 100 test; note-level vocal-melody annotations.
- **Repertoire:** Chinese pop songs.
- **Access/license:** Annotations + YouTube URLs on GitHub with a download script (yt-dlp) — audio is YouTube-sourced, so availability and copyright status are fragile; verify.
- **URL:** https://github.com/york135/singing_transcription_icassp2021/blob/HEAD/Readme.md

### POP909 (Wang et al., 2020)
- **Description:** Symbolic pop-song dataset for arrangement generation.
- **Size/scope:** 909 songs in MIDI: vocal melody, lead-instrument melody, and piano arrangement per song; community chord-label extensions exist.
- **Repertoire:** Chinese pop songs.
- **Access/license:** Open for research; verify hosting.
- **URL:** Original ISMIR 2020 paper; chord-labeled fork: https://github.com/andyweasley2004/pop909-cl-dataset

### JinYue Database (Shen et al., 2020)
- **Description:** One of the few Chinese-music emotion datasets: huqin music with emotion, scene, and imagery annotations.
- **Size/scope:** Metadata + audio features + annotations; exact counts in paper.
- **Repertoire:** Huqin music.
- **Access/license:** Listed as publicly available in CCMusic Table 1; verify hosting.
- **URL:** See CCMusic paper Table 1: https://transactions.ismir.net/articles/194/files/67e15b5aa6352.pdf

---

## 6. Symbolic corpora (MIDI / MusicXML / notation)

### Guqin Symbolic Dataset (lukewys)
- **Description:** Symbolic guqin music transcribed from jianpu/numbered-notation collections into MusicXML.
- **Size/scope:** 71 pieces, per-phrase and per-piece MusicXML files + metadata CSV (tuning, source, performer).
- **Repertoire:** Guqin.
- **Access/license:** Open on GitHub.
- **URL:** https://github.com/lukewys/Guqin-Dataset

### Small Tunes Dataset (arXiv 2410.08626, 2024)
- **Description:** Large MIDI collection of "Xiaodiao" (small tunes), a traditional Chinese folk-song category, built for melody generation research.
- **Size/scope:** 10,088 MIDI files.
- **Repertoire:** Traditional Chinese folk songs (Xiaodiao).
- **Access/license:** See paper for release status; verify.
- **URL:** https://arxiv.org/abs/2410.08626v2

### Anthology of Chinese Folk Songs — digitized dataset (arXiv 2512.14758)
- **Description:** OMR-extracted digital dataset from *The Anthology of Chinese Folk Songs* (30,000+ songs, 31 volumes, published 1980s–90s), converted from printed jianpu to MusicXML/MIDI with lyrics.
- **Size/scope:** Melody-only version: 5,000+ songs / 300,000+ notes (8 volumes); curated subset: 1,400+ songs / 100,000+ notes with melody + lyrics + metadata (Jiangsu I & II).
- **Repertoire:** Chinese folk songs across regions.
- **Access/license:** See paper for release status; verify.
- **URL:** http://arxiv.org/pdf/2512.14758

### XMIDI (XMusic project, 2025)
- **Description:** Large-scale symbolic dataset with emotion and genre labels for controllable generation. General-purpose rather than Chinese-specific, but produced by Chinese researchers and potentially includes Chinese genres.
- **Size/scope:** 108,023 MIDI files, ~5,278 hours.
- **Repertoire:** Multi-genre (verify Chinese coverage).
- **Access/license:** Download via Google Drive per repo; verify terms.
- **URL:** https://github.com/xmusic-project/XMIDI_Dataset

---

## 7. Gaps in the landscape (opportunities for the new dataset paper)

1. **No large-scale audio↔symbolic aligned corpus for traditional Chinese music.** There is no MAESTRO/MusicNet equivalent: aligned performance audio + notation at scale does not exist for any Chinese tradition.
2. **Jianpu (numbered notation) is under-digitized.** Jianpu remains the dominant notation in everyday Chinese music publishing, yet almost no dataset is built natively from it (the MSMP/Jianpu-OMR line of work explicitly flags this).
3. **Ethnic-minority and regional repertoires are thin.** Existing folk coverage skews Han; Tibetan, Uyghur, Mongolian, Zhuang, Miao and other traditions are barely represented in open MIR data.
4. **Opera beyond Jingju and Kunqu is sparse.** Yue opera, Huangmei opera, Cantonese opera and other regional forms have little to no public dataset presence.
5. **Multimodal datasets are rare.** PipaSet, CCOM-HuQin, and KunquDB are exceptions; audio+video+score resources are otherwise absent.
6. **Affect/emotion annotation is scarce.** JinYue is one of very few Chinese-music emotion datasets.
7. **Pop audio is often YouTube-sourced.** MIR-ST500-style reliance on YouTube downloads creates copyright fragility and reproducibility risk — a cleanly licensed pop corpus would be valuable.
8. **No standardized loaders.** Unlike mirdata for Western MIR datasets, there is no community-standard loading/validation layer for Chinese datasets; CCMusic's HuggingFace integration is a partial step.
9. **Ensemble and multi-track recordings are scarce.** Most corpora are solo or virtual-instrument renders; real-world ensemble recordings with stems are missing.
10. **Singing datasets for traditional vocal styles are thin.** Beyond jingju a cappella and KunquDB, annotated singing across folk and regional opera styles is largely absent.

*Suggested positioning for the TISMIR paper: pick one gap the new dataset fills (e.g., a jianpu-native symbolic corpus, an ethnic-minority audio collection, or an audio↔symbolic aligned set), benchmark against CCMusic's unified evaluation where overlap exists, and follow the TISMIR dataset-article format (cf. CCMusic 2025; CCOM-HuQin, TISMIR 2023).*
