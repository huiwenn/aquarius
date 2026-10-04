# Commands (canonical scripts live in the repo, not here)

Run from the repo root. The env for each command is given in brackets.
- PY312 = `/usr/local/Caskroom/miniforge/base/envs/py312/bin/python` (or `conda run -n py312 --no-capture-output python`)
- ARM = `~/miniforge3/envs/<env>/bin/python`

## 1. Curation
```bash
# [py312] logged, search-only candidate discovery (agents call this)
python src/secaiqu/search_candidates.py --region <class> -n 15 "<query>" "<query2>"
# agents write data/regions_curated/<class>.json; builders kept in src/secaiqu/curation/
```

## 2. Download
```bash
# [py312] throttled, cookie-authenticated, cooldown-and-resume
python src/secaiqu/download_curated.py --min-sleep 45 --max-sleep 90 --cooldown 3600 --max-cooldowns 24
# [py312] rebuild manifest from disk (safe any time)
python src/secaiqu/download_curated.py --manifest-only
# [py312] fallback cascade for failures (add --allow-replacement to search replacements)
python src/secaiqu/download_fallbacks.py
# optional PO-token server
~/miniforge3/envs/node/bin/node third_party/bgutil-ytdlp-pot-provider/server/build/main.js &
```

## 3. Benchmark & model selection
```bash
python src/transcription/build_benchmark.py          # [py312] 160 clips + gt/ + gt_A2/
python src/transcription/build_mix_benchmark.py      # [py312] +3 dB ChMusic mixes
~/miniforge3/envs/sep/bin/python src/transcription/separate.py IN OUT --model htdemucs.yaml
~/miniforge3/envs/game/bin/python src/transcription/models/game/run_game.py IN OUT --size medium --lang zh --seg-threshold 0.1
~/miniforge3/envs/some/bin/python src/transcription/models/some/run_some.py IN OUT --ckpt 0119
conda run -n rosvot --no-capture-output python src/transcription/models/rosvot/run_rosvot.py IN OUT
~/miniforge3/envs/ymt3/bin/python src/transcription/models/yourmt3/transcribe.py IN OUT --model moe_ps --device cpu
~/miniforge3/envs/basicpitch/bin/python src/transcription/models/basic_pitch/transcribe.py IN OUT
PYTHONNOUSERSITE=1 ~/miniforge3/envs/vocalparse/bin/python src/transcription/models/vocalparse/run_vocalparse.py IN OUT
python src/transcription/evaluate.py MODEL [MODEL ...] [--track-filter singing]   # [py312]
python src/transcription/postprocess.py IN_MIDI OUT_MIDI --trim 0.05              # [py312]
```

## 4. Production transcription
```bash
# launch from an arm64 shell/python (architecture is inherited!)
src/transcription/run_all.sh                # GPU side (sep→GAME→trim→XML) ∥ CPU side (ROSVOT)
src/transcription/follow_downloads.sh       # repeat run_all while downloads continue, then index
~/miniforge3/envs/sep/bin/python src/transcription/transcribe_regions.py --models game --steps fallback,xml --regions <class>
~/miniforge3/envs/sep/bin/python src/transcription/select_primary.py   # primary = game_pp | rosvot | yourmt3
python src/transcription/build_dataset_index.py                        # [py312] dataset_index.csv
```

## 5. Critic & audit
```bash
src/transcription/critic/extract_dataset_f0.sh       # RMVPE (rosvot env, CPU) ∥ PESTO (sep env, MPS)
/usr/local/Caskroom/miniforge/base/envs/rosvot/bin/python src/transcription/critic/f0_rmvpe.py IN OUT
~/miniforge3/envs/sep/bin/python src/transcription/critic/f0_pesto.py IN OUT
python src/transcription/critic/validate_f0.py [--pesto-conf 0.5]                 # [py312] tracker accuracy vs GT
python src/transcription/critic/eval_critic.py [--base game_pp@sep_htdemucs]      # [py312] critic ↔ GT agreement + F1 per correction
python src/transcription/audit/score_reference.py                                 # [py312] Anthology scores vs chance
python src/transcription/audit/cross_performance.py                               # [py312] same-song vs different-song
```
