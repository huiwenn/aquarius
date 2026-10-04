"""
Majority-vote the three GAME runs of every recording (midi/game, midi/game_run2, midi/game_run3)
→ midi/game_ens3/<region>/<id>.mid, then apply the 50 ms offset trim → midi/game_ens3_pp/<region>/<id>.mid.

Voting rule (audit/ensemble.py): same pitch, onsets within ±50 ms, present in ≥2 of 3 runs; median times;
monophony enforced. Validation: disjoint 3-run ensembles agree 0.897 vs 0.841 for single runs (45 recordings),
and vocadito COnP 0.587 → 0.600, COnPOff 0.366 → 0.380.

Run (py312): python src/transcription/ensemble_vote.py
"""

import os
import sys
from pathlib import Path

import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parent / "audit"))
from ensemble import vote  # noqa: E402
from melody import load_notes  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
M = Path(os.environ.get("AQ_TRANS", ROOT / "data" / "regions_transcription")) / "midi"
TRIM = 0.05


def write(notes, path: Path, trim: float) -> None:
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(0, name="game_ens3")
    inst.notes = [pretty_midi.Note(90, p, s, max(s + 0.03, e - trim)) for s, e, p in notes]
    pm.instruments.append(inst)
    path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(path))


def main() -> None:
    done = skipped = 0
    for f in sorted((M / "game").glob("*/*.mid")):
        region = f.parent.name
        runs = [f, M / "game_run2" / region / f.name, M / "game_run3" / region / f.name]
        out = M / "game_ens3_pp" / region / f.name
        if out.exists() or not all(p.exists() for p in runs):
            skipped += 1
            continue
        notes = vote([load_notes(p) for p in runs])
        write(notes, M / "game_ens3" / region / f.name, 0.0)
        write(notes, out, TRIM)
        done += 1
    print(f"voted {done}, skipped {skipped}")


if __name__ == "__main__":
    main()
