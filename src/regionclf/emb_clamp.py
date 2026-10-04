"""
Extract frozen CLaMP 3 (C2 symbolic checkpoint) and M3 (CLaMP 2's self-supervised symbolic encoder) embeddings
for every corpus record, in MTF or interleaved-ABC input format, with or without tonic normalization.

  CLaMP 3: https://github.com/sanderwood/clamp3  weights https://huggingface.co/sander-wood/clamp3 (…_c2_… .pth)
  M3:      https://huggingface.co/sander-wood/clamp2 (weights_m3_p_size_64_p_length_512_… .pth)

Weights are expected in third_party/clamp3/code/ (git clone + curl, see report). Only the symbolic branch is built
(no XLM-R text model download). Long inputs are split into 512-patch segments and averaged weighted by length,
exactly as clamp3/code/extract_clamp3.py does.

Output: data/regionclf/emb/{model}_{fmt}_{norm}_{source}.npy  float32 [n_records, 768] in corpus order, where
  model ∈ {c2 (projected global = CLaMP 3 joint space), c2pre (mean-pooled pre-projection), m3 (mean-pooled)}
  fmt ∈ {mtf, abc}, norm ∈ {raw, tonic}, source ∈ {anthology, essen, trans_primary}

Run (arm64 env):
  PYTHONPATH=src ~/miniforge3/envs/regionclf/bin/python src/regionclf/emb_clamp.py --models c2,m3 \
      --fmts mtf,abc --norms raw,tonic --sources anthology,essen,trans_primary [--device mps]
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(2)  # machine is shared; also export OMP_NUM_THREADS=2

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "third_party" / "clamp3" / "code"
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(ROOT / "src"))

from config import M3_HIDDEN_SIZE, PATCH_LENGTH, PATCH_NUM_LAYERS, PATCH_SIZE  # noqa: E402
from transformers import BertConfig  # noqa: E402
from utils import M3Patchilizer, M3PatchEncoder  # noqa: E402

from regionclf.common import load  # noqa: E402
from regionclf.pretrained_io import to_abc, to_mtf, tonic_normalize  # noqa: E402

EMB = ROOT / "data" / "regionclf" / "emb"
W_C2 = CODE / ("weights_clamp3_c2_h_size_768_t_model_FacebookAI_xlm-roberta-base_t_length_128_a_size_768_a_layers_12"
               "_a_length_128_s_size_768_s_layers_12_p_size_64_p_length_512.pth")
W_M3 = CODE / "weights_m3_p_size_64_p_length_512_t_layers_3_p_layers_12_h_size_768_lr_0.0001_batch_16_mask_0.45.pth"


def build(model: str, device):
    cfg = BertConfig(vocab_size=1, hidden_size=M3_HIDDEN_SIZE, num_hidden_layers=PATCH_NUM_LAYERS,
                     num_attention_heads=M3_HIDDEN_SIZE // 64, intermediate_size=M3_HIDDEN_SIZE * 4,
                     max_position_embeddings=PATCH_LENGTH)
    enc = M3PatchEncoder(cfg)
    proj = torch.nn.Linear(M3_HIDDEN_SIZE, 768)
    if model == "c2":
        sd = torch.load(W_C2, map_location="cpu", weights_only=True)["model"]
        e = {k[len("symbolic_model."):]: v for k, v in sd.items() if k.startswith("symbolic_model.")}
        p = {k[len("symbolic_proj."):]: v for k, v in sd.items() if k.startswith("symbolic_proj.")}
        proj.load_state_dict(p)
    else:
        sd = torch.load(W_M3, map_location="cpu", weights_only=True)["model"]
        e = {k[len("encoder."):]: v for k, v in sd.items() if k.startswith("encoder.")}
    missing, unexpected = enc.load_state_dict(e, strict=False)
    print(f"{model}: missing {missing} unexpected {unexpected}", flush=True)
    return enc.to(device).eval(), proj.to(device).eval()


@torch.no_grad()
def embed_texts(texts, enc, proj, device, bs=8):
    """Returns (pooled_pre [n,768], projected [n,768]). Segmenting/weighting follows extract_clamp3.py."""
    pat = M3Patchilizer()
    segs, owner, weight = [], [], []
    for i, t in enumerate(texts):
        ids = torch.tensor(pat.encode(t, add_special_patches=True))
        chunks = [ids[j:j + PATCH_LENGTH] for j in range(0, len(ids), PATCH_LENGTH)]
        rem = len(ids) % PATCH_LENGTH
        if len(chunks) > 1:
            chunks[-1] = ids[-PATCH_LENGTH:]
        for k, c in enumerate(chunks):
            segs.append(c)
            owner.append(i)
            last = k == len(chunks) - 1
            weight.append(rem if (last and rem) else PATCH_LENGTH if len(chunks) > 1 else len(c))
    order = np.argsort([len(s) for s in segs])
    pre = np.zeros((len(segs), M3_HIDDEN_SIZE), np.float32)
    pj = np.zeros((len(segs), 768), np.float32)
    for b in range(0, len(order), bs):
        idx = order[b:b + bs]
        L = max(len(segs[i]) for i in idx)
        x = torch.zeros((len(idx), L, PATCH_SIZE), dtype=torch.long)
        m = torch.zeros((len(idx), L))
        for r, i in enumerate(idx):
            x[r, :len(segs[i])] = segs[i]
            m[r, :len(segs[i])] = 1
        h = enc(x, m.to(device))["last_hidden_state"]
        mm = m.to(device).unsqueeze(-1)
        pooled = (h * mm).sum(1) / mm.sum(1)
        pre[idx] = pooled.float().cpu().numpy()
        pj[idx] = proj(pooled).float().cpu().numpy()
    owner, weight = np.array(owner), np.array(weight, float)
    out_pre = np.zeros((len(texts), M3_HIDDEN_SIZE), np.float32)
    out_pj = np.zeros((len(texts), 768), np.float32)
    for i in range(len(texts)):
        s = owner == i
        w = weight[s][:, None] / weight[s].sum()
        out_pre[i] = (pre[s] * w).sum(0)
        out_pj[i] = (pj[s] * w).sum(0)
    return out_pre, out_pj


def texts_for(recs, fmt, norm):
    out = []
    for r in recs:
        n = tonic_normalize(r["notes"]) if norm == "tonic" else r["notes"]
        out.append(to_mtf(n, r["time_unit"]) if fmt == "mtf" else to_abc(n, r["time_unit"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="c2,m3")
    ap.add_argument("--fmts", default="mtf,abc")
    ap.add_argument("--norms", default="raw,tonic")
    ap.add_argument("--sources", default="anthology,essen,trans_primary")
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--bs", type=int, default=8)
    a = ap.parse_args()
    EMB.mkdir(parents=True, exist_ok=True)
    device = torch.device(a.device)
    for model in a.models.split(","):
        enc, proj = build(model, device)
        for src in a.sources.split(","):
            recs = load(src)
            for fmt in a.fmts.split(","):
                for norm in a.norms.split(","):
                    tag = f"{fmt}_{norm}_{src}"
                    outs = {"c2": EMB / f"c2_{tag}.npy", "c2pre": EMB / f"c2pre_{tag}.npy"} if model == "c2" \
                        else {"m3": EMB / f"m3_{tag}.npy"}
                    if all(p.exists() for p in outs.values()):
                        continue
                    t0 = time.time()
                    pre, pj = embed_texts(texts_for(recs, fmt, norm), enc, proj, device, a.bs)
                    if model == "c2":
                        np.save(outs["c2"], pj)
                        np.save(outs["c2pre"], pre)
                    else:
                        np.save(outs["m3"], pre)
                    print(f"{model} {tag}: {pre.shape} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
