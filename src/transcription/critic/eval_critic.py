"""
Validate the critic on the benchmark (separated vocals of the benchmark mixtures, GAME + trim predictions).

1. Critic ↔ ground-truth agreement, per predicted note. GT label:
     correct   a GT note covers ≥50% of the note and pitch within 0.5 st
     wrong     a GT note covers ≥50% of the note but pitch differs ≥0.5 st
     spurious  no GT note covers ≥20% of the note
   Reports precision/recall of the critic's wrong_pitch and unvoiced flags, plus how often a repitch
   produces the GT pitch.
2. Effect of each correction on note F1: writes benchmark_preds/<base>+<variant> and scores with evaluate.py.

Run (py312): python src/transcription/critic/eval_critic.py [--base game_pp@sep_htdemucs] [param overrides]
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from critic import Evidence, Params, audit_notes, correct  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / "data" / "transcription" / "benchmark"
P = ROOT / "data" / "transcription" / "benchmark_preds"
C = ROOT / "data" / "transcription" / "critic"


def gt_label(note, gt: pd.DataFrame) -> tuple[str, float]:
    dur = note.end - note.start
    ov = (np.minimum(gt.offset, note.end) - np.maximum(gt.onset, note.start)).clip(lower=0)
    if len(gt) == 0 or ov.max() < 0.2 * dur:
        return "spurious", np.nan
    k = int(ov.values.argmax())
    if ov.iloc[k] < 0.5 * dur:
        return "ambiguous", np.nan
    g = gt.pitch.iloc[k]
    return ("correct" if abs(g - note.pitch) < 0.5 else "wrong"), g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="game_pp@sep_htdemucs")
    for k, v in vars(Params()).items():
        if isinstance(v, bool):
            ap.add_argument(f"--{k.replace('_', '-')}", type=lambda x: x.lower() in ("1", "true", "yes"), default=v)
        else:
            ap.add_argument(f"--{k.replace('_', '-')}", type=type(v), default=v)
    ap.add_argument("--no-score", action="store_true")
    ap.add_argument("--second", default="rosvot@sep_htdemucs", help="second transcriber for consensus")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    params = Params(**{k: getattr(args, k) for k in vars(Params())})
    idx = pd.read_csv(B / "index.csv")

    rows = []
    variants = {"repitch": dict(repitch=True, delete=False, fill=False),
                "delete": dict(repitch=False, delete=True, fill=False),
                "fill": dict(repitch=False, delete=False, fill=True),
                "critic": dict(repitch=True, delete=True, fill=True)}
    for r in idx.itertuples():
        midi = P / args.base / f"{r.clip_id}.mid"
        ev = Evidence.load(C / "bench_rmvpe" / f"{r.clip_id}.npz", C / "bench_pesto" / f"{r.clip_id}.npz")
        gt = pd.read_csv(B / "gt" / f"{r.clip_id}.csv")
        notes = sorted((n for i in pretty_midi.PrettyMIDI(str(midi)).instruments for n in i.notes),
                       key=lambda n: n.start)
        sec_path = P / args.second / f"{r.clip_id}.mid"
        second = [x for i in pretty_midi.PrettyMIDI(str(sec_path)).instruments for x in i.notes] \
            if sec_path.exists() else []
        for note, a in zip(notes, audit_notes(notes, ev, params, second if params.consensus else None)):
            lab, gp = gt_label(note, gt)
            flagged = a["verdict"] in ("wrong_pitch", "octave_error") and (
                not params.consensus or a["second_agrees"])
            fixed_ok = (abs(a["target"] - gp) < 0.5) if (flagged and not np.isnan(gp)) else np.nan
            v = a["verdict"] if (a["verdict"] not in ("wrong_pitch", "octave_error") or flagged) else "flag_no_consensus"
            rows.append({"source": r.source, "verdict": v, "label": lab, "repitch_correct": fixed_ok})
        for name, kw in variants.items():
            pm, _ = correct(midi, ev, params, second_midi=sec_path, **kw)
            out = P / f"{args.base}+{name}{args.tag}"
            out.mkdir(parents=True, exist_ok=True)
            pm.write(str(out / f"{r.clip_id}.mid"))

    d = pd.DataFrame(rows)
    print("Critic verdict × GT label (predicted notes, all subsets):")
    print(pd.crosstab(d.verdict, d.label, margins=True).to_string())
    for src, s in [("all", d), *d.groupby("source")]:
        flag_w = s.verdict.isin(["wrong_pitch", "octave_error"])
        true_w = s.label == "wrong"
        flag_u, true_s = s.verdict == "unvoiced", s.label == "spurious"
        print(f"\n[{src}] wrong-pitch flag: precision {(flag_w & true_w).sum() / max(1, flag_w.sum()):.2f} "
              f"recall {(flag_w & true_w).sum() / max(1, true_w.sum()):.2f} (n flagged {flag_w.sum()}) | "
              f"repitch lands on GT pitch {s.repitch_correct.mean():.2f} | "
              f"unvoiced flag: precision {(flag_u & true_s).sum() / max(1, flag_u.sum()):.2f} "
              f"recall {(flag_u & true_s).sum() / max(1, true_s.sum()):.2f} | "
              f"'ok' notes actually correct {((s.verdict == 'ok') & (s.label == 'correct')).sum() / max(1, (s.verdict == 'ok').sum()):.2f}")
    if not args.no_score:
        models = [args.base] + [f"{args.base}+{v}{args.tag}" for v in variants]
        subprocess.run([sys.executable, str(ROOT / "src" / "transcription" / "evaluate.py"), *models], check=True)


if __name__ == "__main__":
    main()
