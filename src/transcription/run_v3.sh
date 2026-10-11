#!/usr/bin/env bash
# Round-3 (Musical Map of China catalogue) processing, same pipeline as rounds 1-2, chained end to end:
#   wait for the download → one retry pass for failed items (transient 403s) → speech screen → separation →
#   GAME (+ trim, MusicXML, instrumental fallback) and ROSVOT → 3-run GAME ensemble → RMVPE/PESTO F0 →
#   primary selection → dataset index → release tables.
# Idempotent: every step skips existing outputs. Launch from a native arm64 shell:
#   nohup bash src/transcription/run_v3.sh > /dev/null 2>&1 &
set -u
cd "$(dirname "$0")/../.."
export AQ_MANIFEST=data/regions_v3/manifest.csv AQ_TRANS=data/regions_v3/transcription
PY=~/miniforge3/envs/sep/bin/python
PY312=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
PYCLF=~/miniforge3/envs/regionclf/bin/python
mkdir -p data/regions_v3/logs
LOG=data/regions_v3/logs/run_v3.log
export PYTHONUNBUFFERED=1
step() { echo "== $(date '+%F %T') $*" >> "$LOG"; }

step "RUN_V3 START (waiting for the download)"
while pgrep -f "rhymoi_download.py" > /dev/null; do sleep 300; done
step "retry pass for failed downloads"
$PY312 src/colour_regions/rhymoi_download.py >> data/regions_v3/download.out 2>&1
$PY312 src/colour_regions/rhymoi_download.py --manifest-only >> "$LOG" 2>&1
step "speech screen"
$PYCLF src/secaiqu/v2/speech_screen.py --manifest data/regions_v3/manifest.csv --out data/regions_v3/speech_screen >> "$LOG" 2>&1
step "separation"
$PY src/transcription/transcribe_regions.py --steps sep >> "$LOG" 2>&1
step "GAME + ROSVOT"
$PY src/transcription/transcribe_regions.py --models game --steps midi,xml >> "$LOG" 2>&1
$PY src/transcription/transcribe_regions.py --models rosvot --steps midi >> "$LOG" 2>&1
step "ensemble"
bash src/transcription/ensemble_dataset.sh >> "$LOG" 2>&1
step "F0"
bash src/transcription/critic/extract_dataset_f0.sh >> "$LOG" 2>&1
step "primary selection + index"
$PY312 src/transcription/select_primary.py >> "$LOG" 2>&1
$PY312 src/transcription/build_dataset_index.py >> "$LOG" 2>&1
step "release tables"
$PY312 src/colour_regions/build_release.py >> "$LOG" 2>&1
$PY312 src/colour_regions/export_metadata.py >> "$LOG" 2>&1
$PY312 src/colour_regions/consolidate.py >> "$LOG" 2>&1
step "RUN_V3 DONE"
