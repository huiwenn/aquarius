"""
Frozen "MusicBERT" embeddings: manoskary/musicbert (https://huggingface.co/manoskary/musicbert), a 12-layer BERT MLM
trained on GigaMIDI with REMI+BPE tokens (miditok tokenizer manoskary/miditok-REMI). NOTE: this is a community
re-implementation of the MusicBERT idea, not Microsoft's OctupleMIDI checkpoint (microsoft/muzic ships fairseq
weights that need fairseq==0.10 and do not run on current torch/py3.11).

Notes → symusic Score (480 tpq, 120 bpm; transcription seconds → 2 beats/s) → REMI+BPE ids → 1024-token chunks
(length-weighted mean) → mean-pooled hidden states of the middle (layer 6) and last layer.

Output: data/regionclf/emb/{mbertmid,mbertlast}_midi_{norm}_{source}.npy

Run (arm64 env, needs `pip install miditok`):
  PYTHONPATH=src ~/miniforge3/envs/regionclf/bin/python src/regionclf/emb_musicbert.py --norms raw,tonic \
      --sources trans_primary,essen,anthology
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(2)  # machine is shared; also export OMP_NUM_THREADS=2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from regionclf.common import load  # noqa: E402
from regionclf.pretrained_io import tonic_normalize  # noqa: E402

EMB = ROOT / "data" / "regionclf" / "emb"


def to_score(notes, time_unit, tpq=480):
    from symusic import Note, Score, Tempo, TimeSignature, Track
    s = Score(tpq)
    s.tempos.append(Tempo(0, 120.0))
    s.time_signatures.append(TimeSignature(0, 4, 4))
    tr = Track("melody", 0, False)
    k = 2.0 if time_unit == "sec" else 1.0
    t0 = notes[:, 0].min()
    for on, du, p in notes:
        tr.notes.append(Note(int(round((on - t0) * k * tpq)), max(int(round(du * k * tpq)), 1),
                             int(np.clip(p, 0, 127)), 80))
    s.tracks.append(tr)
    return s


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--norms", default="raw,tonic")
    ap.add_argument("--sources", default="trans_primary,essen,anthology")
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    a = ap.parse_args()
    from miditok import MusicTokenizer
    from transformers import BertModel
    tok = MusicTokenizer.from_pretrained("manoskary/miditok-REMI")
    dev = torch.device(a.device)
    m = BertModel.from_pretrained("manoskary/musicbert", add_pooling_layer=False).to(dev).eval()
    L, CH = m.config.num_hidden_layers, 1024
    for src in a.sources.split(","):
        recs = load(src)
        for norm in a.norms.split(","):
            outs = [EMB / f"mbertmid_midi_{norm}_{src}.npy", EMB / f"mbertlast_midi_{norm}_{src}.npy"]
            if all(p.exists() for p in outs):
                continue
            t0 = time.time()
            mid, last, nunk = [], [], 0
            for r in recs:
                n = tonic_normalize(r["notes"]) if norm == "tonic" else r["notes"]
                seq = tok(to_score(n, r["time_unit"]))
                ids = (seq[0] if isinstance(seq, list) else seq).ids
                chunks = [ids[i:i + CH] for i in range(0, len(ids), CH)] or [[0]]
                w = np.array([len(c) for c in chunks], float)
                hm, hl = 0, 0
                for c, wi in zip(chunks, w / w.sum()):
                    hs = m(torch.tensor([c], device=dev), output_hidden_states=True).hidden_states
                    hm = hm + wi * hs[L // 2][0].mean(0).float().cpu().numpy()
                    hl = hl + wi * hs[L][0].mean(0).float().cpu().numpy()
                mid.append(hm)
                last.append(hl)
            np.save(outs[0], np.stack(mid).astype(np.float32))
            np.save(outs[1], np.stack(last).astype(np.float32))
            print(f"musicbert {norm} {src}: {len(recs)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
