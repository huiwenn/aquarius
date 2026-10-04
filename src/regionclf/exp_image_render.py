"""
Family "image", step 1: render every song into tonic- and tempo-normalized images (cached as uint8 arrays).

Normalization (shared by all renderings)
  pitch  宫 (do pitch class) = features.estimate_gong; the register reference `do0` is the do-pitch closest to the
         song's median pitch, so y = semitones relative to a do near the middle of the tessitura. Works for
         anthology (1=C), Essen (real keys) and transcriptions (absolute sung pitch) alike.
  time   onsets/durations divided by the song's median inter-onset interval (IOI) -> tempo-free "median notes".

Renderings (name: shape per image; several images ("crops") per song for the windowed ones)
  roll     piano roll crop, 37 rows (-18..+18 st from do0) x 64 cols (0.5 median-IOI per col, 32 median notes per
           crop); onset column = 255, sustain = 150.                                 1x37x64, K windows
  contour  melodic contour line plot over note index (rhythm-free): 48 consecutive notes drawn as a 2-px polyline
           on a 37x96 canvas.                                                        1x37x96, K windows
  jianpu   scale-degree x time ("jianpu-like"): 12 rows = degree relative to 宫 (row 0 = do at the bottom),
           3 channels = octave (below / middle / above do0); same time grid as roll.  3x12x64, K windows
  ssm      self-similarity of a 96-note window: R = same relative pitch, G = same next interval,
           B = same 3-note degree n-gram (repeated phrases show up as diagonals).    3x96x96, K windows
  itrans   whole-song 2D transition heatmaps: R = (interval_i, interval_i+1) ±12 st, G = (interval_i,
           log2 duration ratio_i) , B = 12x12 degree transition upsampled; sqrt-scaled.  3x25x25, 1 per song
MFDMap (Khoo, Man & Cao 2012; Khoo 2013 thesis) is a 1-D vector, not an image; it lives in exp_image_mfdmap.py.

Windows: K evenly spaced windows over the song (K=4 for scores, 8 for transcriptions, which are ~5x longer).

Cache: data/regionclf/img/<source>_<rendering>.npz with `x` (n_images, C, H, W) uint8, `song` (n_images,) song
index into the corpus pickle order, `pos` (n_images,) relative window position in [0,1], `item_id` per song.

Run (arm64 env, PYTHONNOUSERSITE=1 because ~/.local holds x86 wheels):
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_render.py
  ... --preview   # also writes notebooks/figures/regionclf_image_renderings.png (one song per region & rendering)
"""

import argparse
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")  # shared machine: cap BLAS threads (set before numpy is imported)

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import D, load  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402

IMG = D / "img"
SOURCES = {"anthology": 4, "essen": 4, "trans_primary": 8}
RENDERINGS = ["roll", "contour", "jianpu", "ssm", "itrans"]
PR = 18  # pitch half-range in semitones


def normalize(notes: np.ndarray):
    """Return (t, d, rel, deg): time/dur in median-IOI units, pitch rel. to do0, degree rel. to 宫 (0..11)."""
    pitch = notes[:, 2].astype(int)
    gong = estimate_gong(notes)
    med = np.median(pitch)
    cands = np.arange(0, 128)[np.arange(0, 128) % 12 == gong]
    do0 = cands[np.argmin(np.abs(cands - med))]
    ioi = np.diff(notes[:, 0])
    ioi = ioi[ioi > 1e-6]
    m = np.median(ioi) if len(ioi) else 1.0
    t = (notes[:, 0] - notes[0, 0]) / m
    d = notes[:, 1] / m
    rel = pitch - do0
    return t, d, rel, (pitch - gong) % 12


def already_logged(task_name: str, experiment: str) -> bool:
    """True if results.csv already has this (task, experiment) row for family image (lets queues resume)."""
    import pandas as pd
    from regionclf.common import RESULTS
    if not RESULTS.exists():
        return False
    df = pd.read_csv(RESULTS, usecols=["experiment", "family", "task"])
    return bool(((df.family == "image") & (df.task == task_name) & (df.experiment == experiment)).any())


def window_starts(total: float, win: float, k: int) -> np.ndarray:
    if total <= win:
        return np.zeros(1)
    return np.linspace(0, total - win, k)


def _roll_grid(t, d, rows, n_rows, start, cols=64, res=0.5, chan=None, n_chan=1):
    img = np.zeros((n_chan, n_rows, cols), np.uint8)
    for ti, di, r, c in zip(t, d, rows, chan if chan is not None else np.zeros(len(t), int)):
        a = (ti - start) / res
        b = (ti + di - start) / res
        if b <= 0 or a >= cols:
            continue
        a0, b0 = max(int(np.floor(a)), 0), min(int(np.ceil(b)), cols)
        img[c, r, a0:b0] = np.maximum(img[c, r, a0:b0], 150)
        if a >= 0:
            img[c, r, int(a)] = 255
    return img


def render_roll(notes, k):
    t, d, rel, _ = normalize(notes)
    rows = PR - np.clip(rel, -PR, PR)  # high pitch at top
    starts = window_starts(t[-1] + d[-1], 32.0, k)
    return [_roll_grid(t, d, rows, 2 * PR + 1, s) for s in starts], starts / max(t[-1], 1e-9)


def render_jianpu(notes, k):
    t, d, rel, deg = normalize(notes)
    rows = 11 - deg  # do at the bottom row
    octv = np.where(rel < 0, 0, np.where(rel < 12, 1, 2))
    starts = window_starts(t[-1] + d[-1], 32.0, k)
    return [_roll_grid(t, d, rows, 12, s, chan=octv, n_chan=3) for s in starts], starts / max(t[-1], 1e-9)


