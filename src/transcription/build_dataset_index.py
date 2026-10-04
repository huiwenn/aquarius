"""
Build the final index of the 色彩区 folk-song audio + transcription dataset.

One row per curated recording with audio on disk:
  curation metadata (region, rank, song_name, genre, performance_type, ethnic_group, url, channel ...),
  paths (audio, vocals, accompaniment, primary MIDI + MusicXML chosen by select_primary.py
  (game_pp by default; rosvot or yourmt3 by explicit coverage rules), GAME and ROSVOT MIDI),
  and QC signals:
    vocal_db            vocals RMS − accompaniment RMS (dB); very low → mostly instrumental
    n_notes, notes_per_s
    game_rosvot_conp    note F1 (onset ±100 ms, pitch ±50 c) between the two independent transcriptions.
                        Low agreement flags recordings whose transcription deserves a manual look.
    tempo_bpm, free_rhythm_suspect (from midi_to_musicxml)

Writes data/regions_transcription/dataset_index.csv and prints a per-region summary.
Run: python src/transcription/build_dataset_index.py   (py312 env)
"""

import os
import json
from pathlib import Path

import mir_eval
import numpy as np
import pandas as pd
import pretty_midi
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = Path(os.environ.get("AQ_MANIFEST", ROOT / "data" / "regions_audio" / "manifest.csv"))  # v2: data/regions_v2/manifest.csv
T = Path(os.environ.get("AQ_TRANS", ROOT / "data" / "regions_transcription"))  # v2: data/regions_v2/transcription


def notes(path: Path) -> np.ndarray:
    if not path.exists():
        return np.zeros((0, 3))
    pm = pretty_midi.PrettyMIDI(str(path))
    n = [(x.start, x.end, x.pitch) for i in pm.instruments for x in i.notes if x.end > x.start]
    return np.array(sorted(n)) if n else np.zeros((0, 3))


def agreement(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    return mir_eval.transcription.precision_recall_f1_overlap(
        a[:, :2], mir_eval.util.midi_to_hz(a[:, 2]), b[:, :2], mir_eval.util.midi_to_hz(b[:, 2]),
        onset_tolerance=0.1, offset_ratio=None)[2]


def rms_db(path: Path) -> float:
    if not path.exists():
        return float("nan")
    x, _ = sf.read(path, always_2d=True)
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9))


def rel(p: Path) -> str | None:
    p = p if p.is_absolute() else ROOT / p  # AQ_TRANS may be relative to the repo root
    return str(p.relative_to(ROOT)) if p.exists() else None


def main() -> None:
    df = pd.read_csv(MANIFEST)
    df = df[df.status == "ok"].copy()
    xml_stats = {}
    for f in (T / "musicxml").glob("*/*/_musicxml_stats.json"):
        xml_stats.update(json.loads(f.read_text()))

    sel_path = T / "primary_selection.csv"  # written by select_primary.py
    sel = pd.read_csv(sel_path).set_index("video_id") if sel_path.exists() else pd.DataFrame()

    rows = []
    for r in df.itertuples():
        vid, reg = r.video_id, r.region
        model = sel.loc[vid, "primary"] if vid in sel.index else "game_pp"
        reason = sel.loc[vid, "reason"] if vid in sel.index else None
        g = T / "midi" / model / reg / f"{vid}.mid"
        gp = T / "midi" / "game_pp" / reg / f"{vid}.mid"
        ro = T / "midi" / "rosvot" / reg / f"{vid}.mid"
        voc, acc = T / "vocals" / reg / f"{vid}.wav", T / "accomp" / reg / f"{vid}.wav"
        xml = T / "musicxml" / model / reg / f"{vid}.musicxml"
        gn, rn = notes(gp), notes(ro)  # agreement is always GAME vs ROSVOT
        pn = notes(g)
        dur = r.duration_s_actual if pd.notna(r.duration_s_actual) else r.duration_s
        st = xml_stats.get(vid, {})
        rows.append({
            **{k: getattr(r, k) for k in df.columns if k in (
                "region", "rank", "video_id", "url", "title", "channel", "song_name", "genre",
                "performance_type", "ethnic_group", "province_or_area", "upload_date", "license", "note")},
            "duration_s": dur,
            "audio_path": r.audio_path,
            "vocals_path": rel(voc), "accomp_path": rel(acc),
            "transcription_model": model if g.exists() else None, "selection_reason": reason,
            "midi_game_path": rel(gp),
            "midi_path": rel(g), "midi_rosvot_path": rel(ro), "musicxml_path": rel(xml),
            "vocal_db": rms_db(voc) - rms_db(acc),
            "n_notes": len(pn), "notes_per_s": len(pn) / dur if dur else np.nan,
            "game_rosvot_conp": agreement(gn, rn),
            "tempo_bpm": st.get("tempo_bpm"), "free_rhythm_suspect": st.get("free_rhythm_suspect"),
        })
    out = pd.DataFrame(rows).sort_values(["region", "rank"])
    out.to_csv(T / "dataset_index.csv", index=False)

    done = out.midi_path.notna() & out.musicxml_path.notna()
    summ = out.assign(transcribed=done).groupby("region").agg(
        recordings=("video_id", "count"), transcribed=("transcribed", "sum"),
        songs=("song_name", "nunique"), hours=("duration_s", lambda s: round(s.sum() / 3600, 2)),
        median_agreement=("game_rosvot_conp", "median"))
    print(summ.to_string())
    print(f"\nTOTAL recordings {len(out)}, transcribed {int(done.sum())}, "
          f"{out.duration_s.sum() / 3600:.1f} h; regions with ≥30 transcribed: "
          f"{int((summ.transcribed >= 30).sum())}/{len(summ)}")


if __name__ == "__main__":
    main()
