"""
Confusion matrix of the region classifier with the three region groups outlined.

Groups come from the region-profile clustering (src/analysis/recordings/region_profiles.py, Ward, k = 3): a highland / steppe / southwest
group, Xinjiang alone, and the eastern and southern Han regions. Regions are ordered by that clustering, so each group is a
block on the diagonal. Besides the matrix, the script reports how often a recording is guessed to be in its OWN group, which
is a more forgiving and more stable question than guessing the exact region.

Input: data/analysis/recordings/classifier/oof_predictions.csv (out-of-fold predictions of the best model, from region_classifier.py).
Output: data/analysis/recordings/classifier/fig_confusion_blocks.png and block_summary.csv.
Limits: the groups were found from the same recordings (a mild circularity: the grouping uses the average profile of each
region, not the single-recording predictions); one model, one run; regions have 56-95 recordings. Exploratory only.
Run (from the repo root):  python src/analysis/recordings/confusion_blocks.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import fcluster, leaves_list, linkage

from scales_by_region import OUT_ROOT, INK, MUTED, style

ORANGE = "#eb6834"


def main() -> None:
    prof = pd.read_csv(OUT_ROOT / "profiles" / "region_profile.csv", index_col=0)
    z = prof[[c for c in prof.columns if c.startswith("z_")]].to_numpy()
    link = linkage(z, "ward")
    order = leaves_list(link)
    lab = fcluster(link, 3, "maxclust")
    regions = prof.index.to_numpy()
    names = regions[order]
    groups = lab[order]
    # name each group by its content
    block_name = {}
    for g in dict.fromkeys(groups):
        mem = names[groups == g]
        block_name[g] = "Xinjiang" if (len(mem) == 1 and mem[0] == "Xinjiang") else (
            "Highland, steppe and southwest" if "Tibetan" in mem else "Eastern and southern Han")

    o = pd.read_csv(OUT_ROOT / "classifier" / "oof_predictions.csv")
    idx = {r: i for i, r in enumerate(names)}
    K = len(names)
    C = np.zeros((K, K))
    np.add.at(C, (o.true.map(idx).to_numpy(), o.predicted.map(idx).to_numpy()), 1)
    M = C / C.sum(1, keepdims=True) * 100

    # blocks: contiguous runs of the same group along the order
    spans = []
    start = 0
    for i in range(1, K + 1):
        if i == K or groups[i] != groups[start]:
            spans.append((start, i - 1, block_name[groups[start]]))
            start = i
    rows = []
    for a, b, nm in spans:
        inside = C[a:b + 1, a:b + 1].sum()
        total = C[a:b + 1].sum()
        predicted_there = C[:, a:b + 1].sum() / C.sum()
        rows.append({"group": nm, "regions": b - a + 1, "recordings": int(total), "guessed_inside_own_group": inside / total,
                     "guessed_exact_region": np.trace(C[a:b + 1, a:b + 1]) / total, "share_of_all_guesses_in_group": predicted_there})
    summ = pd.DataFrame(rows)
    summ.to_csv(OUT_ROOT / "classifier" / "block_summary.csv", index=False)

    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0d2f5c"])
    fig, ax = plt.subplots(figsize=(10.4, 8.8))
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=max(M.max(), 1))
    for i in range(K):
        for j in range(K):
            if M[i, j] >= 8:
                ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7.5, color="white" if M[i, j] > 0.55 * M.max() else INK)
    for (a, b, nm), r in zip(spans, rows):
        ax.add_patch(Rectangle((a - 0.5, a - 0.5), b - a + 1, b - a + 1, fill=False, edgecolor=ORANGE, lw=2.4, zorder=5))
        ax.text(K - 0.35, (a + b) / 2, f"{nm}\n{r['guessed_inside_own_group'] * 100:.0f}% guessed inside the group\n"
                f"({r['share_of_all_guesses_in_group'] * 100:.0f}% of all guesses land there)", va="center", ha="left", fontsize=8.5, color=INK)
    ax.set_xticks(range(K), names, rotation=45, ha="right", fontsize=8.5, color=INK)
    ax.set_yticks(range(K), names, fontsize=8.5, color=INK)
    ax.set_xlabel("Predicted region", color=MUTED, fontsize=9)
    ax.set_ylabel("True region", color=MUTED, fontsize=9)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, cax=fig.add_axes([0.36, 0.07, 0.26, 0.014]), orientation="horizontal")
    cb.set_label("% of the true region's recordings", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle("The classifier mostly confuses regions within their own group", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Rows = true region, columns = guessed region; numbers shown when 8% or more (random guessing gives about 7%). "
             "Orange boxes = region groups.", color=MUTED, fontsize=8.5)
    fig.subplots_adjust(left=0.2, right=0.72, top=0.89, bottom=0.27)
    fig.savefig(OUT_ROOT / "classifier" / "fig_confusion_blocks.png", dpi=160, facecolor="white")
    plt.close(fig)
    pd.set_option("display.width", 200)
    print(summ.round(3).to_string(index=False))
    print("regions in order:", list(names))


if __name__ == "__main__":
    main()
