"""
Family "sequence": self-supervised pretraining of the exp_seq_nn Transformer (input 'fact' = deg+reg+int+dur)
on unlabeled note sequences, then fine-tuning per task with exp_seq_nn (--init <ckpt>).

Objectives
  mlm  mask 15 % of note events (all fields → MASK), predict every field (deg, reg, int, dur) at masked positions
  lm   causal mask, predict the next note's fields
Corpora
  all     anthology + essen + trans_primary + trans_rosvot (~11.8k songs). Label-free, but transductive for every
          task (test songs are seen unlabeled).
  scores  anthology + essen only — no transcription is seen, so it is a clean test of "does pretraining on
          scores help the small transcription tasks T15 / T5".
Checkpoints: data/regionclf/tok/ssl_<obj>_<corpus>.pt

Run (regionseq env, MPS):
  python src/regionclf/exp_seq_pretrain.py --obj mlm --corpus all --steps 6000
  python src/regionclf/exp_seq_nn.py --tasks T15,T5 --arch tf --inp fact --init data/regionclf/tok/ssl_mlm_all.pt --tag ssl_mlm_all
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(2)
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import load  # noqa: E402
from regionclf.exp_seq_nn import CROP, DEV, FIELD_IDX, INPUTS, MASK, OFF, PAD, TF, augment, crop, encode_notes, pad  # noqa: E402
from regionclf.exp_seq_tok import TOK  # noqa: E402

CORPORA = {"all": ["anthology", "essen", "trans_primary", "trans_rosvot"], "scores": ["anthology", "essen"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obj", default="mlm", choices=["mlm", "lm"])
    ap.add_argument("--corpus", default="all", choices=list(CORPORA))
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--bs", type=int, default=64)
    a = ap.parse_args()
    seqs = [encode_notes(r["notes"]) for s in CORPORA[a.corpus] for r in load(s)]
    # long transcriptions contribute proportionally more crops
    wts = np.array([max(1.0, len(s) / CROP) for s in seqs])
    wts /= wts.sum()
    fields = INPUTS["fact"]
    model = TF(fields, n_cls=2).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.02)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=5e-4, total_steps=a.steps, pct_start=0.05)
    rng = np.random.default_rng(0)
    t0 = time.time()
    for step in range(a.steps):
        bi = rng.choice(len(seqs), a.bs, p=wts)
        x = pad([augment(crop(seqs[i], rng), rng, "fact") for i in bi]).to(DEV)
        valid = x[..., 0] != PAD
        if a.obj == "mlm":
            m = (torch.rand(valid.shape, device=DEV) < 0.15) & valid
            xin = x.clone()
            xin[m] = MASK
            h, _ = model.hidden(xin)
            tgt, sel = x, m
        else:
            h, _ = model.hidden(x, causal=True)
            h = h[:, :-1]
            tgt, sel = x[:, 1:], valid[:, 1:]
        loss = 0
        accs = {}
        for f in fields:
            lg = model.lm_heads[f](h[sel])
            t = tgt[..., FIELD_IDX[f]][sel] - OFF
            loss = loss + F.cross_entropy(lg, t)
            accs[f] = (lg.argmax(1) == t).float().mean().item()
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % 250 == 0 or step == a.steps - 1:
            print(f"step {step} loss {loss.item():.3f} acc " + " ".join(f"{k}={v:.2f}" for k, v in accs.items())
                  + f" ({time.time() - t0:.0f}s)", flush=True)
    out = TOK / f"ssl_{a.obj}_{a.corpus}.pt"
    torch.save({k: v.cpu() for k, v in model.state_dict().items()}, out)
    print("saved", out)


if __name__ == "__main__":
    main()
