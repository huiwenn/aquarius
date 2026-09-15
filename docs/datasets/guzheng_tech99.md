# Guzheng_Tech99

## Source
- URL: https://huggingface.co/datasets/ccmusic-database/Guzheng_Tech99
- Paper: Part of CCMusic (see `ccmusic.md`)
- License: CC Attribution 4.0 (via CCMusic)
- Access method: HuggingFace (`ccmusic-database/Guzheng_Tech99`), ModelScope mirror
- Status: ready
- Parent: CSMTD / CCMusic. Download via parent or directly from HuggingFace.

## Paper & Description Insights
Frame-level annotation dataset for Guzheng playing technique detection. 99 solo compositions by professional musicians in studio settings. 63,352 annotated labels total. Average duration 91.56s per composition, total ~151 minutes. Size ~2.16 GB.

Seven labeled techniques: Vibrato (chanyin 颤音), Plucks (boxian 拨弦), Upward Portamento (shanghua 上滑), Downward Portamento (xiahua 下滑), Glissando (huazhi/guazou/lianmo/liantuo), Tremolo (yaozhi 摇指), Point Note (dianyin 点音).

Each note annotated with: onset time, offset time, pitch, technique classification. Data splits: train 79 / val 10 / test 10 compositions.

Notable class imbalance: Plucks represent 74.88% of all labels.

## Content & Taxonomy Analysis
- Time period: Contemporary recordings of traditional repertoire
- Region: Han Chinese
- Genre/form: Traditional Guzheng solo
- Instrumentation: Guzheng (silk family)
- Musical system: Traditional Chinese
- Modalities: Audio (FLAC, 44,100 Hz), CSV annotations, mel spectrograms
- Labels: playing technique (7 classes), onset/offset times, pitch
- Key feature: Frame-level technique annotations with pitch — enables fine-grained temporal analysis

## Download Log

## Inspection Results

## Schema Mapping

## Gap Assessment
