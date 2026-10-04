"""
Transcribe every downloaded 色彩区 recording: separation → vocal-melody MIDI → MusicXML.

Inputs : data/regions_audio/manifest.csv (status == ok) and the audio it points to
Outputs: data/regions_transcription/
           audio/<region>/<id>.<ext>          symlinks to the curated audio only
           vocals/<region>/<id>.wav           htdemucs separated vocals (see docs/transcription.md §4.1)
           accomp/<region>/<id>.wav           separated accompaniment (kept for later work)
           midi/<model>/<region>/<id>.mid      vocal melody (raw model output)
           midi/game_pp/<region>/<id>.mid      GAME + 50 ms offset trim  ← primary transcription
           musicxml/<model>/<region>/<id>.musicxml   (for game: built from game_pp)
           midi/yourmt3/<region>/<id>.mid      fallback for instrumental recordings (no singing found)
Each step skips outputs that already exist, so the script can be rerun as downloads arrive.

Each model runner executes in its own arm64 conda env (see docs/transcription.md).
Run from repo root with a NATIVE arm64 python (child processes inherit the architecture;
launched from the x86 py312, audio-separator sees "i386" and silently falls back to CPU):
  ~/miniforge3/envs/sep/bin/python src/transcription/transcribe_regions.py [--models game,rosvot] [--steps sep,midi,xml]
"""

import os
import argparse
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
ENVS = Path.home() / "miniforge3" / "envs"
MANIFEST = Path(os.environ.get("AQ_MANIFEST", ROOT / "data" / "regions_audio" / "manifest.csv"))  # v2: data/regions_v2/manifest.csv
OUT = Path(os.environ.get("AQ_TRANS", ROOT / "data" / "regions_transcription"))  # v2: data/regions_v2/transcription
PY312 = "/usr/local/Caskroom/miniforge/base/envs/py312/bin/python"
M = ROOT / "src" / "transcription" / "models"

# model name → (command template, input kind). {inp}/{out} are directories.
MODELS = {
    "rosvot": (["/usr/local/Caskroom/miniforge/base/envs/rosvot/bin/python", str(M / "rosvot" / "run_rosvot.py"), "{inp}", "{out}"], "vocals"),
    "game": ([str(ENVS / "game" / "bin" / "python"), str(M / "game" / "run_game.py"), "{inp}", "{out}",
              "--size", "medium", "--lang", "zh", "--seg-threshold", "0.1"], "vocals"),
    "some": ([str(ENVS / "some" / "bin" / "python"), str(M / "some" / "run_some.py"), "{inp}", "{out}",
              "--ckpt", "0119"], "vocals"),
    "yourmt3": ([str(ENVS / "ymt3" / "bin" / "python"), str(M / "yourmt3" / "transcribe.py"), "{inp}", "{out}",
                 "--model", "moe_ps", "--device", "cpu"], "audio"),   # multi-track, on the full mix
    "basic_pitch": ([str(ENVS / "basicpitch" / "bin" / "python"), str(M / "basic_pitch" / "transcribe.py"),
                     "{inp}", "{out}"], "vocals"),
}


POSTPROCESS = {"game": "game_pp"}


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def game_processed(midi_dir: Path) -> set[str] | None:
    """Stems that a successful GAME call processed (run_game.py writes _processed.txt), or None for older
    outputs (round 1) that predate the record — then a missing MIDI is taken to mean "no singing", as before."""
    p = midi_dir / "_processed.txt"
    return set(p.read_text().split()) if p.exists() else None


