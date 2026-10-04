#!/usr/bin/env bash
# Steps after Round-2 transcription (run_v2.sh) finishes: release tables → merged corpus → example study →
# quality checks on the merged pool → figures → paper numbers and build. Logs to data/regions_v2/logs/after_v2.log.
set -u
cd "$(dirname "$0")/../.."
PY=/usr/local/Caskroom/miniforge/base/envs/py312/bin/python
LOG=data/regions_v2/logs/after_v2.log
{
  echo "== $(date '+%F %T') build_release"; $PY src/colour_regions/build_release.py
  echo "== corpus trans_merged";              $PY src/regionclf/corpus.py --sources trans_merged
  echo "== example study (merged pool, round 1 → round 2)"; OMP_NUM_THREADS=4 $PY src/regionclf/rev_merged.py
  echo "== quality checks on the merged core pool"
  AQ_INDEX=data/colour_regions/transcription_index.csv AQ_TAG=_merged $PY src/transcription/audit/score_reference.py
  AQ_INDEX=data/colour_regions/transcription_index.csv AQ_TAG=_merged $PY src/transcription/audit/cross_performance.py
  echo "== figures";                          $PY notebooks/04_colour_regions_corpus.py
  echo "== paper";                            bash ../colour_regions_paper/build.sh
  echo "== $(date '+%F %T') AFTER_V2 DONE"
} >> "$LOG" 2>&1
