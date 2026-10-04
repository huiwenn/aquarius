#!/usr/bin/env bash
# RMVPE (CPU, rosvot env) and PESTO (MPS, sep env) F0 for every region's separated vocals, in parallel.
# Output: data/transcription/critic/f0_{rmvpe,pesto}/<region>/<video_id>.npz  (skips existing)
set -u
cd "$(dirname "$0")/../../.."
T=${AQ_TRANS:-}
if [ -n "$T" ]; then V=$T/vocals; O=$T; else V=data/regions_transcription/vocals; O=data/transcription/critic; fi  # v2: AQ_TRANS=data/regions_v2/transcription
LOG=$O/extract_dataset_f0.log
mkdir -p "$O"
(
  for d in "$V"/*/; do r=$(basename "$d")
    /usr/local/Caskroom/miniforge/base/envs/rosvot/bin/python src/transcription/critic/f0_rmvpe.py "$d" "$O/f0_rmvpe/$r"
  done; echo "RMVPE DONE"
) >> "$LOG" 2>&1 &
(
  for d in "$V"/*/; do r=$(basename "$d")
    ~/miniforge3/envs/sep/bin/python src/transcription/critic/f0_pesto.py "$d" "$O/f0_pesto/$r"
  done; echo "PESTO DONE"
) >> "$LOG" 2>&1 &
wait
echo "ALL DONE" >> "$LOG"
