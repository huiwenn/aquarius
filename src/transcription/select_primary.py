"""
Choose each recording's primary transcription with explicit, documented rules, and make sure it
has MIDI + MusicXML.

Coverage = total note duration / recording duration.
Rules, applied in order:
  1. instrumental     GAME found no singing (no/empty MIDI), or GAME cov < 0.05 and ROSVOT cov < 0.10
                      (the melody is carried by instruments, e.g. 堆谐 song-and-dance with brief calls)
                      → YourMT3+ on the full mix
  2. vocal_rosvot     GAME cov < 0.15 and ROSVOT cov > max(0.20, 2 × GAME cov)
                      (GAME clearly misses sung material that ROSVOT captures)
                      → ROSVOT
  3. vocal_game       otherwise → GAME (3-run majority-vote ensemble when available) + 50 ms offset trim

Writes data/regions_transcription/primary_selection.csv (video_id, region, primary, reason, coverages),
which build_dataset_index.py reads.
Run from a native arm64 python with pandas + pretty_midi (e.g. ~/miniforge3/envs/sep/bin/python).
"""

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transcribe_regions import game_processed  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
T = Path(os.environ.get("AQ_TRANS", ROOT / "data" / "regions_transcription"))  # v2: data/regions_v2/transcription
MANIFEST = Path(os.environ.get("AQ_MANIFEST", ROOT / "data" / "regions_audio" / "manifest.csv"))  # v2: data/regions_v2/manifest.csv
PY312 = "/usr/local/Caskroom/miniforge/base/envs/py312/bin/python"
YMT3 = [str(Path.home() / "miniforge3" / "envs" / "ymt3" / "bin" / "python"),
        "src/transcription/models/yourmt3/transcribe.py"]


def coverage(p: Path, dur: float) -> float:
    if not p.exists() or not dur:
        return 0.0
    return sum(n.end - n.start for i in pretty_midi.PrettyMIDI(str(p)).instruments for n in i.notes) / dur


def main() -> None:
    df = pd.read_csv(MANIFEST)
    df = df[df.status == "ok"]
    rows, processed = [], {}
    for r in df.itertuples():
        dur = r.duration_s_actual if pd.notna(r.duration_s_actual) else r.duration_s
        game_model = "game_ens3_pp" if (T / "midi" / "game_ens3_pp" / r.region / f"{r.video_id}.mid").exists() \
            else "game_pp"  # 3-run ensemble when available (docs §7.6)
        g = coverage(T / "midi" / game_model / r.region / f"{r.video_id}.mid", dur)
        ro = coverage(T / "midi" / "rosvot" / r.region / f"{r.video_id}.mid", dur)
        done = processed.setdefault(r.region, game_processed(T / "midi" / "game" / r.region))
        if g == 0 and done is not None and r.video_id not in done:
            # GAME never processed this recording (e.g. a crashed run): not evidence of "no singing"
            print(f"WARNING not transcribed by GAME yet: {r.region}/{r.video_id}", flush=True)
            primary, reason = None, "not_transcribed"
        elif g == 0 or (g < 0.05 and ro < 0.10):
            primary, reason = "yourmt3", "instrumental"
        elif g < 0.15 and ro > max(0.20, 2 * g):
            primary, reason = "rosvot", "vocal_rosvot"
        else:
            primary, reason = game_model, "vocal_game"
        rows.append({"video_id": r.video_id, "region": r.region, "primary": primary, "reason": reason,
                     "game_cov": round(g, 3), "rosvot_cov": round(ro, 3)})
    sel = pd.DataFrame(rows)

    # make sure every chosen primary has MIDI and MusicXML
    for (model, region), grp in sel[~sel.primary.isin(["game_pp", "game_ens3_pp"])].groupby(["primary", "region"]):
        audio = T / "audio" / region
        midi = T / "midi" / model / region
        if model == "yourmt3":
            todo = [v for v in grp.video_id if not (midi / f"{v}.mid").exists()]
            if todo:
                inp = T / "instrumental_input" / region
                inp.mkdir(parents=True, exist_ok=True)
                for v in todo:
                    src = next(audio.glob(f"{v}.*"))
                    try:
                        (inp / src.name).symlink_to(os.path.relpath(src.resolve(), inp))
                    except FileExistsError:
                        pass
                midi.mkdir(parents=True, exist_ok=True)
                subprocess.run(YMT3 + [str(inp), str(midi)], check=True, cwd=ROOT)
        # MusicXML for the chosen items (midi_to_musicxml skips existing outputs)
        stage = T / "_xml_stage" / model / region
        stage.mkdir(parents=True, exist_ok=True)
        for v in grp.video_id:
            try:
                (stage / f"{v}.mid").symlink_to(os.path.relpath((midi / f"{v}.mid").resolve(), stage))
            except FileExistsError:
                pass
        subprocess.run([PY312, "src/transcription/midi_to_musicxml.py", str(stage), str(audio),
                        str(T / "musicxml" / model / region)], check=True, cwd=ROOT)

    sel.to_csv(T / "primary_selection.csv", index=False)
    print(sel.reason.value_counts().to_string())


if __name__ == "__main__":
    main()
