"""
Family "image", step 5: what the images reveal. Reads the out-of-fold crop probabilities + saliency saved by
exp_image_cnn.py and prints / plots:
  1. crop position vs crop-level accuracy (which part of a song — opening, middle, ending — is most regional);
  2. jianpu saliency per class, summed over time -> which scale degrees (and octaves) drive each region's decision,
     next to the class's mean degree occupancy (saliency/occupancy > 1 = the degree is used as evidence beyond its
     frequency);
  3. itrans saliency per class -> most decisive (interval_i, interval_i+1) pairs;
  4. the most confidently correct jianpu crop per class (figure).
Figures -> notebooks/figures/regionclf_image_*.png

Run (arm64 env):
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_explain.py [--tasks A5,T5,E5prior]
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import ROOT  # noqa: E402
from regionclf.exp_image_frozen import SOURCE  # noqa: E402
from regionclf.exp_image_render import IMG, _cjk, get  # noqa: E402

FIG = ROOT / "notebooks" / "figures"
DEG = ["do", "#do", "re", "#re", "mi", "fa", "#fa", "sol", "#sol", "la", "#la", "ti"]


def load_oof(name, rd, kind="cnnv2"):
    f = IMG / f"{kind}_oof_{name}_{rd}.npz"
    return np.load(f, allow_pickle=True) if f.exists() else None


def crop_labels(z):
    """Per-crop true class index (via rid: task song -> source song) and mask of evaluated crops."""
    classes, rid = z["classes"], z["rid"]
    return classes, rid


def position_analysis(name, rd, y_of_source_song):
    z = load_oof(name, rd)
    if z is None:
        return None
    prob, song, pos = z["prob"], z["song"], z["pos"]
    ev = prob.sum(1) > 0
    yt = np.array([y_of_source_song.get(s, -1) for s in song])
    ok = ev & (yt >= 0)
    correct = prob.argmax(1) == yt
    bins = np.digitize(pos, [0.2, 0.45, 0.7, 0.95])  # opening, early-mid, late-mid, pre-ending, ending
    out = {b: (correct[ok & (bins == b)].mean(), (ok & (bins == b)).sum()) for b in range(5)}
    return out


def main(tasks):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from regionclf.exp_image_frozen import get_task
    fp = _cjk()
    for name in tasks:
        recs = get_task(name)
        src = SOURCE[name]
        print(f"\n===== {name}")
        # 1. position analysis
        for rd in ("jianpu", "roll", "contour", "ssm"):
            z = load_oof(name, rd)
            if z is None:
                continue
            classes = list(z["classes"])
            _, _, _, item_id = get(src, rd)
            idx = {i: k for k, i in enumerate(item_id)}
            ymap = {idx[r["item_id"]]: classes.index(r["region"]) for r in recs}
            res = position_analysis(name, rd, ymap)
            print(f"  crop accuracy by position [{rd}]: " +
                  "  ".join(f"{lab} {a:.3f} (n={n})" for lab, (a, n) in
                            zip(["open", "early", "mid", "late", "end"], res.values())))
        # 2. jianpu saliency by degree
        z = load_oof(name, "jianpu")
        if z is not None:
            classes = list(z["classes"])
            sal = z["sal"]  # (ncls, 3, 12, 64)
            x, song, _, item_id = get(src, "jianpu")
            idx = {i: k for k, i in enumerate(item_id)}
            ymap = {idx[r["item_id"]]: classes.index(r["region"]) for r in recs}
            yc = np.array([ymap.get(s, -1) for s in song])
            occ = np.stack([(x[yc == c] > 0).mean((0, 3)) for c in range(len(classes))])  # (ncls, 3, 12)
            s_deg = sal.sum(3)  # (ncls, 3, 12); row 0 = ti ... row 11 = do
            s_deg = s_deg[:, :, ::-1]
            occ = occ[:, :, ::-1]
            s_tot = s_deg.sum(1)
            s_tot = s_tot / s_tot.sum(1, keepdims=True)
            o_tot = occ.sum(1) / occ.sum((1, 2))[:, None]
            print("  jianpu saliency share by degree (top 4; ratio = saliency share / occupancy share):")
            for c, cl in enumerate(classes):
                top = np.argsort(-s_tot[c])[:4]
                oct_share = s_deg[c].sum(1) / s_deg[c].sum()
                print(f"    {cl:12s} " + ", ".join(f"{DEG[d]} {s_tot[c, d]:.2f} (x{s_tot[c, d] / max(o_tot[c, d], 1e-9):.2f})"
                                                   for d in top) +
                      f" | octave low/mid/high {oct_share[0]:.2f}/{oct_share[1]:.2f}/{oct_share[2]:.2f}")
            fig, ax = plt.subplots(1, 2, figsize=(12, 0.5 * len(classes) + 2))
            for a, M, t in ((ax[0], o_tot, "occupancy share"), (ax[1], s_tot, "saliency share (grad x input)")):
                a.imshow(M, cmap="viridis", aspect="auto")
                a.set_xticks(range(12)); a.set_xticklabels(DEG, rotation=45)
                a.set_yticks(range(len(classes))); a.set_yticklabels(classes, fontproperties=fp)
                a.set_title(f"{name} jianpu CNN: {t}")
            fig.tight_layout(); fig.savefig(FIG / f"regionclf_image_saliency_{name}.png", dpi=110); plt.close(fig)
            # 4. most confident correct crop per class
            prob = z["prob"]
            fig, axes = plt.subplots(len(classes), 1, figsize=(7, 1.3 * len(classes)))
            for c, cl in enumerate(classes):
                m = (yc == c) & (prob.argmax(1) == c)
                if not m.any():
                    continue
                k = np.where(m)[0][np.argmax(prob[m, c])]
                axes[c].imshow(np.transpose(x[k], (1, 2, 0)), aspect="auto")
                axes[c].set_yticks(range(12)); axes[c].set_yticklabels(DEG[::-1], fontsize=5)
                axes[c].set_xticks([])
                axes[c].set_ylabel(cl, fontproperties=fp, rotation=0, ha="right")
                axes[c].set_title(f"p={prob[k, c]:.2f} {item_id[song[k]]}", fontsize=7, fontproperties=fp)
            fig.tight_layout(); fig.savefig(FIG / f"regionclf_image_topcrops_{name}.png", dpi=110); plt.close(fig)
        # 3. itrans saliency
        z = load_oof(name, "itrans")
        if z is not None:
            classes = list(z["classes"])
            sal = z["sal"][:, 0]  # interval-pair channel (ncls, 25, 25)
            print("  itrans: most salient (interval_i, interval_i+1) pairs, semitones:")
            for c, cl in enumerate(classes):
                flat = np.argsort(-sal[c].ravel())[:4]
                print(f"    {cl:12s} " + ", ".join(f"({i // 25 - 12:+d},{i % 25 - 12:+d})" for i in flat))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="A5,T5,E5prior")
    main(ap.parse_args().tasks.split(","))
