# Chinese National Pentatonic Mode Database

## Source
- URL: https://ccmusic-database.github.io/en/database/csmtd.html
- Paper: Part of CSMTD / CCMusic ecosystem
- License: CC Attribution 4.0 (via CCMusic)
- Access method: Via CSMTD platform or HuggingFace
- Status: gated (requires HuggingFace authentication + access approval)
- Parent: CSMTD (see `csmtd.md`). Download via parent.

## Paper & Description Insights
Contains 287 recordings demonstrating the five Chinese national pentatonic modes: Gong (宫), Shang (商), Jue (角), Zhi (徵), Yu (羽). Designed for mode classification research. Part of the CCMusic paper's core datasets.

Important for understanding the Chinese pentatonic tonal system — a fundamental concept in traditional Chinese music theory that differs from Western major/minor modes.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings
- Region: Han Chinese musical tradition
- Genre/form: Mode demonstration / classification examples
- Instrumentation: Not specified (likely keyboard/synthesized demonstrations)
- Musical system: Chinese pentatonic modes — explicitly labeled with all 5 modes (gong/shang/jue/zhi/yu)
- Modalities: Audio recordings
- Labels: pentatonic mode (5 classes), Chinese+English names
- Key feature: Explicit pentatonic mode labeling (rare across datasets)

## Download Log
- 2026-09-15: Download attempted via `load_dataset("ccmusic-database/CNPM")`. Failed: dataset is gated, requires HuggingFace authentication and access approval. No HF_TOKEN configured.
- HF repo: `ccmusic-database/CNPM` (exists but access-restricted)
- To download: set HF_TOKEN env var, request access at https://huggingface.co/datasets/ccmusic-database/CNPM, then re-run `python src/downloaders/hf_batch_download.py cnpm`

## Inspection Results

## Schema Mapping

## Gap Assessment
