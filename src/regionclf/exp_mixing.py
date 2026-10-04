"""
Family "data": what data should we learn from? Cleaner vs noisier, more diverse, mixed, transferred.
Representation fixed to the music-theory features (features.py) + gradient boosting, so that only the
*data* changes between rows. Test sets and folds are always the target task's fixed grouped folds; any
external training data is added in full EXCEPT songs whose normalized title appears in the test fold
(same-title variants across sources would leak).

Experiments
  transfer   train on source S only, test on target T (shared regions only), e.g. A→T5, E5→T5, T5→A5
  mix        target folds + external sources added to each training fold (T5 + A, T5 + E5, T5 + A + E5,
             T15 + E, A5 + T5 …); optional per-source sample weights and a source indicator feature
  variants   T15 with each transcription variant (primary, game_pp, rosvot, game_ens3_pp) and with
             noise-augmentation (train on GAME ∪ ROSVOT versions of the training recordings, test on primary)
  clean      train only on the cleaner part of each training fold (by GAME–ROSVOT agreement, critic ok-share,
             or 原生态 performance type), test on all
  size       learning curve: fraction of training recordings per region

Run (py312): python src/regionclf/exp_mixing.py [--which transfer,mix,variants,clean,size]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import A5_REGIONS, folds, labels, load, log_result, task  # noqa: E402
from regionclf.features import theory_features  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
_cache: dict = {}


def feats(recs) -> np.ndarray:
    out = []
    for r in recs:
        key = (r["source"], r["item_id"])
        if key not in _cache:
            _cache[key] = theory_features(r["notes"])
        out.append(_cache[key])
    return np.vstack(out)


def model():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, class_weight="balanced",
                                          random_state=0)


def fit_predict(train, test, weights=None, source_feature=False):
    Xtr, Xte = feats(train), feats(test)
    if source_feature:
        srcs = sorted({r["source"] for r in train + test})
        enc = lambda rs: np.array([[r["source"] == s for s in srcs] for r in rs], float)  # noqa: E731
        Xtr, Xte = np.hstack([Xtr, enc(train)]), np.hstack([Xte, enc(test)])
    m = model()
    m.fit(Xtr, labels(train), sample_weight=weights)
    return m.predict(Xte)


def run_cv(name, target_name, target, extra=(), weight_fn=None, filter_train=None, source_feature=False,
           notes=""):
    y = labels(target)
    pred = np.empty(len(target), dtype=object)
    for tr, te in folds(target):
        test = [target[i] for i in te]
        test_groups = {r["group"] for r in test}
        train = [target[i] for i in tr]
        if filter_train:
            train = filter_train(train)
        for ex in extra:
            train += [r for r in ex if r["group"] not in test_groups and r["region"] in set(y)]
        w = np.array([weight_fn(r) for r in train]) if weight_fn else None
        pred[te] = fit_predict(train, test, w, source_feature)
    return log_result(name, "data", target_name, y, pred, notes)


def transfer():
    A, E, T = load("anthology"), load("essen"), load("trans_primary")
    pairs = [("A→T5", A, [r for r in T if r["region"] in A5_REGIONS]),
             ("E5→T5", [r for r in E if r["region"] in A5_REGIONS], [r for r in T if r["region"] in A5_REGIONS]),
             ("A+E5→T5", A + [r for r in E if r["region"] in A5_REGIONS],
              [r for r in T if r["region"] in A5_REGIONS]),
             ("T5→A5", [r for r in T if r["region"] in A5_REGIONS], A),
             ("E5→A5", [r for r in E if r["region"] in A5_REGIONS], A),
             ("A→E5", A, [r for r in E if r["region"] in A5_REGIONS])]
    Eregs = {r["region"] for r in E}
    TE = [r for r in T if r["region"] in Eregs]
    pairs.append(("E→T14", E, TE))
    pairs.append(("T14→E", TE, [r for r in E if r["region"] in {r["region"] for r in TE}]))
    for name, src, tgt in pairs:
        tgt_groups = {r["group"] for r in tgt}
        src = [r for r in src if r["group"] not in tgt_groups]  # never train on a same-title song
        pred = fit_predict(src, tgt)
        log_result(f"transfer {name}", "data", name.split("→")[1], labels(tgt), pred,
                   f"train {len(src)} {name.split('→')[0]} only; no target data")


def mix():
    A, E = load("anthology"), load("essen")
    E5 = [r for r in E if r["region"] in A5_REGIONS]
    T5, T15, A5 = task("T5"), task("T15"), task("A5")
    run_cv("T5 only", "T5", T5)
    run_cv("T5 + A", "T5", T5, [A])
    run_cv("T5 + E5", "T5", T5, [E5])
    run_cv("T5 + A + E5", "T5", T5, [A, E5])
    run_cv("T5 + A (A down-weighted to equal total)", "T5", T5, [A],
           weight_fn=lambda r: 1.0 if r["source"].startswith("trans") else 160 / 8654)
    run_cv("T5 + A + source flag", "T5", T5, [A], source_feature=True)
    run_cv("T15 only", "T15", T15)
    run_cv("T15 + E", "T15", T15, [E])
    run_cv("T15 + E + A", "T15", T15, [E, A])
    run_cv("T15 + E (E down-weighted)", "T15", T15, [E],
           weight_fn=lambda r: 1.0 if r["source"].startswith("trans") else 600 / 2189)
    run_cv("A5 only", "A5", A5)
    run_cv("A5 + T5", "A5", A5, [T5])
    run_cv("A5 + E5", "A5", A5, [E5])
    Etask = task("E")
    run_cv("E only", "E", Etask)
    run_cv("E + T15", "E", Etask, [T15])
    run_cv("E + A", "E", Etask, [A])


def variants():
    base = task("T15")
    for v in ["game_pp", "rosvot", "game_ens3_pp"]:
        p = ROOT / "data" / "regionclf" / f"corpus_trans_{v}.pkl"
        if not p.exists():
            continue
        recs = load(f"trans_{v}")
        run_cv(f"T15 transcriptions={v}", "T15", recs, notes=f"transcriber variant {v}")
    # noise augmentation: add the ROSVOT (and GAME single-run) transcriptions of *training* recordings
    ros = {r["item_id"]: r for r in load("trans_rosvot")}
    gam = {r["item_id"]: r for r in load("trans_game_pp")}

    def aug(train):
        extra = [ros[r["item_id"]] for r in train if r["item_id"] in ros] + \
                [gam[r["item_id"]] for r in train if r["item_id"] in gam and r["subset"] != "game_pp"]
        return train + extra
    run_cv("T15 train ∪ ROSVOT versions (noise augmentation)", "T15", base, filter_train=aug,
           notes="each training recording also contributes its ROSVOT transcription")


def clean():
    idx = pd.read_csv(ROOT / "data" / "regions_transcription" / "dataset_index.csv").set_index("video_id")
    crit = ROOT / "data" / "transcription" / "critic" / "dataset_summary.csv"
    ok = pd.read_csv(crit).set_index("video_id") if crit.exists() else None
    base = task("T15")

    def top(frac, score):
        def f(train):
            by_reg = {}
            for r in train:
                by_reg.setdefault(r["region"], []).append(r)
            out = []
            for rs in by_reg.values():
                rs = sorted(rs, key=score, reverse=True)
                out += rs[:max(3, int(round(frac * len(rs))))]
            return out
        return f

    agree = lambda r: idx.loc[r["item_id"], "game_rosvot_conp"] if r["item_id"] in idx.index else 0  # noqa: E731
    okshare = (lambda r: (ok.loc[r["item_id"], "v_ok"] / max(1, ok.loc[r["item_id"], "notes"]))  # noqa: E731
               if ok is not None and r["item_id"] in ok.index else 0)
    rng = np.random.RandomState(0)
    rand = {r["item_id"]: rng.rand() for r in base}
    for frac in (0.5, 0.75):
        run_cv(f"T15 train on top {int(frac*100)}% by GAME–ROSVOT agreement", "T15", base,
               filter_train=top(frac, lambda r: np.nan_to_num(agree(r))))
        run_cv(f"T15 train on top {int(frac*100)}% by critic ok-share", "T15", base,
               filter_train=top(frac, okshare))
        run_cv(f"T15 train on random {int(frac*100)}% (control)", "T15", base,
               filter_train=top(frac, lambda r: rand[r["item_id"]]))
    run_cv("T15 train on 原生态 only", "T15", base,
           filter_train=lambda tr: [r for r in tr if r.get("performance_type") == "原生态"] or tr)
    run_cv("T15 train on non-原生态 only", "T15", base,
           filter_train=lambda tr: [r for r in tr if r.get("performance_type") != "原生态"] or tr)


def size():
    base = task("T15")
    rng = np.random.RandomState(0)
    for frac in (0.25, 0.5, 0.75, 1.0):
        def f(train, frac=frac):
            return [r for r in train if rng.rand() < frac] if frac < 1 else train
        run_cv(f"T15 learning curve {int(frac*100)}% of training data", "T15", base, filter_train=f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="transfer,mix,variants,clean,size")
    args = ap.parse_args()
    for w in args.which.split(","):
        globals()[w]()


if __name__ == "__main__":
    main()
