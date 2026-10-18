"""
Build the Hugging Face release folder of Colour Regions (links + derived data; NO audio) in data/hf_release/.

  README.md                         dataset card (written from docs/hf_dataset_card.md, numbers filled from the data)
  data/recordings.parquet           one row per recording: metadata (as metadata/recordings.csv, minus the internal
                                    `fold`), transcription QC, and repo-relative paths to the derived files below.
                                    feature_flags is a list column here (`;`-separated string in metadata/).
  data/song_labels.parquet          one row per song: class, genre, composer, period, evidence, sources, confidence
  data/anthology_overlap.parquet    songs also printed in the Anthology of Chinese Folk Songs
  data/scores.parquet               Anthology and Essen scores mapped to the colour regions (statistics only)
  data/score_matches.parquet        recording <-> score title matches
  data/fingerprints.parquet         Chromaprint fingerprints (first 120 s) to verify re-downloaded audio
  data/link_status.parquet          latest link check (if present)
  midi/{primary,game,rosvot}/<Region>/<id>.mid      primary transcription + two alternative model outputs
  musicxml/primary/<Region>/<id>.musicxml           primary transcription as quantised notation (metre nominal)
  f0/{rmvpe,pesto}/<Region>/<id>.npz                F0 of the separated voice, 10 ms hop (pesto: + confidence)

Files are copied (symlinks resolved). Re-runnable: the folder is rebuilt from scratch each time.
Run (py312): python src/colour_regions/build_hf.py
Upload:      hf upload sophiaphia/colour-regions data/hf_release . --type dataset --private
"""

import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "colour_regions"
CORPUS = SRC / "corpus"
OUT = ROOT / "data" / "hf_release"
# corpus view variant → release folder name. `game` in the release = the single GAME run with the 50 ms offset trim
MIDI = {"primary": "primary", "game_pp": "game", "rosvot": "rosvot"}
QC = ["transcription_model", "n_notes", "notes_per_s", "vocal_db", "game_rosvot_agreement", "sung_share",
      "music_share"]


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    meta = pd.read_csv(ROOT / "metadata" / "recordings.csv").drop(columns=["fold"], errors="ignore")
    full = pd.read_csv(SRC / "recordings.csv").set_index("item_id")
    for c in QC:
        if c in full:
            meta[c] = meta.item_id.map(full[c])
    meta["feature_flags"] = meta.feature_flags.map(lambda s: [] if pd.isna(s) else s.split(";"))

    files = pd.read_csv(CORPUS / "files.csv")
    paths = {}
    copied = 0
    for r in files.itertuples():
        if r.layer == "midi" and r.variant in MIDI:
            rel = Path("midi") / MIDI[r.variant] / Path(r.path).relative_to(Path("midi") / r.variant)
            col = f"midi_{MIDI[r.variant]}"
        elif r.layer == "musicxml" and r.variant == "primary":
            rel, col = Path(r.path), "musicxml_primary"
        elif r.layer == "f0":
            rel, col = Path(r.path), f"f0_{r.variant}"
        else:
            continue
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile((CORPUS / r.path).resolve(), dst)
        paths.setdefault(col, {})[r.item_id] = str(rel)
        copied += 1
    for col in ("midi_primary", "midi_game", "midi_rosvot", "musicxml_primary", "f0_rmvpe", "f0_pesto"):
        meta[col] = meta.item_id.map(paths.get(col, {}))
    meta.to_parquet(OUT / "data" / "recordings.parquet", index=False)

    tables = {"song_labels": ROOT / "metadata" / "song_labels.csv",
              "anthology_overlap": ROOT / "metadata" / "anthology_overlap.csv",
              "scores": SRC / "scores.csv", "score_matches": SRC / "score_matches.csv",
              "fingerprints": SRC / "fingerprints.csv", "link_status": ROOT / "metadata" / "link_status.csv"}
    for name, p in tables.items():
        if p.exists():
            pd.read_csv(p).to_parquet(OUT / "data" / f"{name}.parquet", index=False)

    card = (ROOT / "docs" / "hf_dataset_card.md").read_text()
    n = dict(N_REC=len(meta), N_CORE=int((meta.subset == "core").sum()),
             N_FSC=int((meta.subset == "folk_style_composed").sum()),
             N_SONGS=len(pd.read_csv(tables["song_labels"])), HOURS=f"{meta.duration_s.sum() / 3600:.1f}",
             N_YT=int((meta.platform == "youtube").sum()), N_BILI=int((meta.platform == "bilibili").sum()),
             N_EU=int((meta.platform == "europeana").sum()),
             N_OVERLAP=pd.read_csv(tables["anthology_overlap"]).query("verdict == 'match'").song_id.nunique())
    for k, v in n.items():
        card = card.replace("{" + k + "}", str(v))
    (OUT / "README.md").write_text(card)
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"{len(meta)} recordings; {copied} derived files; {size:.0f} MB → {OUT}")
    print({c: int(meta[c].notna().sum()) for c in ("midi_primary", "midi_game", "midi_rosvot", "musicxml_primary",
                                                    "f0_rmvpe", "f0_pesto")})


if __name__ == "__main__":
    main()
