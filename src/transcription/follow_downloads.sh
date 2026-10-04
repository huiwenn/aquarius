#!/usr/bin/env bash
# Keep transcribing while download_curated.py is still fetching audio:
#   refresh data/regions_audio/manifest.csv from disk → run_all.sh (skips finished work) → sleep.
# After the downloader exits: one final pass, then the dataset index.
set -u
cd "$(dirname "$0")/../.."
PY312=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
LOG=data/regions_transcription/follow.log

pass() {
  echo "=== pass $(date '+%F %T')" >> "$LOG"
  $PY312 src/secaiqu/download_curated.py --manifest-only >> "$LOG" 2>&1
  src/transcription/run_all.sh
}

while pgrep -f "download_curated.py --min-sleep" > /dev/null; do
  pass
  sleep 900
done
pass
$PY312 src/transcription/build_dataset_index.py >> "$LOG" 2>&1
echo "FOLLOW DONE $(date '+%F %T')" >> "$LOG"
