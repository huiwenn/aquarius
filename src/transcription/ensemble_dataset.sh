#!/usr/bin/env bash
# 3-run GAME ensemble for the whole dataset (docs/transcription.md §7.6):
#   run 1 = existing midi/game/<region>, runs 2–3 = two more GAME passes on the same separated vocals,
#   majority vote → midi/game_ens3/<region> → 50 ms offset trim → midi/game_ens3_pp/<region> → MusicXML.
# Idempotent: GAME skips existing outputs, the vote step skips finished recordings.
# Launch from a native arm64 shell.
set -u
cd "$(dirname "$0")/../.."
T=${AQ_TRANS:-data/regions_transcription}  # v2: AQ_TRANS=data/regions_v2/transcription
GAME=~/miniforge3/envs/game/bin/python
PY312=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
LOG=$T/ensemble_dataset.log
for d in "$T"/vocals/*/; do
  r=$(basename "$d")
  for k in 2 3; do
    $GAME src/transcription/models/game/run_game.py "$d" "$T/midi/game_run$k/$r" \
      --size medium --lang zh --seg-threshold 0.1 >> "$LOG" 2>&1
  done
  echo "GAME runs done: $r $(date '+%T')" >> "$LOG"
done
$PY312 src/transcription/ensemble_vote.py >> "$LOG" 2>&1
for d in "$T"/midi/game_ens3_pp/*/; do
  r=$(basename "$d")
  $PY312 src/transcription/midi_to_musicxml.py "$d" "$T/audio/$r" "$T/musicxml/game_ens3_pp/$r" >> "$LOG" 2>&1
done
echo "ENSEMBLE DONE $(date '+%F %T')" >> "$LOG"
