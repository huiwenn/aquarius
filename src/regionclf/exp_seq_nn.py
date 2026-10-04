"""
Family "sequence": neural sequence classifiers trained from scratch (and fine-tuned from SSL checkpoints,
see exp_seq_pretrain.py), on the shared grouped folds.

Input = one event per note, a *factored* embedding (sum of field embeddings):
  deg  scale degree relative to the estimated 宫 (12)          reg  register vs. song median, 6-semitone buckets (5)
  int  interval from previous note, clipped ±12 (+ start) (26)  dur  log2(IOI / median IOI) bin, −2..3 (6)
  pc   absolute pitch MIDI 0..127 (only in input mode 'raw', where random transposition ±6 is used as augmentation)
Input modes: fact = deg+reg+int+dur,  deg,  degdur = deg+dur,  intdur = int+dur,  raw = pc+int+dur.

Architectures (all small, ≤ ~0.5M params): cnn (3 dilated residual conv blocks, mean+max pool), gru (1-layer
BiGRU 128, attention pool), tf (Transformer encoder, d=128, 3 layers, 4 heads, learned positions, mean pool).
Training: random crops of CROP=256 notes (each song sampled `rep` times per epoch), tempo jitter = random ±1
shift of the duration bins for a random 10% of notes, class-balanced cross-entropy, AdamW, early stopping
(patience 6, ≤40 epochs of ≥1500 crops) on macro-F1 of an inner grouped validation split (≈15 % of the *training* fold). Evaluation
averages logits over sliding windows (256, stride 128) covering the whole song.

Run (regionseq env, MPS):
  python src/regionclf/exp_seq_nn.py --tasks T15,T5,E,A5 --arch cnn,gru,tf --inp fact
  python src/regionclf/exp_seq_nn.py --tasks T15 --arch tf --inp fact --init data/regionclf/tok/ssl_mlm_all.pt
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(2)
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, labels, log_result, task  # noqa: E402
from regionclf.exp_seq_tok import rel_dur  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.model_selection import StratifiedGroupKFold  # noqa: E402

DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
CROP = 256
FIELDS = {"deg": 12, "reg": 5, "int": 26, "dur": 6, "pc": 128}
INPUTS = {"fact": ["deg", "reg", "int", "dur"], "deg": ["deg"], "degdur": ["deg", "dur"],
          "intdur": ["int", "dur"], "raw": ["pc", "int", "dur"]}
PAD, MASK, OFF = 0, 1, 2  # every field value is stored +OFF; 0 = pad, 1 = mask


def encode_notes(notes: np.ndarray) -> np.ndarray:
    """(n, 5) int array of field ids (+OFF): deg, reg, int, dur, pc."""
    p = notes[:, 2].astype(int)
    g = estimate_gong(notes)
    deg = (p - g) % 12
    reg = np.clip(np.round((p - np.median(p)) / 6), -2, 2).astype(int) + 2
    iv = np.r_[25, np.clip(np.diff(p), -12, 12) + 12]
    dur = rel_dur(notes) + 2
    return np.stack([deg, reg, iv, dur, np.clip(p, 0, 127)], 1).astype(np.int64) + OFF


FIELD_IDX = {"deg": 0, "reg": 1, "int": 2, "dur": 3, "pc": 4}


# ----------------------------------------------------------------------------------------------- models
class Embed(nn.Module):
    def __init__(self, fields, d):
        super().__init__()
        self.fields = fields
        self.emb = nn.ModuleDict({f: nn.Embedding(FIELDS[f] + OFF, d, padding_idx=PAD) for f in fields})

    def forward(self, x):  # x: (B, T, 5)
        return sum(self.emb[f](x[..., FIELD_IDX[f]]) for f in self.fields)


class CNN(nn.Module):
    def __init__(self, fields, n_cls, d=128, drop=0.2):
        super().__init__()
        self.embed = Embed(fields, d)
        self.blocks = nn.ModuleList([nn.Sequential(nn.Conv1d(d, d, 5, padding=2 * dl, dilation=dl),
                                                   nn.BatchNorm1d(d), nn.GELU(), nn.Dropout(drop))
                                     for dl in (1, 2, 4)])
        self.head = nn.Linear(2 * d, n_cls)

    def encode(self, x):
        m = (x[..., 0] != PAD).float()
        h = self.embed(x).transpose(1, 2)
        for b in self.blocks:
            h = h + b(h)
        h = h.transpose(1, 2)
        mean = (h * m[..., None]).sum(1) / m.sum(1, keepdim=True).clamp(min=1)
        mx = h.masked_fill(m[..., None] == 0, -1e4).max(1).values
        return torch.cat([mean, mx], 1)

    def forward(self, x):
        return self.head(self.encode(x))


class GRU(nn.Module):
    def __init__(self, fields, n_cls, d=128, drop=0.2):
        super().__init__()
        self.embed = Embed(fields, d)
        self.rnn = nn.GRU(d, d, batch_first=True, bidirectional=True)
        self.att = nn.Linear(2 * d, 1)
        self.drop = nn.Dropout(drop)
        self.head = nn.Linear(2 * d, n_cls)

    def encode(self, x):
        m = x[..., 0] != PAD
        h, _ = self.rnn(self.drop(self.embed(x)))
        a = self.att(h).squeeze(-1).masked_fill(~m, -1e4).softmax(1)
        return self.drop((h * a[..., None]).sum(1))

    def forward(self, x):
        return self.head(self.encode(x))


class TF(nn.Module):
    """Transformer encoder; also used as the SSL backbone (heads 'mlm' / 'lm' predict every field)."""

    def __init__(self, fields, n_cls, d=128, layers=3, heads=4, drop=0.1, max_len=CROP + 8):
        super().__init__()
        self.fields = fields
        self.embed = Embed(fields, d)
        self.pos = nn.Embedding(max_len, d)
        layer = nn.TransformerEncoderLayer(d, heads, 4 * d, drop, batch_first=True, norm_first=True,
                                           activation="gelu")
        self.enc = nn.TransformerEncoder(layer, layers)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, n_cls)
        self.lm_heads = nn.ModuleDict({f: nn.Linear(d, FIELDS[f]) for f in fields})

    def hidden(self, x, causal=False):
        m = x[..., 0] == PAD
        T = x.shape[1]
        h = self.embed(x) + self.pos(torch.arange(T, device=x.device))[None]
        mask = nn.Transformer.generate_square_subsequent_mask(T, device=x.device) if causal else None
        return self.norm(self.enc(h, mask=mask, src_key_padding_mask=m, is_causal=causal)), m

    def encode(self, x):
        h, m = self.hidden(x)
        k = (~m).float()
        return (h * k[..., None]).sum(1) / k.sum(1, keepdim=True).clamp(min=1)

    def forward(self, x):
        return self.head(self.encode(x))


ARCHS = {"cnn": CNN, "gru": GRU, "tf": TF}


# ----------------------------------------------------------------------------------------------- data
def crop(seq, rng, n=CROP):
    if len(seq) <= n:
        return seq
    s = rng.integers(0, len(seq) - n + 1)
    return seq[s:s + n]


def augment(seq, rng, inp):
    seq = seq.copy()
    if inp == "raw":  # random transposition of absolute pitch
        seq[:, 4] = np.clip(seq[:, 4] + rng.integers(-6, 7), OFF, 127 + OFF)
    k = rng.random(len(seq)) < 0.1  # tempo/duration jitter: nudge 10% of duration bins by ±1
    seq[k, 3] = np.clip(seq[k, 3] + rng.choice([-1, 1], k.sum()), OFF, FIELDS["dur"] - 1 + OFF)
    return seq


def pad(batch):
    T = max(len(s) for s in batch)
    out = np.zeros((len(batch), T, 5), np.int64)
    for i, s in enumerate(batch):
        out[i, :len(s)] = s
    return torch.from_numpy(out)


def windows(seq, n=CROP, stride=CROP // 2):
    if len(seq) <= n:
        return [seq]
    starts = list(range(0, len(seq) - n + 1, stride))
    if starts[-1] != len(seq) - n:
        starts.append(len(seq) - n)
    return [seq[s:s + n] for s in starts]


@torch.no_grad()
def predict_logits(model, seqs, bs=128):
    model.eval()
    ws, owner = [], []
    for i, s in enumerate(seqs):
        for w in windows(s):
            ws.append(w)
            owner.append(i)
    out = []
    for b in range(0, len(ws), bs):
        out.append(model(pad(ws[b:b + bs]).to(DEV)).float().cpu())
    lg = torch.cat(out).numpy()
    owner = np.array(owner)
    return np.stack([lg[owner == i].mean(0) for i in range(len(seqs))])


def build_model(arch, inp, n_cls, init=None):
    fields = INPUTS[inp]
    m = ARCHS[arch](fields, n_cls)
    if init:
        sd = torch.load(init, map_location="cpu")
        own = m.state_dict()
        sd = {k: v for k, v in sd.items() if k in own and own[k].shape == v.shape and not k.startswith("head.")}
        m.load_state_dict(sd, strict=False)
    return m.to(DEV)


def train_eval(tr_recs, te_recs, arch, inp, seqcache, init=None, max_epochs=40, patience=6, seed=0,
               lr=None, rep=None, verbose=False):
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    classes = sorted(set(labels(tr_recs)))
    ci = {c: i for i, c in enumerate(classes)}
    y = np.array([ci[r["region"]] for r in tr_recs])
    g = np.array([r["group"] for r in tr_recs])
    # inner grouped validation split (~15 %)
    inner = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=seed)
    fit_i, val_i = next(inner.split(np.zeros(len(y)), y, g))
    seqs = [seqcache[r["item_id"]] for r in tr_recs]
    model = build_model(arch, inp, len(classes), init)
    lr = lr or (3e-4 if arch == "tf" else 1e-3)
    if init:
        lr = lr / 2
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.02)
    w = torch.tensor(len(y) / (len(classes) * np.bincount(y[fit_i], minlength=len(classes)).clip(1)),
                     dtype=torch.float32, device=DEV)
    rep = rep or max(1, int(round(1500 / len(fit_i))))
    best, best_state, bad = -1, None, 0
    bs = 64
    for ep in range(max_epochs):
        model.train()
        idx = np.tile(fit_i, rep)
        rng.shuffle(idx)
        for b in range(0, len(idx), bs):
            bi = idx[b:b + bs]
            x = pad([augment(crop(seqs[i], rng), rng, inp) for i in bi]).to(DEV)
            loss = F.cross_entropy(model(x), torch.from_numpy(y[bi]).to(DEV), weight=w, label_smoothing=0.05)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        vp = predict_logits(model, [seqs[i] for i in val_i]).argmax(1)
        f = f1_score(y[val_i], vp, average="macro")
        if verbose:
            print(f"  ep {ep} loss {loss.item():.3f} val F1 {f:.3f}", flush=True)
        if f > best + 1e-4:
            best, bad = f, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    lg = predict_logits(model, [seqcache[r["item_id"]] for r in te_recs])
    return np.array(classes)[lg.argmax(1)], lg, classes


def seq_cache(recs):
    return {r["item_id"]: encode_notes(r["notes"]) for r in recs}


def run(task_name, arch, inp, init=None, tag="", log=True):
    recs = task(task_name)
    cache = seq_cache(recs)
    t0 = time.time()
    y, pred = cv_predict(recs, lambda tr, te: train_eval(tr, te, arch, inp, cache, init)[0])
    name = f"nn[{arch}|{inp}]" + (f"+{tag}" if tag else "")
    if log:
        log_result(name, "sequence", task_name, y, pred,
                   notes=f"crop{CROP}, balanced CE, inner-val early stop; {time.time() - t0:.0f}s")
    return y, pred


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="T15,T5,E,A5")
    ap.add_argument("--arch", default="cnn,gru,tf")
    ap.add_argument("--inp", default="fact")
    ap.add_argument("--init", default=None)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    for t in a.tasks.split(","):
        for arch in a.arch.split(","):
            for inp in a.inp.split(","):
                run(t, arch, inp, a.init, a.tag)
