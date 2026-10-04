"""
Convert a monophonic vocal-melody MIDI (seconds-based model output) into MusicXML.

Model output MIDI has no meaningful tempo/meter (notes are placed in absolute time),
so we:
  1. estimate a beat grid from the source audio (librosa beat tracker),
  2. map each note onset/offset from seconds to beats by interpolating along that grid
     (this follows tempo drift, which is common in folk performance),
  3. quantize to a 16th-note / eighth-triplet grid, force a single line (a note is cut at the
     next onset; sub-16th ornaments are dropped), fill gaps with rests, and write MusicXML.
Pieces in free rhythm (散板, 长调, 信天游 openings) have no stable beat. For those the
result is a readable approximation, not a faithful rhythmic score. `beat_regularity`
(CV of inter-beat intervals) is saved so such pieces can be flagged.

Usage (py312 env):
  python src/transcription/midi_to_musicxml.py MIDI_DIR AUDIO_DIR OUT_DIR
"""

import argparse
import json
from pathlib import Path

import librosa
import music21 as m21
import numpy as np
import pretty_midi

EXTS = [".wav", ".webm", ".m4a", ".opus", ".mp3", ".flac", ".ogg", ".mp4"]


def beat_grid(audio: Path) -> tuple[np.ndarray, float, float]:
    y, sr = librosa.load(audio, sr=22050, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    tempo = float(np.atleast_1d(tempo)[0]) or 80.0
    if len(beats) < 4:
        dur = len(y) / sr
        beats = np.arange(0, dur + 60 / tempo, 60 / tempo)
    ibi = np.diff(beats)
    regularity = float(np.std(ibi) / np.mean(ibi)) if len(ibi) else float("nan")
    return beats, tempo, regularity


def sec_to_beat(t: np.ndarray, beats: np.ndarray) -> np.ndarray:
    # linear interpolation inside the grid, constant-tempo extrapolation outside it
    idx = np.arange(len(beats), dtype=float)
    lo = (t - beats[0]) / (beats[1] - beats[0])
    hi = (len(beats) - 1) + (t - beats[-1]) / (beats[-1] - beats[-2])
    return np.where(t < beats[0], lo, np.where(t > beats[-1], hi, np.interp(t, beats, idx)))


GRID = np.array([0, 1 / 4, 1 / 3, 1 / 2, 2 / 3, 3 / 4, 1])  # 16ths + eighth-triplets within a beat


def quantize(x: np.ndarray) -> np.ndarray:
    base = np.floor(x)
    frac = x - base
    return base + GRID[np.abs(frac[:, None] - GRID[None, :]).argmin(1)]


def convert(midi: Path, audio: Path, out: Path, title: str) -> dict:
    pm = pretty_midi.PrettyMIDI(str(midi))
    notes = sorted((n for inst in pm.instruments if not inst.is_drum for n in inst.notes),
                   key=lambda n: n.start)
    beats, tempo, regularity = beat_grid(audio)
    part = m21.stream.Part()
    part.append(m21.instrument.Vocalist())
    part.append(m21.tempo.MetronomeMark(number=round(tempo)))
    if notes:
        on = sec_to_beat(np.array([n.start for n in notes]), beats)
        off = sec_to_beat(np.array([n.end for n in notes]), beats)
        origin = np.floor(on.min())
        on, off = quantize(on - origin), quantize(off - origin)
        cursor = 0.0
        for i, n in enumerate(notes):
            start = max(on[i], cursor)                      # enforce monophony
            end = off[i] if i + 1 == len(notes) else min(off[i], on[i + 1])
            if end - start < 1 / 4 - 1e-6:                  # too short after quantization
                end = start + 1 / 4
                if i + 1 < len(notes) and end > on[i + 1] + 1e-6:
                    continue                                # swallowed by next note (ornament)
            if start - cursor > 1e-6:
                part.append(m21.note.Rest(quarterLength=m21.common.opFrac(start - cursor)))
            part.append(m21.note.Note(n.pitch, quarterLength=m21.common.opFrac(end - start)))
            cursor = end
    score = m21.stream.Score()
    score.insert(0, m21.metadata.Metadata(title=title))
    score.insert(0, part.makeMeasures())
    score = score.makeNotation()
    out.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(out))
    return {"tempo_bpm": round(tempo, 1), "beat_regularity_cv": round(regularity, 3),
            "n_notes_midi": len(notes), "free_rhythm_suspect": bool(regularity > 0.25)}


def find_audio(audio_dir: Path, stem: str) -> Path | None:
    for ext in EXTS:
        if (audio_dir / f"{stem}{ext}").exists():
            return audio_dir / f"{stem}{ext}"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("midi_dir", type=Path)
    ap.add_argument("audio_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()
    stats = {}
    for midi in sorted(args.midi_dir.glob("*.mid")):
        out = args.out_dir / f"{midi.stem}.musicxml"
        audio = find_audio(args.audio_dir, midi.stem)
        if out.exists() or audio is None:
            continue
        try:
            stats[midi.stem] = convert(midi, audio, out, midi.stem)
        except Exception as e:  # keep going; report at the end
            stats[midi.stem] = {"error": str(e)[:200]}
        print(midi.stem, stats[midi.stem], flush=True)
    stats_path = args.out_dir / "_musicxml_stats.json"
    prev = json.loads(stats_path.read_text()) if stats_path.exists() else {}
    stats_path.write_text(json.dumps(prev | stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
