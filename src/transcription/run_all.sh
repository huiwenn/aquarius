#!/usr/bin/env bash
# Full 色彩区 transcription run: two processes in parallel.
#   GPU side: htdemucs separation → GAME → offset trim → MusicXML   (primary transcription)
#   CPU side: ROSVOT on regions whose separation is complete        (secondary / QC transcription)
# Safe to rerun at any time: every step skips outputs that already exist.
# Must be launched from a native arm64 shell (see transcribe_regions.py docstring).
set -u
cd "$(dirname "$0")/../.."
PY=~/miniforge3/envs/sep/bin/python
LOG=data/regions_transcription
mkdir -p "$LOG"

PYTHONUNBUFFERED=1 $PY src/transcription/transcribe_regions.py --models game >> "$LOG/gpu_side.log" 2>&1 &
GPU=$!

while kill -0 $GPU 2>/dev/null; do
  PYTHONUNBUFFERED=1 $PY src/transcription/transcribe_regions.py --models rosvot --steps midi --only-ready >> "$LOG/cpu_side.log" 2>&1
  sleep 120
done
PYTHONUNBUFFERED=1 $PY src/transcription/transcribe_regions.py --models rosvot --steps midi --only-ready >> "$LOG/cpu_side.log" 2>&1
wait $GPU
echo "RUN_ALL DONE $(date)" >> "$LOG/gpu_side.log"
