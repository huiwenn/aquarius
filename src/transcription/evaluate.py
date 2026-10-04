"""
Score model outputs on the benchmark with standard note-level metrics (mir_eval).

Expects predictions at data/transcription/benchmark_preds/<model>/<clip_id>.mid
(for multi-track MIDI, only the track(s) selected by --track-filter are used;
default: all non-drum notes).

Metrics (F1, averaged over clips):
  COnPOff  onset ±50 ms, pitch ±50 cents, offset within max(50 ms, 20% dur)
  COnP     onset ±50 ms, pitch ±50 cents
  COn      onset ±50 ms
  *_100    same with onset tolerance ±100 ms. Added because singing GT conventions differ:
           M4Singer/GTSinger start a note at the syllable's consonant, while OpenVPI-style
           models start it at the vowel, which gives a ~+65 ms systematic bias (see docs/transcription.md)
  bias_ms  median signed offset (est - ref) of each est onset to its nearest ref onset
Results appended to data/transcription/benchmark_results.csv

Run: python src/transcription/evaluate.py MODEL [MODEL ...]
"""

import argparse
from pathlib import Path

import mir_eval
import numpy as np
import pandas as pd
import pretty_midi

ROOT = Path(__file__).resolve().parent.parent.parent
BENCH = ROOT / "data" / "transcription" / "benchmark"
PREDS = ROOT / "data" / "transcription" / "benchmark_preds"
RESULTS = ROOT / "data" / "transcription" / "benchmark_results.csv"


def load_pred(path: Path, track_filter: str | None) -> tuple[np.ndarray, np.ndarray]:
    pm = pretty_midi.PrettyMIDI(str(path))
    notes = []
    for inst in pm.instruments:
        if inst.is_drum:
            continue
        if track_filter and track_filter.lower() not in (inst.name or "").lower():
            continue
        notes += [(n.start, n.end, n.pitch) for n in inst.notes if n.end > n.start]
    if not notes:
        return np.zeros((0, 2)), np.zeros(0)
    notes = np.array(sorted(notes))
    return notes[:, :2], notes[:, 2]


METRICS = ["COnPOff", "COnP", "COn", "COnPOff_100", "COnP_100", "bias_ms"]


def score(ref_iv, ref_p, est_iv, est_p) -> dict:
    ref_hz, est_hz = mir_eval.util.midi_to_hz(ref_p), mir_eval.util.midi_to_hz(est_p)
    if len(est_iv) == 0:
        return {m: 0.0 for m in METRICS} | {"bias_ms": np.nan}
    prf = mir_eval.transcription.precision_recall_f1_overlap
    out = {}
    for tol, suffix in [(0.05, ""), (0.1, "_100")]:
        out["COnPOff" + suffix] = prf(ref_iv, ref_hz, est_iv, est_hz, onset_tolerance=tol)[2]
        out["COnP" + suffix] = prf(ref_iv, ref_hz, est_iv, est_hz, onset_tolerance=tol, offset_ratio=None)[2]
    out["COn"] = mir_eval.transcription.onset_precision_recall_f1(ref_iv, est_iv)[2]
    d = est_iv[:, :1] - ref_iv[:, 0][None, :]
    nearest = d[np.arange(len(d)), np.abs(d).argmin(1)]
    out["bias_ms"] = float(np.median(nearest[np.abs(nearest) < 0.3]) * 1000) if (np.abs(nearest) < 0.3).any() else np.nan
    return out


def evaluate(model: str, track_filter: str | None) -> pd.DataFrame:
    index = pd.read_csv(BENCH / "index.csv")
    rows = []
    for _, r in index.iterrows():
        gt = pd.read_csv(BENCH / "gt" / f"{r.clip_id}.csv")
        ref_iv, ref_p = gt[["onset", "offset"]].to_numpy(), gt["pitch"].to_numpy(float)
        pred = PREDS / model / f"{r.clip_id}.mid"
        est_iv, est_p = load_pred(pred, track_filter) if pred.exists() else (np.zeros((0, 2)), np.zeros(0))
        rows.append({"clip_id": r.clip_id, "source": r.source, "missing": not pred.exists(),
                     **score(ref_iv, ref_p, est_iv, est_p)})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("models", nargs="+")
    ap.add_argument("--track-filter", default=None, help="substring of MIDI track name to keep (e.g. 'sing')")
    args = ap.parse_args()

    summary = []
    for model in args.models:
        df = evaluate(model, args.track_filter)
        for src, sub in [("all", df), *df.groupby("source")]:
            summary.append({"model": model + (f"[{args.track_filter}]" if args.track_filter else ""),
                            "subset": src, "n": len(sub), "missing": int(sub.missing.sum()),
                            **sub[METRICS].mean().round(4).to_dict()})
    out = pd.DataFrame(summary)
    out["bias_ms"] = out["bias_ms"].round(1)
    print(out.to_string(index=False))
    if RESULTS.exists():
        prev = pd.read_csv(RESULTS)
        prev = prev[~prev.model.isin(out.model)]
        out = pd.concat([prev, out])
    out.to_csv(RESULTS, index=False)


if __name__ == "__main__":
    main()
