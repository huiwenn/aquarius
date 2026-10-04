"""
Family "image", step 2: frozen pretrained vision-backbone embeddings of every rendered crop (MPS).

Backbones: resnet50 (timm resnet50.a1_in1k, 2048-d), dinov2 (timm vit_small_patch14_dinov2.lvd142m, 384-d),
clip (open_clip ViT-B-32 laion2b_s34b_b79k image tower, 512-d). Rendered images are upscaled (nearest) to 224x224,
1-channel renderings are repeated to RGB, then normalized with the backbone's mean/std.
Output: data/regionclf/img/emb_<backbone>_<source>_<rendering>.npy (float16, one row per embedded image; for anthology
only every other window per song is embedded, see crop_subset/MAX_CROPS).

Run (arm64 env):
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_embed.py \
      [--backbones resnet50,dinov2,clip] [--sources anthology,essen,trans_primary] [--renderings roll,...]
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.exp_image_render import IMG, RENDERINGS, SOURCES, get  # noqa: E402

torch.set_num_threads(2)
DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
TIMM = {"resnet50": "resnet50.a1_in1k", "dinov2": "vit_small_patch14_dinov2.lvd142m",
        "dinov2b": "vit_base_patch14_dinov2.lvd142m", "resnet18": "resnet18.a1_in1k"}


def load_backbone(name):
    if name == "clip":
        import open_clip
        m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        mean, std = (0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)
        f = m.visual
    else:
        import timm
        kw = {"img_size": 224} if "dinov2" in name else {}
        f = timm.create_model(TIMM[name], pretrained=True, num_classes=0, **kw)
        cfg = f.pretrained_cfg
        mean, std = cfg["mean"], cfg["std"]
    return f.eval().to(DEV), torch.tensor(mean).view(1, 3, 1, 1).to(DEV), torch.tensor(std).view(1, 3, 1, 1).to(DEV)


MAX_CROPS = {"anthology": 2}  # GPU is shared: keep every other window for the 8.6k anthology songs


def crop_subset(song: np.ndarray, max_crops=None) -> np.ndarray:
    """Indices of the images that get embedded (all, or every other window per song)."""
    if not max_crops:
        return np.arange(len(song))
    rank = np.zeros(len(song), int)
    for i in range(1, len(song)):
        rank[i] = rank[i - 1] + 1 if song[i] == song[i - 1] else 0
    return np.where(rank % 2 == 0)[0]


def to_input(xb: np.ndarray, mean, std, size=224):
    x = torch.from_numpy(xb).to(DEV).float() / 255.0
    if x.shape[1] == 1:
        x = x.repeat(1, 3, 1, 1)
    x = F.interpolate(x, size=(size, size), mode="nearest")
    return (x - mean) / std


@torch.no_grad()
def embed(name, source, rendering, bs=64, force=False):
    out = IMG / f"emb_{name}_{source}_{rendering}.npy"
    if out.exists() and not force:
        return out
    model, mean, std = load_backbone(name)
    x, song, *_ = get(source, rendering)
    sel = crop_subset(song, MAX_CROPS.get(source))
    x = x[sel]
    t0 = time.time()
    feats = []
    for i in range(0, len(x), bs):
        feats.append(model(to_input(x[i:i + bs], mean, std)).float().cpu().numpy().astype(np.float16))
    np.save(out, np.concatenate(feats))
    print(f"{name}/{source}/{rendering}: {len(x)} imgs in {time.time() - t0:.0f}s", flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbones", default="dinov2,resnet50,clip")
    ap.add_argument("--sources", default="trans_primary,essen,anthology")
    ap.add_argument("--renderings", default=",".join(RENDERINGS))
    a = ap.parse_args()
    for s in a.sources.split(","):
        for b in a.backbones.split(","):
            for r in a.renderings.split(","):
                embed(b, s, r)
