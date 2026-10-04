"""
Example study on the merged Colour Regions pool (rounds 1 + 2) for the paper.

(a) Strict protocol (channel+song folds, 3 seeds pooled; common.folds) on T15 / T5 of the merged pool,
    with the official models: theory+GBM, multi-viewpoint n-gram LR, dual-view (+ scores).
(b) Cross-round transfer: train on round 1, test on round 2 (round 2 shares no channel with round 1); training
    drops round-1 recordings whose song occurs in round 2. One run per seed (dual-view/n-gram deterministic).
(c) Breakdown of the pooled out-of-fold predictions of (a): by provenance tier (A+B vs C), Han vs minority,
    round, and performance type.

Needs corpus_trans_merged.pkl:  python src/regionclf/corpus.py --sources trans_merged
Results → data/regionclf/review_merged.csv, review_merged_breakdown.csv, oof/merged_*.csv
Run (py312): OMP_NUM_THREADS=4 python src/regionclf/rev_merged.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from colour_regions.regions import TYPE  # noqa: E402
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import A5_REGIONS, D, labels, load, log_result, scores, task  # noqa: E402
from regionclf.rev_protocol import oof  # noqa: E402
from regionclf.rev_stats import compare, dual_fold  # noqa: E402

MODELS = [("theory+GBM", F.theory_fold), ("n-gram LR", F.ngram_fold)]


def main() -> None:
    E, A = load("essen"), load("anthology")
    rows, oof_rows = [], []
    for tname, ext in [("T15", [E]), ("T5", [A, [r for r in E if r["region"] in A5_REGIONS]])]:
        recs = task(tname, trans_variant="merged")
        models = MODELS + [("dual-view", dual_fold(ext))]
        runs = {}
        # (a) strict protocol on the pool
        for mname, fn in models:
            runs[mname] = [oof(recs, fn, s) for s in (0, 1, 2)]
            y = np.concatenate([r[0] for r in runs[mname]])
            p = np.concatenate([r[1] for r in runs[mname]])
            s = log_result(f"{mname} [merged pool, channel+song folds, 3 seeds pooled]", "merged", tname, y, p,
                           "musical features only; no shared channel or song between train/test")
            rows.append({"task": tname, "setting": "pool", "model": mname, "n": len(recs), **s})
            for seed, (_, pred) in enumerate(runs[mname]):
                oof_rows += [dict(task=tname, model=mname, seed=seed, item_id=r["item_id"], region=r["region"],
                                  pred=pp, round=r["round"], tier=r["tier"], ptype=r["performance_type"])
                             for r, pp in zip(recs, pred)]
        for a, b in (("dual-view", "n-gram LR"), ("n-gram LR", "theory+GBM")):
            c = compare(f"{tname} merged pool: {a} vs {b}", runs[a], runs[b], n_boot=2000, n_perm=5000)
            rows.append({"task": tname, "setting": "pool", "model": f"Δ {a} − {b}", **c})
        # (b) round 1 → round 2
        te = [r for r in recs if r["round"] == 2]
        te_songs = {r["group"] for r in te}
        tr = [r for r in recs if r["round"] == 1 and r["group"] not in te_songs]
        for mname, fn in models:
            pred = fn(tr, te)
            s = scores(labels(te), pred)
            log_result(f"{mname} [round 1 → round 2, songs disjoint]", "merged", tname, labels(te), pred,
                       f"train {len(tr)} round-1 recordings, test {len(te)} round-2 (new channels)")
            rows.append({"task": tname, "setting": "round1→round2", "model": mname, "n": len(te),
                         "n_train": len(tr), **s})
        pd.DataFrame(rows).round(4).to_csv(D / "review_merged.csv", index=False)

    # (c) breakdowns of pooled OOF predictions
    o = pd.DataFrame(oof_rows)
    o.to_csv(D / "oof" / "merged_oof.csv", index=False)
    o["tier_group"] = np.where(o.tier.isin(["A1", "A2", "A", "B"]), "A+B", np.where(o.tier == "C", "C", "unknown"))
    o["type"] = o.region.map(TYPE)
    br = []
    for col in ("tier_group", "type", "round", "ptype"):
        for (t, m, v), g in o.groupby(["task", "model", col]):
            br.append(dict(task=t, model=m, by=col, value=v, n=len(g) // 3, acc=(g.region == g.pred).mean(),
                           **{k: v_ for k, v_ in scores(g.region, g.pred).items() if k != "acc"}))
    pd.DataFrame(br).round(4).to_csv(D / "review_merged_breakdown.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string())
    print(pd.DataFrame(br).round(3).to_string())


if __name__ == "__main__":
    main()
