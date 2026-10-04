"""
Post-process GAME vocal MIDI: trim every note offset by a constant.

GAME notes end systematically late (median +40 ms on vocadito, +60 ms on M4Singer/GTSinger).
A constant trim was chosen by 2-fold singer-disjoint cross-validation on vocadito
(best folds: 40 ms, 60 ms → CV COnPOff 0.299 → 0.357) and confirmed on M4Singer/GTSinger
(0.115 → 0.150 at 40–60 ms). 50 ms is used. Onsets and pitches are untouched, so COnP is unchanged.

Usage: python src/transcription/postprocess.py IN_MIDI_DIR OUT_MIDI_DIR [--trim 0.05]
"""

import argparse
from pathlib import Path

import pretty_midi

MIN_DUR = 0.03


def trim(src: Path, dst: Path, amount: float) -> None:
    pm = pretty_midi.PrettyMIDI(str(src))
    for inst in pm.instruments:
        for n in inst.notes:
            n.end = max(n.start + MIN_DUR, n.end - amount)
    dst.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(dst))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--trim", type=float, default=0.05)
    args = ap.parse_args()
    n = 0
    for f in sorted(args.in_dir.glob("*.mid")):
        out = args.out_dir / f.name
        if not out.exists() or out.stat().st_mtime < f.stat().st_mtime:
            trim(f, out, args.trim)
            n += 1
    print(f"trimmed {n} files → {args.out_dir}")


if __name__ == "__main__":
    main()
