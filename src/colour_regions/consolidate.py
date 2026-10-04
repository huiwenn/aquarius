"""
Consolidate both collection rounds into one round-agnostic corpus layout, built from RELATIVE symlinks (no copies,
no moves; the per-round folders stay the working copies that the pipeline scripts write to).

  data/colour_regions/corpus/
    audio/<Region>/<id>.<ext>                 original downloads
    vocals/<Region>/<id>.wav, accomp/<Region>/<id>.wav
    midi/<variant>/<Region>/<id>.mid          variants: primary, game, game_pp, game_ens3_pp, rosvot, yourmt3
    musicxml/<variant>/<Region>/<id>.musicxml
    f0/{rmvpe,pesto}/<Region>/<id>.npz
    files.csv                                 one row per linked file (item_id, round, layer, variant, path)
  <Region> = English region name (e.g. Northwest_Plateau). `primary` points at each recording's primary transcription.

To upload real files (e.g. to a cloud drive): rsync -aL data/colour_regions/corpus/ <dest>/   (-L follows links)
Run (py312): python src/colour_regions/consolidate.py [--layers audio,midi,musicxml,f0,vocals,accomp]
"""

import argparse
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data"
OUT = D / "colour_regions" / "corpus"
ROUND = {1: dict(audio=D / "regions_audio", trans=D / "regions_transcription",
                 f0=D / "transcription" / "critic", index=D / "regions_transcription" / "dataset_index.csv"),
         2: dict(audio=D / "regions_v2" / "audio", trans=D / "regions_v2" / "transcription",
                 f0=D / "regions_v2" / "transcription", index=D / "regions_v2" / "transcription" / "dataset_index.csv")}
VARIANTS = ["game", "game_pp", "game_ens3_pp", "rosvot", "yourmt3"]
AUDIO_EXTS = {".webm", ".m4a", ".opus", ".mp3", ".ogg", ".mp4", ".wav", ".flac", ".aac"}


def slug(en: str) -> str:
    return en.replace("–", "-").replace(" ", "_")


def link(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    dst.symlink_to(os.path.relpath(src.resolve(), dst.parent))
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="audio,midi,musicxml,f0,vocals,accomp")
    layers = set(ap.parse_args().layers.split(","))
    rec = pd.read_csv(D / "colour_regions" / "recordings.csv")
    prim = {}
    for r, p in ROUND.items():
        if p["index"].exists():
            ix = pd.read_csv(p["index"])
            prim.update(dict(zip(ix.video_id, ix.transcription_model)))
    rows = []

    def add(item, rnd, layer, variant, src, dst):
        if link(src, dst):
            rows.append(dict(item_id=item, round=rnd, layer=layer, variant=variant,
                             path=str(dst.relative_to(OUT))))

    for r in rec.itertuples():
        p, reg, iid = ROUND[int(r.round)], r.region, r.item_id
        R = slug(r.region_en)
        if "audio" in layers:
            src = next((f for f in (p["audio"] / reg).glob(f"{iid}.*") if f.suffix in AUDIO_EXTS), None)
            if src:
                add(iid, r.round, "audio", "", src, OUT / "audio" / R / src.name)
        for stem in ("vocals", "accomp"):
            if stem in layers:
                add(iid, r.round, stem, "", p["trans"] / stem / reg / f"{iid}.wav", OUT / stem / R / f"{iid}.wav")
        for v in VARIANTS + ["primary"]:
            src_v = prim.get(iid) if v == "primary" else v
            if not isinstance(src_v, str):
                continue
            if "midi" in layers:
                add(iid, r.round, "midi", v, p["trans"] / "midi" / src_v / reg / f"{iid}.mid",
                    OUT / "midi" / v / R / f"{iid}.mid")
            if "musicxml" in layers:
                add(iid, r.round, "musicxml", v, p["trans"] / "musicxml" / src_v / reg / f"{iid}.musicxml",
                    OUT / "musicxml" / v / R / f"{iid}.musicxml")
        if "f0" in layers:
            for tr in ("rmvpe", "pesto"):
                add(iid, r.round, "f0", tr, p["f0"] / f"f0_{tr}" / reg / f"{iid}.npz", OUT / "f0" / tr / R / f"{iid}.npz")
    files = pd.DataFrame(rows)
    files.to_csv(OUT / "files.csv", index=False)
    print(files.groupby(["layer", "variant"]).size().to_string())
    miss = rec[~rec.item_id.isin(files[files.layer == "audio"].item_id)]
    print(f"\n{files.item_id.nunique()} recordings linked; {len(miss)} without audio")


if __name__ == "__main__":
    main()
