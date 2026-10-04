"""
Frozen text / symbolic-LM embeddings of textual music renderings (family "pretrained").

Renderings (all from regionclf.pretrained_io, tonic-normalized unless *_raw):
  abc     standard single-voice ABC (K:C, L:1/8, fixed 4/4 bars)       e.g. "X:1\\nL:1/8\\nM:4/4\\nK:C\\nC2 D2 E4 | …"
  deg     简谱 scale-degree string (movable-do 1–7, ' , octave marks, - holds, _ short)

Models:
  qwen3emb   Qwen/Qwen3-Embedding-0.6B via sentence-transformers (last-token pooling, 32k context; we cap 2048)
  mpnet      sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (512-token cap → truncated melodies)
  mupt       m-a-p/MuPT-v1-8192-190M (LLaMA-style ABC LM, trained on ~7M ABC pieces). Input uses MuPT's "<n>"
             newline convention; embedding = mean-pooled hidden state of the middle layer (mupt-mid) and last
             layer (mupt-last), truncated to 2048 tokens.

Output: data/regionclf/emb/{model}_{rendering}_{norm}_{source}.npy

Run (arm64 env):
  PYTHONPATH=src ~/miniforge3/envs/regionclf/bin/python src/regionclf/emb_text.py --models qwen3emb \
      --renders abc,deg --norms tonic --sources trans_primary,essen,anthology [--device mps]
"""

import argparse
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(2)  # machine is shared; also export OMP_NUM_THREADS=2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from regionclf.common import load  # noqa: E402
from regionclf.pretrained_io import to_abc, to_degrees, tonic_normalize  # noqa: E402

EMB = ROOT / "data" / "regionclf" / "emb"


def std_abc(notes, time_unit, max_bars=120):
    inter = to_abc(notes, time_unit)
    bars = re.findall(r"^\[V:1\](.*)\|$", inter, flags=re.M)[:max_bars]
    return "X:1\nL:1/8\nM:4/4\nK:C\n" + " | ".join(bars) + " |]"


def render(recs, kind, norm):
    out = []
    for r in recs:
        n = tonic_normalize(r["notes"]) if norm == "tonic" else r["notes"]
        out.append(std_abc(n, r["time_unit"]) if kind == "abc" else to_degrees(n, r["time_unit"]))
    return out


@torch.no_grad()
def embed_st(name, texts, device, max_len, bs):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(name, device=str(device))
    m.max_seq_length = max_len
    return m.encode(texts, batch_size=bs, show_progress_bar=True, convert_to_numpy=True).astype(np.float32)


_MUPT = {}


def _mupt_tokenizer():
    """MuPT's remote tokenizer is broken as shipped: it applies GPT-2 byte-level mapping (space → 'Ġ') while its
    vocab/merges use SentencePiece-style '▁', and it skips the first merge line as if it were a '#version'
    header. Result = character-level ids. We re-implement: '\n' → '<n>' token, spaces → '▁', Metaspace-style
    word split, BPE with all merges."""
    from transformers import AutoTokenizer
    from huggingface_hub import hf_hub_download
    name = "m-a-p/MuPT-v1-8192-190M"
    tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True, use_fast=False)
    lines = Path(hf_hub_download(name, "merges.txt")).read_text(encoding="utf-8").split("\n")
    tok.bpe_ranks = {tuple(l.split(" ")): i for i, l in enumerate(lines) if len(l.split(" ")) == 2}
    tok.cache = {}

    def encode(text):
        toks = []
        for k, seg in enumerate(text.split("\n")):
            if k:
                toks.append("<n>")
            for w in re.findall(r"▁?[^▁]+|▁+", seg.replace(" ", "▁")):
                toks += tok.bpe(w).split(" ")
        unk = tok.encoder["<unk>"]
        return [tok.encoder["<bos>"]] + [tok.encoder.get(t, unk) for t in toks]
    return encode


@torch.no_grad()
def embed_mupt(texts, device, max_len=2048):
    from transformers import AutoModelForCausalLM
    if not _MUPT:
        _MUPT["enc"] = _mupt_tokenizer()
        _MUPT["m"] = AutoModelForCausalLM.from_pretrained("m-a-p/MuPT-v1-8192-190M",
                                                          dtype=torch.float32).to(device).eval()
    enc, m = _MUPT["enc"], _MUPT["m"]
    L = m.config.num_hidden_layers
    mid, last = [], []
    for t in texts:
        ids = torch.tensor([enc(t)[:max_len]], device=device)
        hs = m(ids, output_hidden_states=True).hidden_states
        mid.append(hs[L // 2][0, 1:].mean(0).float().cpu().numpy())
        last.append(hs[L][0, 1:].mean(0).float().cpu().numpy())
    return np.stack(mid), np.stack(last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="qwen3emb")
    ap.add_argument("--renders", default="abc,deg")
    ap.add_argument("--norms", default="tonic")
    ap.add_argument("--sources", default="trans_primary,essen,anthology")
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    ap.add_argument("--bs", type=int, default=4)
    a = ap.parse_args()
    EMB.mkdir(parents=True, exist_ok=True)
    dev = torch.device(a.device)
    for model in a.models.split(","):
        for src in a.sources.split(","):
            recs = load(src)
            for kind in a.renders.split(","):
                for norm in a.norms.split(","):
                    tag = f"{kind}_{norm}_{src}"
                    t0 = time.time()
                    if model == "mupt":
                        outs = [EMB / f"muptmid_{tag}.npy", EMB / f"muptlast_{tag}.npy"]
                        if all(p.exists() for p in outs):
                            continue
                        mid, last = embed_mupt(render(recs, kind, norm), dev)
                        np.save(outs[0], mid)
                        np.save(outs[1], last)
                    else:
                        out = EMB / f"{model}_{tag}.npy"
                        if out.exists():
                            continue
                        name = {"qwen3emb": "Qwen/Qwen3-Embedding-0.6B",
                                "mpnet": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"}[model]
                        np.save(out, embed_st(name, render(recs, kind, norm), dev,
                                              2048 if model == "qwen3emb" else 512, a.bs))
                    print(f"{model} {tag} done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
