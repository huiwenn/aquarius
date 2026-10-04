#!/usr/bin/env bash
# Stage driver with sanity checks between stages. Each stage is idempotent; rerun the script to resume.
# Usage: .claude/skills/regional-folk-audio-dataset/scripts/run_pipeline.sh [download|transcribe|select|index|audit|all]
# Run from the repo root in a NATIVE arm64 shell (see references/environment.md).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PY312=${PY312:-/usr/local/Caskroom/miniforge/base/envs/py312/bin/python}
ARM=${ARM:-$HOME/miniforge3/envs/sep/bin/python}
STAGE=${1:-all}

check_arch() {
  local a; a=$($ARM -c "import platform; print(platform.processor())")
  [[ "$a" == "arm" ]] || { echo "ERROR: $ARM reports processor '$a' (Rosetta?). GPU stages would run on CPU."; exit 1; }
}

per_region_counts() {
  $PY312 - <<'EOF'
import pandas as pd
m = pd.read_csv("data/regions_audio/manifest.csv")
t = m.groupby("region").status.value_counts().unstack(fill_value=0)
print(t.to_string())
short = t[t.get("ok", 0) < 30]
if len(short):
    print("\nWARNING: regions below 30 downloaded:", ", ".join(short.index))
EOF
}

if [[ $STAGE == download || $STAGE == all ]]; then
  [[ -n $(ls data/regions_curated/*.json 2>/dev/null) ]] || { echo "No curated lists — run curation first."; exit 1; }
  $PY312 src/secaiqu/download_curated.py --min-sleep 45 --max-sleep 90 --cooldown 3600 --max-cooldowns 24
  $PY312 src/secaiqu/download_fallbacks.py
  $PY312 src/secaiqu/download_curated.py --manifest-only
  per_region_counts
fi

if [[ $STAGE == transcribe || $STAGE == all ]]; then
  check_arch
  src/transcription/run_all.sh
fi

if [[ $STAGE == select || $STAGE == all ]]; then
  check_arch
  $ARM src/transcription/select_primary.py
fi

if [[ $STAGE == index || $STAGE == all ]]; then
  $PY312 src/transcription/build_dataset_index.py
  $PY312 - <<'EOF'
import pandas as pd
d = pd.read_csv("data/regions_transcription/dataset_index.csv")
bad = d.midi_path.isna().sum() + d.musicxml_path.isna().sum()
print(f"{len(d)} recordings; missing midi/xml: {bad}; zero-note: {(d.n_notes == 0).sum()}; "
      f"sparse (<0.3 notes/s): {(d.notes_per_s < 0.3).sum()}")
print(d.transcription_model.value_counts().to_string())
EOF
fi

if [[ $STAGE == audit || $STAGE == all ]]; then
  src/transcription/critic/extract_dataset_f0.sh
  $PY312 src/transcription/audit/score_reference.py
  $PY312 src/transcription/audit/cross_performance.py
fi
