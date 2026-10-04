# YourMT3+ setup (Apple Silicon, no CUDA)

Code and checkpoints live in the HF Space, not the GitHub repo (the GitHub repo is only a README).

```bash
# arm64 conda (NOT the x86_64 /usr/local/Caskroom miniforge, which runs under Rosetta)
C=/Users/sophiasun/miniforge3/bin/conda
$C create -y -n ymt3 python=3.10
$C run -n ymt3 pip install torch==2.4.1 torchaudio==2.4.1 "lightning>=2.2.1" deprecated librosa einops \
    transformers==4.45.1 numpy==1.26.4 mido pretty_midi soundfile mir_eval wandb

cd third_party
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/spaces/mimbres/YourMT3 yourmt3_space
cd yourmt3_space && git checkout 5e66c1ea173a8186e0d20432b841d3180cc015b5
git lfs install --local          # otherwise `git lfs pull` silently skips
git lfs pull --include="amt/logs/2024/mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops/checkpoints/last.ckpt,amt/logs/2024/mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b80_ps2/checkpoints/model.ckpt"
```

No source patches to the Space are needed: `transcribe.py` imports the Space code and
replaces its `model_helper.transcribe()` (which hard-codes cuda) with a device-agnostic loop.
Default device is CPU because it is faster than MPS on an M1 Pro (see below).

Checkpoints (args copied from the Space `app.py`):
- `moe_nops` = "YPTF.MoE+Multi (noPS)": `mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops@last.ckpt`
- `moe_ps` (default; best on our singing benchmark) = "YPTF.MoE+Multi (PS)": `mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b80_ps2@model.ckpt`

Output: multi-track MIDI, one track per predicted instrument class. Vocal melody track is
named `Singing Voice`; a chorus track `Singing Voice (chorus)` can also appear. Filter with `singing`.

Speed (M1 Pro, fp32): 189 s file: cpu bsz8 34 s/min audio, cpu bsz32 35, mps bsz32 47; short clips: cpu 33-46, mps 76-80 s/min.
