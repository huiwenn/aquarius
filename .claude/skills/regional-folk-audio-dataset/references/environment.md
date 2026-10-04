# Environment (Apple Silicon worked example)

## Architecture pitfalls

- **Check every Python's arch before installing torch:**
  `python -c "import platform, torch; print(platform.machine(), torch.backends.mps.is_available())"`.
  In the worked example the default conda (`/usr/local/Caskroom/miniforge`, incl. `py312`) was **x86_64 under
  Rosetta**: torch ran with no MPS and some packages (llvmlite) failed to build.
- The native arm64 conda was at `~/miniforge3`. Its envs don't show up in the default `conda env list`, so call
  their pythons by absolute path (`~/miniforge3/envs/<env>/bin/python`).
- **Architecture is inherited.** An arm64 binary launched from an x86 (Rosetta) parent reports
  `platform.processor() == "i386"`. audio-separator then decides "not ARM" and silently uses the CPU: 278 s instead
  of 53 s for a 417 s song. Launch GPU pipelines from an arm64 Python (the orchestrator runs in the arm64 `sep` env).
- You can create an arm64 env from an x86 conda with `CONDA_SUBDIR=osx-arm64 conda create …` plus
  `conda config --env --set subdir osx-arm64` (how the `rosvot` env was made).
- `~/.local` site-packages from another arch can shadow env packages. Set `PYTHONNOUSERSITE=1`.
- The system Node (Homebrew node 15) was broken (missing ICU dylib). Install Node in its own conda env
  (`conda create -n node -c conda-forge "nodejs>=22"`) rather than touching Homebrew.

## Env list (worked example)

| Env | Arch/Python | Purpose |
|---|---|---|
| `py312` (default conda, x86) | 3.12 | yt-dlp, evaluation, MusicXML, index, audit (CPU-only work) |
| `~/miniforge3/envs/sep` | arm64 3.11 | audio-separator (htdemucs/BS-RoFormer), PESTO, pipeline orchestrator |
| `~/miniforge3/envs/game` | arm64 3.12 | GAME (Lightning, MPS) |
| `~/miniforge3/envs/some` | arm64 3.10 | SOME (`librosa<0.10`, `setuptools<81`) |
| `rosvot` (arm64 via CONDA_SUBDIR) | 3.9 | ROSVOT + RMVPE, torch 2.1.1, **CPU** |
| `~/miniforge3/envs/ymt3` | arm64 3.10 | YourMT3+ (torch 2.4.1, transformers 4.45.1), **CPU** |
| `~/miniforge3/envs/basicpitch` | arm64 3.10 | Basic Pitch (CoreML) |
| `~/miniforge3/envs/vocalparse` | arm64 3.11 | VocalParse (not used in production) |
| `~/miniforge3/envs/node` | arm64 | Node 26 for yt-dlp JS challenges and the bgutil server |

Third-party repos and checkpoints live in `third_party/` (gitignored). Record commit hashes and checkpoint names
in the research log.

## Device quirks per model

| Model | Device | Notes |
|---|---|---|
| htdemucs / BS-RoFormer | MPS | autocast gives no speedup |
| GAME | MPS | via Lightning; long files slower; watch swap |
| SOME | MPS | its runner loads the model once |
| ROSVOT | CPU | MPS output is wrong on torch 2.1 (lacks FFT/complex, garbage even when patched); bsz 1 |
| YourMT3+ | CPU | faster than MPS; MPS output also differed |
| PESTO | MPS | use `pesto.predict` |
| RMVPE | CPU | bundled with ROSVOT |
| VocalParse | MPS | bf16, ~8 GB |

Run GPU and CPU models as **parallel processes**. A sequential per-region loop left the GPU idle during ROSVOT and
took ~40 min per region.

## Orphans and contention

- Killing an orchestrator does not kill its grandchildren. Look for them with
  `ps -eo pid,ppid,command | grep -E "run_game|infer.py|separate.py"` and kill them, or they fight for the GPU.
  An orphaned GAME slowed the live one to 0.11 it/s.
- Swap pressure (9 GB used) slowed GAME noticeably. Close other GPU jobs during long runs.
