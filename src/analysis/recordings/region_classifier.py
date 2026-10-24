"""
Song-level region classifier: can the region of a recording be predicted from its melody, scale, intonation and rhythm?

Protocol (the project's strict protocol, docs/region_classification.md section 22):
  - musical features only: no channel, genre, place, title or any other metadata goes into a model
  - folds are the repo's evaluation folds (`add_folds` in src/colour_regions/build_release.py: stratified by region, grouped by
    channel and singer components, 5 folds), computed here from metadata/recordings.csv because the public table has no `fold`
  - each training set also drops every recording whose song (`song_key`) appears in the test fold
  - no hyper-parameter tuning on the test folds: settings are fixed in advance (LR C = 0.1, GBM depth 3, 200 rounds)
Data: core recordings with all four analyses (scales, intonation, rhythm, melody; 15 regions).
Feature sets:  A = the 12 interpretable region-profile features;  B = A plus the pitch-class profile relative to the final
note, the interval histogram, contour shares and the remaining rhythm/intonation measures (no recording-condition
measures such as tuning offset, drift, or length).
Models: multinomial logistic regression (LR) and histogram gradient boosting (GBM), both with balanced class weights;
missing values are filled with the training median.
Metrics: macro-F1 (mean of the 15 per-region F1 scores), accuracy, top-3 accuracy; 95% intervals resample whole groups.
References: stratified random guessing, the majority class, and a place-only diagnostic (k-nearest neighbours on
longitude/latitude: NOT a musical model; it shows how much geography alone gives).
Also: one-family-only and one-family-left-out runs (LR on B), permutation importance of the 12 A features, per-fold scores,
the confusion matrix and the most confused region pairs against their distance.

Limits: 15 regions, about 1,170 recordings, and one channel (group 0, the Musical Map of China series) holds about a quarter
of them, so fold 0 is dominated by it; features are automatic transcriptions; this predicts the label of this corpus, which
is built from regional playlists and so mixes music with source habits that the grouping only partly removes.
Exploratory only.
Run (from the repo root):  python src/analysis/recordings/region_classifier.py [--out data/analysis/recordings/classifier]
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from region_profiles import FEATURES, haversine
from scales_by_region import GRID, OUT_ROOT, INK, MUTED, ROOT, style

sys.path.insert(0, str(ROOT / "src"))
from colour_regions.build_release import add_folds  # noqa: E402

BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
N_BOOT = 1000
FAMILY_COLS = {
    "scales": ["penta_coverage", "bian_share", "scale_size", "pc_entropy"] + [f"rel_final_{k}" for k in range(12)],
    "intonation": ["off_grid_share", "off_grid_local", "mean_abs_dev", "grid_R"],
    "rhythm": ["note_rate", "median_ioi", "isochrony", "tempo_variation", "rest_share", "long_note_share"],
    "melody": ["range_90", "mean_abs_interval", "repeat_share", "step_share", "third_share", "leap_share",
               "over_octave_share", "up_share", "phrase_net_change", "phrase_notes_median"]
              + [f"contour_{f}" for f in ("arch", "descending", "ascending", "concave", "level")] + [f"int_{k}" for k in range(13)],
}
SET_A = list(FEATURES)
SET_B = [c for cols in FAMILY_COLS.values() for c in cols]


def load() -> pd.DataFrame:
    rec = pd.read_csv(ROOT / "metadata" / "recordings.csv")
    rec["fold"] = add_folds(rec)  # folds are made on the whole corpus, as in the release, then restricted to core
    rec = rec[rec.core][["item_id", "region_en", "region_type", "group_id", "fold", "song_key", "lon", "lat", "geo_level"]]
    d = rec
    for fam, cols in FAMILY_COLS.items():
        t = pd.read_csv(OUT_ROOT / {"scales": "scales", "intonation": "intonation", "rhythm": "rhythm", "melody": "melody"}[fam]
                        / "per_recording.csv")
        have = [c for c in cols if c in t.columns]
        assert len(have) == len(cols), (fam, set(cols) - set(have))
        d = d.merge(t[["item_id"] + cols], on="item_id", how="inner", suffixes=("", f"_{fam}"))
    d = d.reset_index(drop=True)  # gaps in any feature (e.g. contour needs >= 3 phrases) are filled by the imputer
    d["song_key"] = d.song_key.fillna(d.item_id)
    return d


def make_model(kind: str):
    if kind == "LR":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(C=0.1, class_weight="balanced", max_iter=3000))
    if kind == "GBM":
        return make_pipeline(SimpleImputer(strategy="median"),
                             HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                                            class_weight="balanced", random_state=0))
    return KNeighborsClassifier(n_neighbors=7)  # place-only diagnostic


def splits(d: pd.DataFrame):
    for f in sorted(d.fold.unique()):
        te = d.fold == f
        songs = set(d.loc[te, "song_key"])
        tr = (~te) & (~d.song_key.isin(songs))
        yield f, np.flatnonzero(tr), np.flatnonzero(te)


def oof(d: pd.DataFrame, cols: list[str], kind: str, classes: np.ndarray, X=None):
    X = d[cols].to_numpy(float) if X is None else X
    y = d.region_en.to_numpy()
    P = np.zeros((len(d), len(classes)))
    for f, tr, te in splits(d):
        m = make_model(kind).fit(X[tr], y[tr])
        proba = m.predict_proba(X[te])
        P[np.ix_(te, [list(classes).index(c) for c in m.classes_])] = proba
    return P


def confusion(y, pred, K):
    C = np.zeros((K, K))
    np.add.at(C, (y, pred), 1)
    return C


def macro_f1(C):
    tp = np.diag(C)
    p = tp / np.maximum(C.sum(0), 1e-12)
    r = tp / np.maximum(C.sum(1), 1e-12)
    return np.where(p + r > 0, 2 * p * r / np.maximum(p + r, 1e-12), 0.0)


def boot(y, pred, groups, K, rng):
    """Per-class F1 and macro-F1 with a group bootstrap; returns point estimate, lo, hi arrays."""
    g = pd.factorize(groups)[0]
    G = g.max() + 1
    Cg = np.zeros((G, K, K))
    np.add.at(Cg, (g, y, pred), 1)
    pt = macro_f1(Cg.sum(0))
    bt = np.array([macro_f1(np.tensordot(np.bincount(rng.integers(0, G, G), minlength=G).astype(float), Cg, axes=(0, 0)))
                   for _ in range(N_BOOT)])
    mac = bt.mean(1)
    return (pt, np.percentile(bt, 2.5, 0), np.percentile(bt, 97.5, 0)), (pt.mean(), *np.percentile(mac, [2.5, 97.5]))


def score(d, P, classes, rng, name):
    K = len(classes)
    y = np.searchsorted(classes, d.region_en.to_numpy())
    pred = P.argmax(1)
    (pc, plo, phi), (mf, lo, hi) = boot(y, pred, d.group_id.to_numpy(), K, rng)
    top3 = np.mean([y[i] in np.argsort(-P[i])[:3] for i in range(len(y))])
    return {"model": name, "macro_f1": mf, "lo": lo, "hi": hi, "accuracy": float((pred == y).mean()), "top3": float(top3)}, (pc, plo, phi)


def permutation_importance(d, cols, kind, classes, rng, repeats=5):
    X = d[cols].to_numpy(float)
    y = np.searchsorted(classes, d.region_en.to_numpy())
    K = len(classes)
    base = np.zeros(len(d), int)
    perm = {(j, r): np.zeros(len(d), int) for j in range(len(cols)) for r in range(repeats)}
    for f, tr, te in splits(d):
        m = make_model(kind).fit(X[tr], d.region_en.to_numpy()[tr])
        cl = np.searchsorted(classes, m.classes_)
        base[te] = cl[m.predict_proba(X[te]).argmax(1)]
        for j in range(len(cols)):
            for r in range(repeats):
                Xp = X[te].copy()
                Xp[:, j] = rng.permutation(Xp[:, j])
                perm[(j, r)][te] = cl[m.predict_proba(Xp).argmax(1)]
    b = macro_f1(confusion(y, base, K)).mean()
    rows = []
    for j, c in enumerate(cols):
        drops = [b - macro_f1(confusion(y, perm[(j, r)], K)).mean() for r in range(repeats)]
        rows.append({"feature": c, "label": FEATURES[c][1], "drop_in_macro_f1": np.mean(drops), "sd": np.std(drops)})
    return pd.DataFrame(rows).sort_values("drop_in_macro_f1", ascending=False)


# ---------------------------------------------------------------- figures
def plot_models(m: pd.DataFrame, chance: float, out: Path):
    sections = [("References", ["Stratified random guess", "Majority class", "Place only (longitude/latitude) - not musical"]),
                ("12 interpretable features (A)", ["A + LR", "A + GBM"]),
                ("Extended features (B)", ["B + LR", "B + GBM"]),
                ("Extended (B), LR: one family only", [f"only {f}" for f in FAMILY_COLS]),
                ("Extended (B), LR: one family left out", [f"without {f}" for f in FAMILY_COLS])]
    items, y, heads = [], 0.0, []
    for title, names in sections:
        y += 0.8
        heads.append((y - 0.5, title))
        for n in names:
            r = m[m.model == n]
            if len(r):
                items.append((y, n, r.iloc[0]))
                y += 1
    fig, ax = plt.subplots(figsize=(9.4, 6.9))
    for yy, n, r in items:
        ref = n in sections[0][1]
        c = GRAY if ref else BLUE
        ax.hlines(yy, r.lo, r.hi, color=c, lw=2, zorder=2)
        ax.scatter(r.macro_f1, yy, s=52, color=c, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks([i[0] for i in items], [i[1] for i in items], fontsize=9, color=INK)
    ax.set_ylim(y, 0)
    ax.axvline(chance, color=MUTED, ls=(0, (4, 3)), lw=1)
    ax.text(chance, y + 0.05, " chance", color=MUTED, fontsize=8, va="bottom")
    ax.set_xlabel("Macro-F1 over the 15 regions (mean of per-region F1)", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    for yy, t in heads:
        ax.annotate(t, xy=(0, yy), xycoords=("axes fraction", "data"), xytext=(2, 0), textcoords="offset points",
                    color=MUTED, fontsize=8, weight="bold", va="center")
    fig.suptitle("How well can the region be predicted from the music?", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Strict protocol: new channels and new songs in every test fold. Line = 95% interval resampling channels/singers.",
             color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_confusion(C, order, classes, name, out: Path):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6", "#0d2f5c"])
    M = (C / np.maximum(C.sum(1, keepdims=True), 1))[np.ix_(order, order)] * 100
    fig, ax = plt.subplots(figsize=(9, 7.4))
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=max(M.max(), 1))
    for i in range(len(order)):
        for j in range(len(order)):
            if M[i, j] >= 8:
                ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7.5, color="white" if M[i, j] > 0.55 * M.max() else INK)
    names = [classes[i] for i in order]
    ax.set_xticks(range(len(order)), names, rotation=45, ha="right", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(order)), names, fontsize=8.5, color=INK)
    ax.set_xlabel("Predicted region", color=MUTED, fontsize=9)
    ax.set_ylabel("True region", color=MUTED, fontsize=9)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("% of the true region's recordings", color=MUTED, fontsize=9)
    cb.outline.set_visible(False)
    fig.suptitle(f"What does the classifier confuse? ({name})", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.text(0.02, 0.925, "Regions ordered west to east by their typical place. Numbers shown when 8% or more.", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_regions(pr: pd.DataFrame, chance: float, name: str, out: Path):
    s = pr.sort_values("f1")
    fig, ax = plt.subplots(figsize=(8.4, 5.8))
    y = np.arange(len(s))
    ax.hlines(y, s.lo, s.hi, color=BLUE, lw=2, zorder=2)
    ax.scatter(s.f1, y, s=52, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_yticks(y, [f"{r}  (n={n})" for r, n in zip(s.region, s.n)], fontsize=9, color=INK)
    ax.axvline(chance, color=MUTED, ls=(0, (4, 3)), lw=1)
    ax.text(chance, len(s) - 0.4, " chance", color=MUTED, fontsize=8, va="bottom")
    ax.set_xlabel("F1 score of the region", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    fig.suptitle(f"Which regions are easy to recognise? ({name})", x=0.02, ha="left", color=INK, fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def plot_importance(imp: pd.DataFrame, name: str, out: Path):
    s = imp.sort_values("drop_in_macro_f1")
    fig, ax = plt.subplots(figsize=(8, 5.4))
    y = np.arange(len(s))
    ax.barh(y, s.drop_in_macro_f1, height=0.62, color=BLUE, xerr=s.sd, ecolor=MUTED, error_kw=dict(lw=1))
    ax.set_yticks(y, s.label, fontsize=9, color=INK)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel("Drop in macro-F1 when this feature is shuffled in the test fold", color=MUTED, fontsize=9)
    ax.grid(axis="x", color=GRID)
    style(ax)
    fig.suptitle(f"Which features does the classifier rely on? ({name})", x=0.02, ha="left", color=INK, fontsize=12, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_ROOT / "classifier"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    pd.set_option("display.width", 220)
    d = load()
    classes = np.array(sorted(d.region_en.unique()))
    K = len(classes)
    y = np.searchsorted(classes, d.region_en.to_numpy())
    print(f"{len(d)} recordings, {K} regions, {d.group_id.nunique()} groups; folds {d.fold.value_counts().sort_index().to_dict()}; "
          f"A has {len(SET_A)} features, B has {len(SET_B)}")
    tr_sizes = [len(tr) for _, tr, _ in splits(d)]
    print("training sizes after dropping test songs:", tr_sizes)

    results, per_region, probs = [], {}, {}
    for kind in ("LR", "GBM"):
        for tag, cols in (("A", SET_A), ("B", SET_B)):
            P = oof(d, cols, kind, classes)
            r, pr = score(d, P, classes, rng, f"{tag} + {kind}")
            results.append(r)
            per_region[r["model"]] = pr
            probs[r["model"]] = P
            print(f"{r['model']:8s} macro-F1 {r['macro_f1']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]  acc {r['accuracy']:.3f}  top3 {r['top3']:.3f}")

    # references
    prior = np.bincount(y, minlength=K) / len(y)
    sims = [macro_f1(confusion(y, rng.choice(K, len(y), p=prior), K)).mean() for _ in range(300)]
    chance = float(np.mean(sims))
    results.append({"model": "Stratified random guess", "macro_f1": chance, "lo": np.percentile(sims, 2.5), "hi": np.percentile(sims, 97.5),
                    "accuracy": float((prior**2).sum()), "top3": np.nan})
    maj = np.full(len(y), prior.argmax())
    (_, _, _), (mf, lo, hi) = boot(y, maj, d.group_id.to_numpy(), K, rng)
    results.append({"model": "Majority class", "macro_f1": mf, "lo": lo, "hi": hi, "accuracy": float(prior.max()), "top3": np.nan})
    geo = d.dropna(subset=["lon", "lat"]).reset_index(drop=True)
    yg = np.searchsorted(classes, geo.region_en.to_numpy())
    Pg = oof(geo, ["lon", "lat"], "KNN", classes)
    rg, _ = score(geo, Pg, classes, rng, "Place only (longitude/latitude) - not musical")
    results.append(rg)

    # family ablations on B with LR
    for fam in FAMILY_COLS:
        only = FAMILY_COLS[fam]
        rest = [c for c in SET_B if c not in only]
        for name, cols in ((f"only {fam}", only), (f"without {fam}", rest)):
            P = oof(d, cols, "LR", classes)
            r, _ = score(d, P, classes, rng, name)
            results.append(r)

    res = pd.DataFrame(results)
    res.to_csv(out / "metrics.csv", index=False)
    print(res.round(3).to_string(index=False))

    best = max(("A + LR", "A + GBM", "B + LR", "B + GBM"), key=lambda n: res.set_index("model").loc[n, "macro_f1"])
    P = probs[best]
    pred = P.argmax(1)
    pc, plo, phi = per_region[best]
    pr = pd.DataFrame({"region": classes, "n": np.bincount(y, minlength=K), "f1": pc, "lo": plo, "hi": phi})
    pr["recall"] = np.diag(confusion(y, pred, K)) / pr.n
    pr.to_csv(out / "per_region_scores.csv", index=False)
    print(f"best model: {best}")
    print(pr.sort_values("f1", ascending=False).round(2).to_string(index=False))

    # per fold
    fold_rows = []
    for f, tr, te in splits(d):
        fold_rows.append({"fold": f, "n_test": len(te), "n_train": len(tr), "channels_in_test": d.group_id.iloc[te].nunique(),
                          "largest_channel_share": d.group_id.iloc[te].value_counts(normalize=True).iloc[0],
                          "accuracy": float((pred[te] == y[te]).mean()),
                          "macro_f1": macro_f1(confusion(y[te], pred[te], K)).mean()})
    pf = pd.DataFrame(fold_rows)
    pf.to_csv(out / "per_fold_scores.csv", index=False)
    print(pf.round(3).to_string(index=False))

    # confusion, ordered west to east; most confused pairs vs distance
    placed = d[d.geo_level.isin(["county", "prefecture"])]
    lon = pd.Series({r: placed[placed.region_en == r].lon.median() for r in classes})
    lat = pd.Series({r: placed[placed.region_en == r].lat.median() for r in classes})
    order = np.argsort(lon.reindex(classes).to_numpy())
    C = confusion(y, pred, K)
    plot_confusion(C, order, classes, best, out / "fig_confusion.png")
    dg = haversine(lon.reindex(classes).to_numpy(), lat.reindex(classes).to_numpy())
    rows = []
    for i in range(K):
        for j in range(i + 1, K):
            rows.append({"region_a": classes[i], "region_b": classes[j], "km": dg[i, j],
                         "mistakes_a_as_b": int(C[i, j]), "mistakes_b_as_a": int(C[j, i]),
                         "rate": (C[i, j] + C[j, i]) / (C[i].sum() + C[j].sum())})
    cp = pd.DataFrame(rows).sort_values("rate", ascending=False)
    cp.to_csv(out / "confused_pairs.csv", index=False)
    print(cp.head(8).round(3).to_string(index=False))
    from scipy.stats import spearmanr
    print("confusion rate vs distance between region centres: Spearman %.2f" % spearmanr(cp.rate, cp.km)[0])

    imp = permutation_importance(d, SET_A, best.split(" + ")[1] if best.startswith("A") else "LR", classes, rng)
    imp.to_csv(out / "feature_importance.csv", index=False)
    print(imp.round(3).to_string(index=False))

    plot_models(res, chance, out / "fig_models.png")
    plot_regions(pr, chance, best, out / "fig_region_scores.png")
    plot_importance(imp, "12 features, " + (best if best.startswith("A") else "A + LR"), out / "fig_importance.png")
    pd.DataFrame({"item_id": d.item_id, "true": d.region_en, "predicted": classes[pred],
                  "confidence": P.max(1)}).to_csv(out / "oof_predictions.csv", index=False)
    print("outputs ->", out)


if __name__ == "__main__":
    main()
