# ACE-OpenCpop / ACE-KiSing

## Source
- URL: https://www.isca-archive.org/interspeech_2024/shi24_interspeech.pdf
- Paper: "Singing Voice Data Scaling-up: An Introduction to ACE-Opencpop and ACE-KiSing" (Interspeech 2024) — https://arxiv.org/abs/2401.17619
- License: CC-BY-NC-4.0
- Access method: ESPnet-Muskits; HuggingFace (https://huggingface.co/datasets/espnet/ace-opencpop-segments)
- Status: ready
- Derived from: Opencpop (see `opencpop.md`) and KiSing (see `kising.md`)

## Paper & Description Insights
ACE-Opencpop and ACE-KiSing are data-augmented extensions of Opencpop and KiSing, created using an existing SVS synthesizer for data augmentation with detailed manual tuning. ACE-Opencpop has vocal characteristics and styles from 30 singers, presented at song level with segmentation aligning to original Opencpop configuration.

ACE-KiSing extends KiSing with eight additional songs by Kiki Zhang, including four English songs (making it bilingual). Both serve as benchmarks for SVS and enhance performance on other datasets as supplementary training data.

Available via ESPnet-Muskits with pre-trained models and training recipes.

## Content & Taxonomy Analysis
- Time period: Contemporary
- Region: Mainland China
- Genre/form: C-pop / Mandopop (synthesized augmentation of real recordings)
- Instrumentation: Vocal only (30 singer voices in ACE-Opencpop; augmented)
- Musical system: Western diatonic
- Language: Mandarin Chinese (+ English in ACE-KiSing)
- Modalities: Audio (singing), music scores, segmentation annotations
- Labels: singer identity, segmentation, music score alignment
- Note: Synthetic augmentation — not all recordings are from real singers

## Download Log

## Inspection Results

## Schema Mapping

## Gap Assessment
