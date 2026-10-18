#!/usr/bin/env bash
# Process one collection round end to end (same pipeline as rounds 1-3): speech screen → separation →
# GAME (+ trim, MusicXML, instrumental fallback) and ROSVOT → 3-run GAME ensemble → RMVPE/PESTO F0 →
# primary selection → dataset index → release tables. The audio must already be in data/regions_v<N>/audio/ with
# data/regions_v<N>/manifest.csv (src/secaiqu/v2/download.py with AQ_COLLECTION=data/regions_v<N>).
# Idempotent: every step skips existing outputs. Launch from a native arm64 shell (GPU):
#   nohup arch -arm64 /bin/bash src/transcription/run_round.sh 4 > /dev/null 2>&1 &
# Log: data/regions_v<N>/logs/run_round.log
set -u
N=${1:?usage: run_round.sh <round number ≥ 2>}
cd "$(dirname "$0")/../.."
B=data/regions_v$N
[ -f "$B/manifest.csv" ] || { echo "no $B/manifest.csv"; exit 1; }
export AQ_MANIFEST=$B/manifest.csv AQ_TRANS=$B/transcription PYTHONUNBUFFERED=1
PY=~/miniforge3/envs/sep/bin/python
PY312=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
PYCLF=~/miniforge3/envs/regionclf/bin/python
mkdir -p "$B/logs"
LOG=$B/logs/run_round.log
step() { echo "== $(date '+%F %T') $*" >> "$LOG"; }

step "ROUND $N START"
step "speech screen"
$PYCLF src/secaiqu/v2/speech_screen.py --manifest "$B/manifest.csv" --out "$B/speech_screen" >> "$LOG" 2>&1
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
step "ROUND $N DONE (check: grep -c Traceback $LOG)"
