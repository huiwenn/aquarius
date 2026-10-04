"""
Hierarchical classification (T15): stage 1 Han vs minority song area, stage 2 region within the predicted group.
Motivated by §9: only ~20% of confusions cross the Han/minority boundary, and within-Han confusions are geographic.
Model at every node: the multi-viewpoint n-gram LR (exp_fusion.fit_ngram). Also reports stage-1 accuracy.

Run (py312): python src/regionclf/exp_hier.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.analyze import MINORITY  # noqa: E402
from regionclf.common import folds, labels, log_result, task  # noqa: E402
from sklearn.metrics import accuracy_score  # noqa: E402


def grp(r):
    return "minority" if r["region"] in MINORITY else "han"


def main() -> None:
    recs = task("T15")
    for by in ["group", "channel"]:
        y = labels(recs)
        pred = np.empty(len(recs), dtype=object)
        g_true, g_pred = [], []
        for tr, te in folds(recs, by=by):
            train, test = [recs[i] for i in tr], [recs[i] for i in te]
            top = F.ngram_model().fit([F.doc(r) for r in train], [grp(r) for r in train])
            gp = top.predict([F.doc(r) for r in test])
            sub = {g: F.fit_ngram([r for r in train if grp(r) == g]) for g in ("han", "minority")}
            for k, (r, g) in enumerate(zip(test, gp)):
                pred[te[k]] = sub[g].predict([F.doc(r)])[0]
            g_true += [grp(r) for r in test]
            g_pred += list(gp)
        log_result(f"hierarchical Han/minority → region (n-gram LR) folds-by-{by}", "fusion", "T15", y, pred,
                   f"stage-1 Han/minority accuracy {accuracy_score(g_true, g_pred):.3f}")


if __name__ == "__main__":
    main()
