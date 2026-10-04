"""
GAME run-ensembling: GAME's D3PM decoder is stochastic; two identical runs agree on only ~84% of notes
in-domain (invariance.py). Majority-voting several runs removes run-specific notes.

vote(runs): cluster notes across runs (same pitch, onset within ±`tol` s); keep a cluster present in
≥ ceil(k/2) runs; onset/offset = median over the cluster.
Test (no reference needed): two *disjoint* 3-run ensembles should agree far more than two single runs.

Runs: data/transcription/audit/invariance/midi/{orig,rerun,run3,run4,run5,run6}/<id>.mid
Run (py312): python src/transcription/audit/ensemble.py            (generates missing runs with GAME)
"""

import subprocess
import sys
from pathlib import Path

import mir_eval
import numpy as np
import pandas as pd
import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from melody import load_notes  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
W = ROOT / "data" / "transcription" / "audit" / "invariance"
GAME = [str(Path.home() / "miniforge3" / "envs" / "game" / "bin" / "python"),
        str(ROOT / "src" / "transcription" / "models" / "game" / "run_game.py")]
GAME_ARGS = ["--size", "medium", "--lang", "zh", "--seg-threshold", "0.1"]
RUNS = ["orig", "rerun", "run3", "run4", "run5", "run6"]


def vote(runs: list[list[tuple]], tol: float = 0.05) -> list[tuple]:
    k = len(runs)
    need = int(np.ceil(k / 2)) if k % 2 else k // 2 + 1
    pool = sorted((s, e, p, r) for r, notes in enumerate(runs) for s, e, p in notes)
    used = [False] * len(pool)
    out = []
    for i, (s, e, p, r) in enumerate(pool):
        if used[i]:
            continue
        members, seen = [i], {r}
        for j in range(i + 1, len(pool)):
            if pool[j][0] - s > tol:
                break
            if not used[j] and pool[j][2] == p and pool[j][3] not in seen:
                members.append(j)
                seen.add(pool[j][3])
        if len(members) >= need:
            for m in members:
                used[m] = True
            out.append((float(np.median([pool[m][0] for m in members])),
                        float(np.median([pool[m][1] for m in members])), p))
    out.sort()
    # enforce monophony: cut a note at the next onset
    return [(s, min(e, out[i + 1][0]) if i + 1 < len(out) else e, p) for i, (s, e, p) in enumerate(out)]


def f1(a, b) -> float:
    if not a or not b:
        return np.nan
    a, b = np.array(a), np.array(b)
    return mir_eval.transcription.precision_recall_f1_overlap(
        a[:, :2], mir_eval.util.midi_to_hz(a[:, 2]), b[:, :2], mir_eval.util.midi_to_hz(b[:, 2]),
        offset_ratio=None)[2]


def main() -> None:
    for run in RUNS[2:]:
        out = W / "midi" / run
        if not out.exists() or len(list(out.glob("*.mid"))) < len(list((W / "audio" / "orig").glob("*.wav"))):
            subprocess.run(GAME + [str(W / "audio" / "orig"), str(out)] + GAME_ARGS, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rows = []
    for f in sorted((W / "audio" / "orig").glob("*.wav")):
        runs = [load_notes(W / "midi" / r / f"{f.stem}.mid") for r in RUNS]
        ea, eb = vote(runs[:3]), vote(runs[3:])
        rows.append({"video_id": f.stem,
                     "single_vs_single": np.nanmean([f1(runs[i], runs[j]) for i, j in [(0, 3), (1, 4), (2, 5)]]),
                     "ens3_vs_ens3": f1(ea, eb),
                     "notes_single": np.mean([len(r) for r in runs]), "notes_ens3": (len(ea) + len(eb)) / 2})
        full = vote(runs)  # 6-run ensemble saved for inspection
        pm = pretty_midi.PrettyMIDI()
        inst = pretty_midi.Instrument(0, name="game_ens6")
        inst.notes = [pretty_midi.Note(90, p, s, e) for s, e, p in full]
        pm.instruments.append(inst)
        (W / "midi" / "ens6").mkdir(parents=True, exist_ok=True)
        pm.write(str(W / "midi" / "ens6" / f"{f.stem}.mid"))
    d = pd.DataFrame(rows)
    d.to_csv(W / "ensemble.csv", index=False)
    print(d.describe().round(3).to_string())


if __name__ == "__main__":
    main()
