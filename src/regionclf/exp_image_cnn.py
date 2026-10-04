"""
Family "image", step 4: small CNNs trained from scratch on the renderings (MPS), plus light fine-tuning of a
pretrained backbone (--finetune), on the shared song-grouped folds.

Small CNN: 3 x [conv3x3-BN-ReLU, conv3x3-BN-ReLU, maxpool] (32/64/128 ch) -> global avg+max pool -> dropout -> linear.
Trained on crops (each crop inherits its song's label; anthology: every other window), class-balanced
cross-entropy, AdamW (bs 256, 15 epochs or >= 300 steps, one-cycle LR). (Rows "img-cnn-*" are an earlier run
with a fixed 15 epochs, which under-trained the small tasks; "img-cnnv2-*" are the reported ones.)
Windowed renderings get a random +-4-column time shift as augmentation. Song prediction = mean crop softmax.
Fine-tune (--finetune rendering): timm resnet18 (ImageNet) at 112x224, all layers, bs 32, max(6 epochs, 300 steps),
lr 3e-4 head / 1e-4 backbone. (Rows "img-ft-resnet18-*" are a collapsed first attempt with ~10 optimizer steps.)

Also saves, per task/rendering, out-of-fold crop-level probabilities (data/regionclf/img/cnn_oof_<task>_<rd>.npz)
and input-gradient saliency averaged per class (for the musicological reading in exp_image_explain.py).

Run (arm64 env):
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_cnn.py --tasks T15,T5,E,E5prior,A5 \
      --renderings roll,contour,jianpu,ssm,itrans
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_cnn.py --tasks T5,E5prior --finetune itrans   # and --finetune roll
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_cnn.py --ensemble --tasks A5,E,T5,T15,E5prior \
      --renderings itrans,jianpu        # late fusion of saved OOF probabilities
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import folds, labels, log_result  # noqa: E402
from regionclf.exp_image_embed import MAX_CROPS, crop_subset  # noqa: E402
from regionclf.exp_image_frozen import SOURCE, get_task  # noqa: E402
from regionclf.exp_image_render import IMG, already_logged, get  # noqa: E402

torch.set_num_threads(2)
MIN_STEPS = 300  # small tasks (T5: 1.6k crops; itrans: 1 image/song) otherwise get < 50 optimizer steps and collapse
DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


class SmallCNN(nn.Module):
    def __init__(self, cin, ncls, w=32):
        super().__init__()
        layers, c = [], cin
        for co in (w, 2 * w, 4 * w):
            layers += [nn.Conv2d(c, co, 3, padding=1), nn.BatchNorm2d(co), nn.ReLU(),
                       nn.Conv2d(co, co, 3, padding=1), nn.BatchNorm2d(co), nn.ReLU(), nn.MaxPool2d(2, ceil_mode=True)]
            c = co
        self.f = nn.Sequential(*layers)
        self.head = nn.Sequential(nn.Dropout(0.3), nn.Linear(2 * c, ncls))

    def forward(self, x):
        h = self.f(x)
        return self.head(torch.cat([h.mean((2, 3)), h.amax((2, 3))], 1))


class FineTune(nn.Module):
    def __init__(self, cin, ncls):
        super().__init__()
        import timm
        self.m = timm.create_model("resnet18.a1_in1k", pretrained=True, num_classes=ncls)
        cfg = self.m.pretrained_cfg
        self.register_buffer("mean", torch.tensor(cfg["mean"]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(cfg["std"]).view(1, 3, 1, 1))

    def forward(self, x):
        if x.shape[1] == 1:
            x = x.repeat(1, 3, 1, 1)
        x = F.interpolate(x, size=(112, 224), mode="nearest")
        return self.m((x - self.mean) / self.std)


def augment(x):
    if x.shape[-1] >= 64 and x.shape[-2] != x.shape[-1]:  # windowed time-axis renderings
        s = int(np.random.randint(-4, 5))
        x = torch.roll(x, s, dims=-1)
    return x


def train_eval(Xtr, ytr, Xte, ncls, finetune=False, epochs=None, bs=256):
    torch.manual_seed(0)
    np.random.seed(0)
    model = (FineTune if finetune else SmallCNN)(Xtr.shape[1], ncls).to(DEV)
    if finetune:
        bs = 32
    per_ep = int(np.ceil(len(Xtr) / bs))
    epochs = epochs or int(min(100, max(6 if finetune else 15, np.ceil(MIN_STEPS / per_ep))))
    if finetune:
        head = [p for n, p in model.named_parameters() if n.startswith("m.fc")]
        body = [p for n, p in model.named_parameters() if not n.startswith("m.fc")]
        opt = torch.optim.AdamW([{"params": body, "lr": 1e-4}, {"params": head, "lr": 3e-4}], weight_decay=1e-4)
    else:
        opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-3)
    steps = epochs * int(np.ceil(len(Xtr) / bs))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[g["lr"] for g in opt.param_groups], total_steps=steps)
    cw = torch.tensor(len(ytr) / (ncls * np.maximum(np.bincount(ytr, minlength=ncls), 1)), dtype=torch.float32,
                      device=DEV)
    Xt = torch.from_numpy(Xtr)
    yt = torch.from_numpy(ytr).long()
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(perm), bs):
            idx = perm[i:i + bs]
            xb = augment(Xt[idx].to(DEV).float() / 255.0)
            loss = F.cross_entropy(model(xb), yt[idx].to(DEV), weight=cw)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
    model.eval()
    probs = []
    with torch.no_grad():
        for i in range(0, len(Xte), 256):
            probs.append(F.softmax(model(torch.from_numpy(Xte[i:i + 256]).to(DEV).float() / 255.0), 1).cpu().numpy())
    return model, np.concatenate(probs)


def saliency(model, X, y, ncls):
    """Mean |d logit_y / d input| per class (grad-x-input, rectified), native image shape."""
    model.eval()
    out = np.zeros((ncls,) + X.shape[1:], np.float32)
    cnt = np.zeros(ncls)
    for i in range(0, len(X), 128):
        xb = (torch.from_numpy(X[i:i + 128]).to(DEV).float() / 255.0).requires_grad_(True)
        lg = model(xb)
        yb = torch.from_numpy(y[i:i + 128]).long().to(DEV)
        lg.gather(1, yb[:, None]).sum().backward()
        g = (xb.grad * xb).clamp(min=0).detach().cpu().numpy()
        for c in range(ncls):
            out[c] += g[y[i:i + 128] == c].sum(0)
            cnt[c] += (y[i:i + 128] == c).sum()
    return out / np.maximum(cnt, 1)[:, None, None, None]


def run(name, rendering, finetune=False):
    kind = "ft2-resnet18" if finetune else "cnnv2"
    if already_logged(name, f"img-{kind}-{rendering}"):
        return
    recs = get_task(name)
    src = SOURCE[name]
    x, song, pos, item_id = get(src, rendering)
    idx_of = {i: k for k, i in enumerate(item_id)}
    rid = np.array([idx_of[r["item_id"]] for r in recs])  # task song -> source song index
    y_str = labels(recs)
    classes = np.unique(y_str)
    y = np.searchsorted(classes, y_str)
    by_song = {}
    for k in crop_subset(song, MAX_CROPS.get(src)):  # anthology: every other window (GPU is shared)
        by_song.setdefault(song[k], []).append(k)
    crop_idx = [np.array(by_song[s]) for s in rid]
    pred = np.empty(len(recs), dtype=object)
    oof_crop = np.zeros((len(x), len(classes)), np.float32)
    sal = np.zeros((len(classes),) + x.shape[1:], np.float32)
    t0 = time.time()
    for f, (tr, te) in enumerate(folds(recs)):
        ci_tr = np.concatenate([crop_idx[i] for i in tr])
        yc_tr = np.concatenate([[y[i]] * len(crop_idx[i]) for i in tr])
        ci_te = np.concatenate([crop_idx[i] for i in te])
        model, p = train_eval(x[ci_tr], yc_tr, x[ci_te], len(classes), finetune)
        oof_crop[ci_te] = p
        o = 0
        for i in te:
            n = len(crop_idx[i])
            pred[i] = classes[p[o:o + n].mean(0).argmax()]
            o += n
        if not finetune:
            yc_te = np.concatenate([[y[i]] * len(crop_idx[i]) for i in te])
            sal += saliency(model, x[ci_te], yc_te, len(classes)) / 5
    np.savez_compressed(IMG / f"{kind}_oof_{name}_{rendering}.npz", prob=oof_crop, song=song, pos=pos,
                        classes=classes, rid=rid, sal=sal)
    log_result(f"img-{kind}-{rendering}", "image", name, y_str, pred,
               notes=("ImageNet resnet18 fine-tuned, bs 32, max(6 ep, 300 steps)" if finetune else "small CNN from scratch, max(15 ep, 300 steps)") +
               f" on crops, song = mean crop softmax; {time.time() - t0:.0f}s")


def ensemble(name, renderings, kind="cnnv2"):
    """Late fusion: average the out-of-fold song-level probabilities of several renderings' CNNs (no refit)."""
    exp = f"img-{kind}-ens[{'+'.join(renderings)}]"
    if already_logged(name, exp):
        return
    recs = get_task(name)
    y_str = labels(recs)
    tot = None
    for rd in renderings:
        z = np.load(IMG / f"{kind}_oof_{name}_{rd}.npz", allow_pickle=True)
        prob, song, rid, classes = z["prob"], z["song"], z["rid"], z["classes"]
        ev = prob.sum(1) > 0
        sums = np.zeros((song.max() + 1, prob.shape[1]))
        np.add.at(sums, song[ev], prob[ev])
        cnt = np.bincount(song[ev], minlength=song.max() + 1)[:, None]
        p = (sums / np.maximum(cnt, 1))[rid]
        tot = p if tot is None else tot + p
    log_result(exp, "image", name, y_str, classes[tot.argmax(1)], notes="mean of per-rendering OOF song probs")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="T15,T5,E,E5prior,A5")
    ap.add_argument("--renderings", default="roll,contour,jianpu,ssm,itrans")
    ap.add_argument("--finetune", default="")
    ap.add_argument("--ensemble", action="store_true", help="late-fuse the listed renderings' saved OOF probs")
    a = ap.parse_args()
    if a.ensemble:
        for t in a.tasks.split(","):
            ensemble(t, a.renderings.split(","))
        sys.exit()
    for t in a.tasks.split(","):
        if a.finetune:
            run(t, a.finetune, finetune=True)
        else:
            for rd in a.renderings.split(","):
                run(t, rd)
