"""
Run the critic over the whole dataset with in-domain evidence (RMVPE + PESTO + stem dominance).

For every recording whose primary transcription is vocal (game_pp or rosvot):
  - per-note audit → data/transcription/critic/notes/<region>/<id>.csv
  - corrected variants → data/regions_transcription/midi/critic_<variant>/<region>/<id>.mid
      variants: repitch, delete, fill, all (all = repitch + delete + fill)
    repitch uses ROSVOT as the consensus second opinion (only when the primary is GAME)
  - summary row → data/transcription/critic/dataset_summary.csv
Instrumental recordings (YourMT3+ primary) are skipped: the vocal evidence doesn't apply to them.

Run (py312): python src/transcription/critic/run_dataset.py [--consensus true]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from critic import Evidence, Params, audit_notes, correct, missed_segments  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "data" / "regions_transcription"
C = ROOT / "data" / "transcription" / "critic"
VARIANTS = {"repitch": dict(repitch=True, delete=False, fill=False),
            "delete": dict(repitch=False, delete=True, fill=False),
            "fill": dict(repitch=False, delete=False, fill=True),
            "all": dict(repitch=True, delete=True, fill=True)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consensus", type=lambda x: x.lower() in ("1", "true", "yes"), default=True)
    args = ap.parse_args()
    params = Params(consensus=args.consensus)
    idx = pd.read_csv(T / "dataset_index.csv")
    idx = idx[idx.transcription_model.isin(["game_pp", "rosvot"])]
    rows = []
    for r in idx.itertuples():
        reg, vid = r.region, r.video_id
        ev = Evidence.load(C / "f0_rmvpe" / reg / f"{vid}.npz", C / "f0_pesto" / reg / f"{vid}.npz",
                           C / "dominance" / reg / f"{vid}.npz")
        primary = ROOT / r.midi_path
        second = ROOT / r.midi_rosvot_path if r.transcription_model == "game_pp" and isinstance(
            r.midi_rosvot_path, str) else None
        notes = sorted((n for i in pretty_midi.PrettyMIDI(str(primary)).instruments for n in i.notes),
                       key=lambda n: n.start)
        sec_notes = [n for i in pretty_midi.PrettyMIDI(str(second)).instruments for n in i.notes] if second else None
        audit = pd.DataFrame(audit_notes(notes, ev, params, sec_notes if params.consensus else None))
        (C / "notes" / reg).mkdir(parents=True, exist_ok=True)
        audit.to_csv(C / "notes" / reg / f"{vid}.csv", index=False)
        stats = {}
        for name, kw in VARIANTS.items():
            pm, s = correct(primary, ev, params, second_midi=second, **kw)
            out = T / "midi" / f"critic_{name}" / reg / f"{vid}.mid"
            out.parent.mkdir(parents=True, exist_ok=True)
            pm.write(str(out))
            if name == "all":
                stats = s
        missed_s = sum((j - i) * 0.01 for i, j in missed_segments(notes, ev, params))
        rows.append({"region": reg, "video_id": vid, "model": r.transcription_model,
                     "voiced_s": float((ev.rmvpe > 0).sum() * 0.01), "confident_s": float(ev.confident.sum() * 0.01),
                     "missed_s": missed_s, **stats})
        if len(rows) % 50 == 0:
            print(f"{len(rows)}/{len(idx)}", flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(C / "dataset_summary.csv", index=False)
    v = [c for c in d.columns if c.startswith("v_")]
    tot = d[v].sum()
    print("\nnote verdicts (all vocal recordings):")
    print((tot / tot.sum()).round(3).to_string())
    print("\nper region (fraction of notes):")
    print(d.groupby("region")[v].sum().div(d.groupby("region")[v].sum().sum(1), axis=0).round(3).to_string())
    print("\ncorrections applied:", d[["repitched", "octave", "deleted", "filled"]].sum().to_dict(),
          f"| missed confident-voiced time: {d.missed_s.sum() / 60:.1f} min of {d.voiced_s.sum() / 60:.1f} min voiced")


if __name__ == "__main__":
    main()
