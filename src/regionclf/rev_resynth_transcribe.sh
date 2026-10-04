#!/usr/bin/env bash
# Reviewer R3, step 3: transcribe the resynthesized audio with exactly the dataset pipeline
# (docs/transcription.md §4–5): [htdemucs separation, accompanied only] → GAME-1.0-medium (lang zh,
# seg-threshold 0.1) → 50 ms offset trim (postprocess.py).
#   in : data/regionclf/resynth/audio/<cond>/<sid>.wav            (rev_resynth_render.py)
#   out: data/regionclf/resynth/midi/game/<cond>/<sid>.mid, midi/game_pp/<cond>/<sid>.mid
# Run from the repo root (~35 min per condition for GAME on MPS; htdemucs ~1 h):
#   bash src/regionclf/rev_resynth_transcribe.sh [plain expressive heavy ornamented accompanied]
set -euo pipefail
export OMP_NUM_THREADS=3
R=data/regionclf/resynth
GAME=~/miniforge3/envs/game/bin/python
SEP=~/miniforge3/envs/sep/bin/python
PY=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
CONDS=${@:-plain expressive heavy ornamented accompanied}
for c in $CONDS; do
  in=$R/audio/$c
  if [ "$c" = accompanied ]; then
    $SEP src/transcription/separate.py $R/audio/accompanied_mix $R/audio/accompanied --model htdemucs.yaml
  fi
  $GAME src/transcription/models/game/run_game.py $in $R/midi/game/$c --size medium --lang zh --seg-threshold 0.1
  $PY src/transcription/postprocess.py $R/midi/game/$c $R/midi/game_pp/$c
done
