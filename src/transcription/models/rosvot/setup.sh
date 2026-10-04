#!/usr/bin/env bash
# Reproducible setup of ROSVOT (ACL 2024) for inference on Apple Silicon (tested M1 Pro, macOS 15).
# Run from the repo root:  bash src/transcription/models/rosvot/setup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
COMMIT=3c8332bf43adae35f6e4d64971862f2f6139b310
CKPT_GDRIVE_ID=1JNtNT37KiLq9uFQqHk7JFs-3trxd3bRh   # checkpoints.zip (584 MB), README "Model Weights" link
CKPT_SHA256=b6055e81315b93415c9bd7fc48e10a28a3da1bea960cab7385483bd7443ba852

# 1. code
mkdir -p "$ROOT/third_party"
if [ ! -d "$ROOT/third_party/ROSVOT" ]; then
  git clone https://github.com/RickyL-2000/ROSVOT.git "$ROOT/third_party/ROSVOT"
fi
cd "$ROOT/third_party/ROSVOT"
git checkout -q "$COMMIT"
git apply --check "$ROOT/src/transcription/models/rosvot/rosvot_device.patch" 2>/dev/null \
  && git apply "$ROOT/src/transcription/models/rosvot/rosvot_device.patch" || echo "patch already applied?"

# 2. env. NOTE: the default `conda` on this machine (/usr/local/Caskroom/miniforge) is an x86_64 (osx-64)
#    install; CONDA_SUBDIR=osx-arm64 makes it create a *native arm64* env (verified: python is Mach-O arm64,
#    torch.backends.mps.is_available() == True). With the arm64 install (~/miniforge3/bin/conda) no
#    CONDA_SUBDIR is needed. Without either, torch runs under Rosetta and MPS is unavailable.
if ! conda env list | grep -q '^rosvot '; then
  CONDA_SUBDIR=osx-arm64 conda create -y -n rosvot python=3.9
  conda run -n rosvot conda config --env --set subdir osx-arm64
fi
conda run -n rosvot pip install "numpy<2" cython
# pyworld 0.2.12 has no arm64 wheel; its isolated build fails -> build without isolation
conda run -n rosvot pip install --no-build-isolation pyworld==0.2.12
conda run -n rosvot pip install torch==2.1.1 torchaudio==2.1.1 librosa tqdm matplotlib==3.5 pyyaml \
  pretty_midi soundfile gdown "numpy<2"

# 3. checkpoints (ROSVOT + RWBD + RMVPE), trained on M4Singer only
if [ ! -f checkpoints/rosvot/model.pt ]; then
  conda run -n rosvot gdown "$CKPT_GDRIVE_ID" -O checkpoints.zip
  echo "$CKPT_SHA256  checkpoints.zip" | shasum -a 256 -c
  unzip -o -q checkpoints.zip
fi
echo "ROSVOT ready."