def instrumental_fallback(region: str, audio: Path, vocal_midi: Path, xml: bool) -> None:
    """Recordings where GAME found no singing (separated vocals ~silent: instrumental folk tunes)
    are transcribed from the full mix with YourMT3+ (multi-instrument) instead."""
    import pretty_midi  # only needed here (pip install pretty_midi in the sep env)

    def no_notes(p: Path) -> bool:
        if not p.exists():
            # judge by the raw GAME output: a missing post-processed file (e.g. after an interrupted run) is not
            # evidence of "no singing"
            raw = OUT / "midi" / "game" / region / p.name
            return not raw.exists() or sum(len(i.notes) for i in pretty_midi.PrettyMIDI(str(raw)).instruments) == 0
        empty = sum(len(i.notes) for i in pretty_midi.PrettyMIDI(str(p)).instruments) == 0
        if empty:  # GAME wrote an empty file: drop it (and its score) so the fallback owns this item
            p.unlink()
            xml = OUT / "musicxml" / "game_pp" / region / f"{p.stem}.musicxml"
            xml.unlink(missing_ok=True)
        return empty

    done = game_processed(OUT / "midi" / "game" / region)
    missing = [f for f in audio.iterdir() if (done is None or f.stem in done)
               and no_notes(vocal_midi / f"{f.stem}.mid")]
    if not missing:
        return
    inp = OUT / "instrumental_input" / region
    inp.mkdir(parents=True, exist_ok=True)
    for f in missing:
        try:
            (inp / f.name).symlink_to(os.path.relpath(f.resolve(), inp))
        except FileExistsError:
            pass
    out = OUT / "midi" / "yourmt3" / region
    out.mkdir(parents=True, exist_ok=True)
    cmd, _ = MODELS["yourmt3"]
    run([c.format(inp=inp, out=out) for c in cmd])
    if xml:  # monophonic reduction (a note is cut at the next onset) → melody-line MusicXML
        run([PY312, "src/transcription/midi_to_musicxml.py", str(out), str(audio),
             str(OUT / "musicxml" / "yourmt3" / region)])


def stage_audio(df: pd.DataFrame) -> list[str]:
    regions = []
    for r in df.itertuples():
        d = OUT / "audio" / r.region
        d.mkdir(parents=True, exist_ok=True)
        src = ROOT / r.audio_path
        link = d / src.name
        try:
            link.symlink_to(os.path.relpath(src, d))  # relative: survives moving the repo
        except FileExistsError:  # already staged (or staged concurrently by the CPU-side process)
            pass
        regions.append(r.region)
    return sorted(set(regions))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="game,rosvot")
    ap.add_argument("--steps", default="sep,midi,xml")
    ap.add_argument("--regions", default=None, help="comma-separated subset")
    ap.add_argument("--only-ready", action="store_true",
                    help="skip regions whose separation is incomplete (for a second, CPU-side process "
                         "running e.g. --models rosvot --steps midi,xml alongside the GPU-side one)")
    args = ap.parse_args()
    steps = args.steps.split(",")

    df = pd.read_csv(MANIFEST)
    df = df[df.status == "ok"]
    if args.regions:
        df = df[df.region.isin(args.regions.split(","))]
    regions = stage_audio(df)
    print(f"{len(df)} recordings in {len(regions)} regions")

    for region in regions:
        audio, vocals = OUT / "audio" / region, OUT / "vocals" / region
        if args.only_ready and len(list(vocals.glob("*.wav"))) < len(list(audio.iterdir())):
            print(f"skip {region}: separation incomplete", flush=True)
            continue
        if "sep" in steps:
            run([str(ENVS / "sep" / "bin" / "python"), "src/transcription/separate.py",
                 str(audio), str(vocals), "--keep-accomp", "--model", "htdemucs.yaml"])
            acc_src = vocals / "accomp"
            if acc_src.exists():  # move accompaniment next to vocals/ rather than inside it
                acc_dst = OUT / "accomp" / region
                acc_dst.mkdir(parents=True, exist_ok=True)
                for f in acc_src.iterdir():
                    f.rename(acc_dst / f.name)
                acc_src.rmdir()
        for model in args.models.split(","):
            cmd, kind = MODELS[model]
            inp = vocals if kind == "vocals" else audio
            midi = OUT / "midi" / model / region
            if "midi" in steps:
                midi.mkdir(parents=True, exist_ok=True)
                run([c.format(inp=inp, out=midi) for c in cmd])
            if model in POSTPROCESS:  # e.g. game → game_pp (offset trim, see postprocess.py)
                pp = OUT / "midi" / POSTPROCESS[model] / region
                if "midi" in steps or "pp" in steps:
                    run([PY312, "src/transcription/postprocess.py", str(midi), str(pp)])
                midi, model = pp, POSTPROCESS[model]
            if "xml" in steps:
                run([PY312, "src/transcription/midi_to_musicxml.py", str(midi), str(audio),
                     str(OUT / "musicxml" / model / region)])
            if model == "game_pp" and ("midi" in steps or "fallback" in steps):
                instrumental_fallback(region, audio, midi, "xml" in steps)


if __name__ == "__main__":
    main()
