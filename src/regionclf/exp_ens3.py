"""
Cleaner transcriptions: does the 3-run GAME majority-vote ensemble (docs/transcription.md §7.6: ~35% less run-to-run
noise, better vocadito F1) also make regions more learnable? Compares, on the same recordings and the same folds,
single-run GAME (trans_game_pp) vs the ensemble (trans_game_ens3_pp), for theory+GBM, n-gram LR and dual-view.
Only recordings present in both variants are used, so the comparison is paired.

Run (py312): python src/regionclf/corpus.py --sources trans_game_ens3_pp && python src/regionclf/exp_ens3.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import folds, labels, load, log_result  # noqa: E402


def main() -> None:
    E = load("essen")
    single = {r["item_id"]: r for r in load("trans_game_pp")}
    ens = {r["item_id"]: r for r in load("trans_game_ens3_pp")}
    ids = sorted(set(single) & set(ens))
    for name, pool in [("game single run", single), ("game 3-run ensemble", ens)]:
        recs = [pool[i] for i in ids]
        y = labels(recs)
        for mname, fn in [("theory/hgb", F.theory_fold), ("ngram7/LR", F.ngram_fold)]:
            pred = np.empty(len(recs), dtype=object)
            for tr, te in folds(recs):
                pred[te] = fn([recs[i] for i in tr], [recs[i] for i in te])
            log_result(f"{mname} on {name}", "data", "T15", y, pred, f"paired subset n={len(ids)}")

        def dual(tr, te):
            classes = sorted(set(labels(tr)))
            tg = {r["group"] for r in te}
            ext = [r for r in E if r["group"] not in tg and r["region"] in set(classes)]
            w = np.array([1.0] * len(tr) + [len(tr) / max(1, len(ext))] * len(ext))
            sk = F.fit_ngram(tr + ext, level=2, weights=w)
            sf = F.fit_ngram(tr)
            p = F.proba(sk, classes)([F.doc(r, 2) for r in te]) + F.proba(sf, classes)([F.doc(r) for r in te])
            return np.array(classes)[p.argmax(1)]
        pred = np.empty(len(recs), dtype=object)
        for tr, te in folds(recs):
            pred[te] = dual([recs[i] for i in tr], [recs[i] for i in te])
        log_result(f"dual-view on {name}", "data", "T15", y, pred, f"paired subset n={len(ids)}")


if __name__ == "__main__":
    main()