def _line(img, x0, y0, x1, y1, val=255):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    xs = np.linspace(x0, x1, n).round().astype(int)
    ys = np.linspace(y0, y1, n).round().astype(int)
    h, w = img.shape
    for dy in (0, 1):  # 2-px thick
        ok = (xs >= 0) & (xs < w) & (ys + dy >= 0) & (ys + dy < h)
        img[ys[ok] + dy, xs[ok]] = val


def render_contour(notes, k, win=48, width=96):
    _, _, rel, _ = normalize(notes)
    y = PR - np.clip(rel, -PR, PR)
    starts = np.linspace(0, max(len(rel) - win, 0), k).astype(int) if len(rel) > win else np.zeros(1, int)
    out = []
    for s in starts:
        seg = y[s:s + win]
        img = np.zeros((2 * PR + 1, width), np.uint8)
        xs = np.arange(len(seg)) * (width - 1) / (win - 1)
        for i in range(len(seg) - 1):
            _line(img, xs[i], seg[i], xs[i + 1], seg[i + 1])
        out.append(img[None])
    return out, starts / max(len(rel), 1)


def render_ssm(notes, k, win=96):
    _, _, rel, deg = normalize(notes)
    iv = np.r_[np.diff(rel), 99]
    starts = np.linspace(0, max(len(rel) - win, 0), k).astype(int) if len(rel) > win else np.zeros(1, int)
    out = []
    for s in starts:
        r, v, g = rel[s:s + win], iv[s:s + win], deg[s:s + win]
        n = len(r)
        img = np.zeros((3, win, win), np.uint8)
        img[0, :n, :n] = (r[:, None] == r[None, :]) * 255
        img[1, :n, :n] = (v[:, None] == v[None, :]) * 255
        if n >= 3:
            tri = g[:-2] * 144 + g[1:-1] * 12 + g[2:]
            img[2, :n - 2, :n - 2] = (tri[:, None] == tri[None, :]) * 255
        out.append(img)
    return out, starts / max(len(rel), 1)


def render_itrans(notes, k=1):
    t, d, rel, deg = normalize(notes)
    iv = np.clip(np.diff(rel), -12, 12) + 12
    img = np.zeros((3, 25, 25))
    if len(iv) > 1:
        np.add.at(img[0], (iv[:-1], iv[1:]), 1)
    dr = np.log2(np.maximum(d[1:], 1e-3) / np.maximum(d[:-1], 1e-3))
    drb = np.clip(np.round(dr * 4), -12, 12).astype(int) + 12
    np.add.at(img[1], (iv, drb), 1)
    tm = np.zeros((12, 12))
    np.add.at(tm, (deg[:-1], deg[1:]), 1)
    up = np.kron(tm, np.ones((2, 2)))
    img[2, :24, :24] = up
    for c in range(3):
        img[c] = np.sqrt(img[c] / max(img[c].max(), 1e-9))
    return [(img * 255).astype(np.uint8)], np.zeros(1)


RENDER = {"roll": render_roll, "contour": render_contour, "jianpu": render_jianpu, "ssm": render_ssm,
          "itrans": render_itrans}


def build(source: str, rendering: str, force: bool = False) -> Path:
    path = IMG / f"{source}_{rendering}.npz"
    if path.exists() and not force:
        return path
    recs = load(source)
    k = SOURCES[source]
    xs, song, pos = [], [], []
    for i, r in enumerate(recs):
        imgs, p = RENDER[rendering](r["notes"], k)
        xs += imgs
        song += [i] * len(imgs)
        pos += list(np.clip(p, 0, 1))
    IMG.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, x=np.stack(xs), song=np.array(song), pos=np.array(pos, np.float32),
                        item_id=np.array([r["item_id"] for r in recs]))
    print(f"{source}/{rendering}: {len(xs)} images for {len(recs)} songs, shape {xs[0].shape}", flush=True)
    return path


def get(source: str, rendering: str):
    z = np.load(build(source, rendering))
    return z["x"], z["song"], z["pos"], z["item_id"]


def preview():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from regionclf.common import A5_REGIONS
    recs = load("anthology")
    rng = np.random.RandomState(1)
    fig, axes = plt.subplots(len(A5_REGIONS), len(RENDERINGS), figsize=(16, 11))
    for i, reg in enumerate(A5_REGIONS):
        cand = [r for r in recs if r["region"] == reg and 60 < len(r["notes"]) < 120]
        r = cand[rng.randint(len(cand))]
        for j, name in enumerate(RENDERINGS):
            img = RENDER[name](r["notes"], 4)[0][0]
            show = img[0] if img.shape[0] == 1 else np.transpose(img, (1, 2, 0))
            axes[i, j].imshow(show, aspect="auto", cmap="magma", origin="upper" if name != "jianpu" else "upper")
            axes[i, j].set_xticks([]); axes[i, j].set_yticks([])
            if i == 0:
                axes[i, j].set_title(name)
            if j == 0:
                axes[i, j].set_ylabel(r["item_id"].split("/")[0] + "\n" + reg, fontproperties=_cjk())
    fig.tight_layout()
    out = D.parents[1] / "notebooks" / "figures" / "regionclf_image_renderings.png"
    fig.savefig(out, dpi=110)
    print("wrote", out)


def _cjk():
    from matplotlib.font_manager import FontProperties
    for f in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc",
              "/Library/Fonts/Arial Unicode.ttf"]:
        if Path(f).exists():
            return FontProperties(fname=f)
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=",".join(SOURCES))
    ap.add_argument("--renderings", default=",".join(RENDERINGS))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    if a.preview:
        preview()
    for s in a.sources.split(","):
        for rd in a.renderings.split(","):
            build(s, rd, a.force)
