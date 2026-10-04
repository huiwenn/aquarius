"""
Shared data access + evaluation protocol for all region-classification experiments.

TASKS (dataset × label set). Every experiment reports on the same tasks with the same folds:
  A5      anthology, 5 色彩区 (8.6k clean scores)
  E       essen, regions with ≥ 20 songs (13 classes, heavily skewed to 西北部高原)
  T15     transcriptions (primary), all 15 regions × 40 recordings
  T5      transcriptions restricted to the 5 anthology regions (for transfer / mixing experiments)
Label-set helpers let experiments train on one source and test on another.

PROTOCOL: StratifiedGroupKFold(5, shuffle, seed 0). Scores: grouped by song title. Transcriptions (default since
2026-10-01): grouped by channel AND training folds drop test-fold songs (see folds()). Channel is never a feature.
Originally: groups = normalized song title, so the same song never
sits in train and test. Metrics: macro-F1 (headline; classes are imbalanced in A5/E), balanced accuracy, accuracy.
Every run appends one row per task to data/regionclf/results.csv via `log_result`.

Usage:
  from regionclf.common import load, task, folds, evaluate_predictions, log_result
  X, y, groups, recs = task("T15")
"""

import datetime as dt
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "regionclf"
RESULTS = D / "results.csv"
A5_REGIONS = ["东北部平原", "江浙平原", "粤", "江汉", "西南高原"]


def load(source: str) -> list[dict]:
    with open(D / f"corpus_{source}.pkl", "rb") as f:
        return pickle.load(f)


def task(name: str, trans_variant: str = "primary") -> list[dict]:
    """Return the records for a task (no features: each experiment builds its own representation)."""
    if name == "A5":
        return load("anthology")
    if name == "E":
        recs = load("essen")
        counts = pd.Series([r["region"] for r in recs]).value_counts()
        keep = set(counts[counts >= 20].index)
        return [r for r in recs if r["region"] in keep]
    if name == "T15":
        return load(f"trans_{trans_variant}")
    if name == "T5":
        return [r for r in load(f"trans_{trans_variant}") if r["region"] in A5_REGIONS]
    if name == "E5":
        return [r for r in load("essen") if r["region"] in A5_REGIONS]
    raise ValueError(name)


def labels(recs):
    return np.array([r["region"] for r in recs])


def groups(recs):
    return np.array([r["group"] for r in recs])


def is_transcription(recs) -> bool:
    return all(str(r["source"]).startswith("trans") for r in recs)


def folds(recs, n_splits: int = 5, seed: int = 0, by: str | None = None):
    """Deterministic grouped stratified folds.

    by='group'   folds grouped by song (normalized title)
    by='channel' folds grouped by recording channel / volume
    by='channel+song' (DEFAULT for transcriptions, by=None): folds grouped by channel, and every training fold
                 additionally drops recordings whose song appears in the test fold. No channel and no song is
                 shared between train and test. Channel is never a model input; this only blocks it from leaking
                 into the evaluation through singer / recording-chain / transcription-artifact similarity
                 (docs/region_classification.md §17.1). Strict song∪channel connected components are infeasible
                 (one component holds 394/600 recordings), hence this two-constraint form.
    by=None on score corpora → 'group'.
    """
    if by is None:
        by = "channel+song" if is_transcription(recs) else "group"
    y = labels(recs)
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    if by != "channel+song":
        g = np.array([r[by] for r in recs])
        return list(skf.split(np.zeros(len(y)), y, g))
    ch = np.array([r["channel"] for r in recs])
    song = np.array([r["group"] for r in recs])
    out = []
    for tr, te in skf.split(np.zeros(len(y)), y, ch):
        test_songs = set(song[te])
        out.append((np.array([i for i in tr if song[i] not in test_songs]), te))
    return out


def scores(y_true, y_pred) -> dict:
    return {"macro_f1": f1_score(y_true, y_pred, average="macro"),
            "bal_acc": balanced_accuracy_score(y_true, y_pred),
            "acc": accuracy_score(y_true, y_pred)}


def cv_predict(recs, fit_predict, n_splits=5, seed=0, by=None):
    """fit_predict(train_recs, test_recs) -> predicted labels for test_recs. Returns out-of-fold predictions."""
    y = labels(recs)
    pred = np.empty(len(recs), dtype=object)
    for tr, te in folds(recs, n_splits, seed, by):
        pred[te] = fit_predict([recs[i] for i in tr], [recs[i] for i in te])
    return y, pred


def log_result(experiment: str, family: str, task_name: str, y_true, y_pred, notes: str = "", **extra) -> dict:
    s = scores(y_true, y_pred)
    row = {"time": dt.datetime.now().isoformat(timespec="seconds"), "experiment": experiment, "family": family,
           "task": task_name, "n": len(y_true), "n_classes": len(set(y_true)), **{k: round(v, 4) for k, v in s.items()},
           "notes": notes, **extra}
    D.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(RESULTS, mode="a", header=not RESULTS.exists(), index=False)
    print(f"[{task_name}] {experiment}: macroF1 {s['macro_f1']:.3f}  balAcc {s['bal_acc']:.3f}  acc {s['acc']:.3f}",
          flush=True)
    return s


def chance(task_name: str):
    """Majority-class and stratified-random baselines."""
    recs = task(task_name)
    y = labels(recs)
    maj = pd.Series(y).value_counts().index[0]
    log_result("majority", "baseline", task_name, y, np.array([maj] * len(y)))
    rng = np.random.RandomState(0)
    log_result("stratified_random", "baseline", task_name, y, rng.permutation(y))
