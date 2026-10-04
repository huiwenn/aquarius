#!/usr/bin/env bash
# Crash-safe orchestration template (adapt the commands). Launch with nohup from a native arm64 shell.
# Every step must skip existing outputs, so the script can be rerun at any time.
# While separation runs: repeat passes over groups whose separation is complete. Then finish GPU + CPU steps,
# then ensemble / select / index. Decide "finished" from output COUNTS, not from whether a process is alive.
set -u
cd "$(dirname "$0")"
LOG=logs/pipeline.log; mkdir -p logs
complete() {  # true when every input in every group has a separated voice
  for g in data/audio/*/; do
    n_in=$(ls "$g" | wc -l); n_out=$(ls "data/vocals/$(basename "$g")" 2>/dev/null | wc -l)
    [ "$n_out" -lt "$n_in" ] && return 1
  done; return 0
}
pass() {
  python transcribe.py --model game --only-ready   >> "$LOG" 2>&1   # GPU; writes _processed.txt; retries batch 1
  python transcribe.py --model rosvot --only-ready >> "$LOG" 2>&1   # CPU, in parallel with GPU work
}
echo "START $(date '+%F %T')" >> "$LOG"
until complete; do
  pgrep -f separate.py > /dev/null || { echo "separation not running but incomplete — rerun it" >> "$LOG"; exit 1; }
  pass; sleep 120
done
pass
python ensemble.py   >> "$LOG" 2>&1
python f0.py         >> "$LOG" 2>&1
python select_primary.py  >> "$LOG" 2>&1   # fallback only for items in _processed.txt with no notes
python build_index.py     >> "$LOG" 2>&1
python stage_report.py data --stage vocals=vocals --stage game=midi/game --stage fallback=midi/fallback --fallback fallback >> "$LOG"
echo "DONE $(date '+%F %T')" >> "$LOG"
