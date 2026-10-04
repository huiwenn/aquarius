"""
Probing: what do frozen embeddings encode? For each embedding, a 5-fold ridge / logistic probe predicts simple
musical descriptors from the embedding. Output: data/regionclf/emb/probe_<task>.csv (+ printed table).

Descriptors: mean MIDI pitch (register), pitch range, log #notes (length), log median IOI (tempo / note density),
mean |interval| (leapiness), 偏音 share (mass on fa/ti/变徵/闰 relative to 宫, i.e. non-pentatonic content),
estimated 宫 pitch class (12-way accuracy, "key"), final degree relative to 宫 (12-way accuracy, "mode").

Run (arm64 env):
  PYTHONPATH=src ~/miniforge3/envs/regionclf/bin/python src/regionclf/exp_pretrained_probe.py --task A5 \
      --embs c2pre_mtf_raw,c2pre_mtf_tonic,m3_mtf_raw
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sklearn.linear_model import LogisticRegression, RidgeCV  # noqa: E402
from sklearn.model_selection import KFold, cross_val_predict  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from regionclf.common import D, task  # noqa: E402
from regionclf.exp_pretrained import SOURCE, features  # noqa: E402
from regionclf.features import estimate_gong, pc_profile  # noqa: E402


def descriptors(recs):
    rows = []
    for r in recs:
        n = r["notes"]
        g = estimate_gong(n)
        prof = np.roll(pc_profile(n), -g)
        ioi = np.diff(n[:, 0])
        ioi = ioi[ioi > 1e-3]
        rows.append({"mean_pitch": n[:, 2].mean(), "range": np.percentile(n[:, 2], 95) - np.percentile(n[:, 2], 5),
                     "log_len": np.log(len(n)), "log_ioi": np.log(np.median(ioi)) if len(ioi) else 0.0,
                     "abs_int": np.abs(np.diff(n[:, 2])).mean(), "pianyin": prof[[5, 6, 10, 11]].sum(),
                     "gong": g, "final_deg": int(n[-1, 2] - g) % 12})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="A5")
    ap.add_argument("--embs", required=True)
    a = ap.parse_args()
    recs = task(a.task)
    desc = descriptors(recs)
    kf = KFold(5, shuffle=True, random_state=0)
    out = []
    for emb in a.embs.split(","):
        X = np.nan_to_num(features(recs, emb, SOURCE[a.task]))
        row = {"emb": emb}
        for c in ["mean_pitch", "range", "log_len", "log_ioi", "abs_int", "pianyin"]:
            y = desc[c].values
            p = cross_val_predict(make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 4, 11))), X, y, cv=kf)
            row[f"R2_{c}"] = round(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum(), 3)
        for c in ["gong", "final_deg"]:
            y = desc[c].values
            p = cross_val_predict(make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000)), X, y,
                                  cv=kf)
            row[f"acc_{c}"] = round((p == y).mean(), 3)
            row[f"maj_{c}"] = round(pd.Series(y).value_counts(normalize=True).iloc[0], 3)
        out.append(row)
        print(row, flush=True)
    df = pd.DataFrame(out)
    df.to_csv(D / "emb" / f"probe_{a.task}.csv", index=False)
    print(df.to_string())


if __name__ == "__main__":
    main()
