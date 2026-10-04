"""
Build the human-audited gold set: a stratified sample of the critic's decisions, with blinded A/B tones.

Strata (per region, round-robin, seed 0):
  repitch  critic changed the pitch (wrong_pitch + ROSVOT consensus)   → A/B = original vs corrected
  ok       critic judged the note correct                              → A/B = original vs ±1 st foil
  uncertain critic couldn't judge                                      → A/B = original vs ±1 st foil
  fill     critic added a note in an uncovered voiced segment          → A/B = added pitch vs ±1 st foil
  delete   critic removed a note as unvoiced                           → A/B = removed pitch vs ±1 st foil
Tones are played at MIDI pitch + the recording's tuning offset, so A/B compare in the singer's own tuning.
Each item gets a clip of the *separated vocals* from note start − 1 s to note end + 1 s (mp3, 64 kbps mono).

Output: data/transcription/audit/gold/{clips/<item>.mp3, items.json}
Run (py312): python src/transcription/audit/gold_sample.py [--n 150]
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "critic"))
from critic import Evidence, tuning_offset  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
T = ROOT / "data" / "regions_transcription"
C = ROOT / "data" / "transcription" / "critic"
OUT = ROOT / "data" / "transcription" / "audit" / "gold"
QUOTA = {"repitch": 60, "ok": 30, "uncertain": 20, "fill": 25, "delete": 15}


def notes_of(p: Path):
    return sorted(((n.start, n.end, n.pitch) for i in pretty_midi.PrettyMIDI(str(p)).instruments
                   for n in i.notes), key=lambda x: x[0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    scale = args.n / sum(QUOTA.values())
    quota = {k: max(1, round(v * scale)) for k, v in QUOTA.items()}

    idx = pd.read_csv(T / "dataset_index.csv")
    idx = idx[idx.transcription_model == "game_pp"]
    pools = {k: [] for k in quota}
    for r in idx.itertuples():
        reg, vid = r.region, r.video_id
        a = pd.read_csv(C / "notes" / reg / f"{vid}.csv")
        a = a[(a.end - a.start) >= 0.15]  # too-short notes can't be judged by ear
        for row in a.itertuples():
            v = row.verdict
            if v in ("wrong_pitch", "octave_error") and row.second_agrees is True or str(row.second_agrees) == "True":
                if v in ("wrong_pitch", "octave_error"):
                    pools["repitch"].append((reg, vid, row.start, row.end, int(row.pitch), int(row.target)))
                    continue
            if v == "ok":
                pools["ok"].append((reg, vid, row.start, row.end, int(row.pitch), None))
            elif v == "uncertain":
                pools["uncertain"].append((reg, vid, row.start, row.end, int(row.pitch), None))
            elif v == "unvoiced":
                pools["delete"].append((reg, vid, row.start, row.end, int(row.pitch), None))
        # filled notes = notes in critic_fill not present in the primary
        prim = {(round(s, 2), p) for s, e, p in notes_of(ROOT / r.midi_path)}
        for s, e, p in notes_of(T / "midi" / "critic_fill" / reg / f"{vid}.mid"):
            if (round(s, 2), p) not in prim and e - s >= 0.15:
                pools["fill"].append((reg, vid, s, e, p, None))

    items = []
    for stratum, k in quota.items():
        by_reg = {}
        for x in pools[stratum]:
            by_reg.setdefault(x[0], []).append(x)
        for v in by_reg.values():
            rng.shuffle(v)
        regs = sorted(by_reg)
        rng.shuffle(regs)
        chosen, i = [], 0
        while len(chosen) < k and any(by_reg.values()):
            reg = regs[i % len(regs)]
            if by_reg[reg]:
                chosen.append(by_reg[reg].pop())
            i += 1
        for reg, vid, s, e, p, target in chosen:
            items.append((stratum, reg, vid, s, e, p, target))

    (OUT / "clips").mkdir(parents=True, exist_ok=True)
    tau_cache, out = {}, []
    rng.shuffle(items)
    for n, (stratum, reg, vid, s, e, p, target) in enumerate(items):
        item_id = f"g{n:03d}"
        if (reg, vid) not in tau_cache:
            ev = Evidence.load(C / "f0_rmvpe" / reg / f"{vid}.npz", C / "f0_pesto" / reg / f"{vid}.npz",
                               C / "dominance" / reg / f"{vid}.npz")
            tau_cache[(reg, vid)] = tuning_offset(ev)
        tau = tau_cache[(reg, vid)]
        other = target if stratum == "repitch" else p + rng.choice([-1, 1])
        options = [("original" if stratum in ("repitch", "ok", "uncertain") else stratum, p),
                   ("corrected" if stratum == "repitch" else "foil", other)]
        rng.shuffle(options)
        t0 = max(0.0, s - 1.0)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{t0:.3f}",
                        "-t", f"{(e - s) + 2.0:.3f}", "-i", str(T / "vocals" / reg / f"{vid}.wav"),
                        "-ac", "1", "-ar", "22050", "-b:a", "64k", str(OUT / "clips" / f"{item_id}.mp3")], check=True)
        out.append({"id": item_id, "stratum": stratum, "region": reg, "video_id": vid,
                    "note_start": round(s, 3), "note_end": round(e, 3), "clip_offset": round(s - t0, 3),
                    "tuning": round(tau, 3),
                    "A": {"role": options[0][0], "midi": int(options[0][1])},
                    "B": {"role": options[1][0], "midi": int(options[1][1])}})
    (OUT / "items.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(pd.Series([o["stratum"] for o in out]).value_counts().to_string())
    print(f"{len(out)} items → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
