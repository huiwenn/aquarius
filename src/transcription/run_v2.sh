#!/usr/bin/env bash
# Round-2 (v2) transcription, same pipeline as round 1 (docs/transcription.md), chained end to end.
# Assumes separation (`transcribe_regions.py --steps sep`) is already running or finished.
#   while separation runs: GAME (+ trim, MusicXML, instrumental fallback) and ROSVOT on fully separated regions
#   afterwards: final passes → 3-run GAME ensemble → primary selection → dataset index
# Idempotent: every step skips existing outputs. Launch from a native arm64 shell.
set -u
cd "$(dirname "$0")/../.."
export AQ_MANIFEST=data/regions_v2/manifest.csv AQ_TRANS=data/regions_v2/transcription
PY=~/miniforge3/envs/sep/bin/python
PY312=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
LOG=data/regions_v2/logs/run_v2.log
export PYTHONUNBUFFERED=1

pass() {
  $PY src/transcription/transcribe_regions.py --models game --steps midi,xml --only-ready >> "$LOG" 2>&1
  $PY src/transcription/transcribe_regions.py --models rosvot --steps midi --only-ready >> "$LOG" 2>&1
}
echo "RUN_V2 START $(date '+%F %T')" >> "$LOG"
while pgrep -f "transcribe_regions.py --steps sep" > /dev/null; do
  pass
  sleep 120
done
pass
echo "PASSES DONE $(date '+%F %T')" >> "$LOG"
bash src/transcription/ensemble_dataset.sh
bash src/transcription/critic/extract_dataset_f0.sh   # RMVPE + PESTO → $AQ_TRANS/f0_{rmvpe,pesto}
$PY312 src/transcription/select_primary.py >> "$LOG" 2>&1
$PY312 src/transcription/build_dataset_index.py >> "$LOG" 2>&1
echo "RUN_V2 DONE $(date '+%F %T')" >> "$LOG"
