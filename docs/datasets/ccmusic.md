# CCMusic

## Source
- URL: https://ccmusic-database.github.io/en/download.html
- Paper: "CCMusic: An Open and Diverse Database for Chinese and General Music Information Retrieval Research" (TISMIR, 2024) — https://transactions.ismir.net/articles/10.5334/tismir.194
- License: CC-BY-4.0 (but application terms add institutional restriction: "This database can only be used by the applicant and members of the applicant's department or research institution." Data cannot be publicly redistributed.)
- Access method: HuggingFace (https://huggingface.co/ccmusic-database), GitHub, Zenodo (https://doi.org/10.5281/zenodo.5676893). Full files may require application to ccmusic.database@hotmail.com; demo versions available on public platforms.
- Status: umbrella (sub-datasets handled individually)

## Paper & Description Insights
CCMusic is an umbrella platform ("Music Data Sharing Platform for Computational Musicology Research") integrating multiple Chinese music datasets with unified data structures and open accessibility. The TISMIR paper describes 6 core datasets: CTIS (4,956 instrument recordings), GZ_IsoTech (2,824 Guzheng technique clips), Guzheng_Tech99 (99 compositions with frame-level annotations), Erhu Playing Technique (1,253 clips), Chinese National Pentatonic Modes (287 recordings), and Bel Canto & Chinese Folk Singing (203 vocal recordings).

The broader CCMusic platform encompasses 4 main databases: CTIS, Multi-functional Music Database for MIR Research, Midi-wav Bi-directional Database of Pop Music, and CSMTD. Note: CSMTD has its own doc — see `csmtd.md`.

Key design decisions: unified data structure with standardized dictionaries, data cleaning and label refinement, fixed-length audio segmentation (1.6–20s depending on task), standard train/validation/test splits (8:1:1).

Known limitations: significant class imbalance (e.g., Guzheng_Tech99 plucks = 74.88% of data), limited dataset sizes, variable recording quality, no MIDI or score data in the core paper datasets, no cross-cultural comparative baselines.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings of traditional pieces
- Region: Primarily Han Chinese traditions; Xinjiang minority instruments via XFID (under CSMTD)
- Genre/form: Traditional instrumental solo, folk singing, Bel Canto comparison
- Instrumentation: Guzheng, Erhu, plus 219 instrument types in CTIS covering traditional Chinese instrument families
- Musical system: Chinese pentatonic modes (gong/shang/jue/zhi/yu) explicitly labeled
- Language: Mandarin Chinese (vocal datasets)
- Modalities: Audio (WAV, 22,050–44,100 Hz), mel/CQT/chroma spectrograms. No MIDI or scores in core datasets.
- Labels: instrument names (Chinese+pinyin+English), playing techniques, pentatonic modes, singing styles, gender

## Download Log

## Inspection Results

## Schema Mapping

## Gap Assessment
