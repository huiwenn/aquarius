"""
Conversion helpers for the pretrained-embedding family: corpus notes → text formats that pretrained symbolic
models consume.

  to_mtf(notes, time_unit)   MIDI Text Format (CLaMP 2/3, M3): notes → mido MIDI (480 tpb, 120 bpm; 1 beat =
                             1 quarter, 1 sec = 2 quarters) → the same `msg_to_str` serialization as
                             third_party/clamp3/preprocessing/midi/batch_midi2mtf.py (m3_compatible).
  to_abc(notes, time_unit)   Interleaved ("rotated") ABC as produced by CLaMP's batch_interleaved_abc.py for a
                             single voice: header, then one `[V:1]<bar>|` line per bar. L:1/8, M:4/4 (the corpus
                             has no meter, so bars are a fixed 4/4 grid), K:C, sharps only, 16th-note grid.
                             Seconds (transcriptions) are converted to beats by setting the median IOI = an 8th.
  to_degrees(notes, time_unit) 简谱-like scale-degree string ("1 2 3 #4 5 6 7", ' / , octave marks, '-' holds),
                             relative to C of the given pitches — pass tonic-normalized notes for movable-do.
  tonic_normalize(notes)     transpose so estimated 宫 (regionclf.features.estimate_gong) = C, shift in [-6, 5].

Pure numpy + mido; importable from both envs.
"""

import numpy as np

from regionclf.features import estimate_gong


def tonic_normalize(notes: np.ndarray) -> np.ndarray:
    g = estimate_gong(notes)
    shift = -g if g <= 6 else 12 - g  # nearest transposition that puts 宫 on C
    out = notes.copy()
    out[:, 2] = out[:, 2] + shift
    return out


def to_beats(notes: np.ndarray, time_unit: str) -> np.ndarray:
    if time_unit == "beat":
        return notes
    ioi = np.diff(notes[:, 0])
    med = np.median(ioi[ioi > 1e-3]) if (ioi > 1e-3).any() else 0.25
    scale = 0.5 / max(med, 1e-3)  # median IOI → an eighth note
    out = notes.copy()
    out[:, :2] *= scale
    return out


# ------------------------------------------------------------------ MTF
def _msg_to_str(msg):
    s = ""
    for _, v in msg.dict().items():
        s += " " + str(v)
    return s.strip().encode("unicode_escape").decode("utf-8")


def to_mtf(notes: np.ndarray, time_unit: str, tpb: int = 480) -> str:
    import mido
    beats = notes[:, :2] * (2.0 if time_unit == "sec" else 1.0)  # 120 bpm: 1 s = 2 beats
    beats = beats - np.array([beats[:, 0].min(), 0.0])  # drop leading silence
    ev = []
    for (on, du), p in zip(beats, notes[:, 2].astype(int)):
        p = int(np.clip(p, 0, 127))
        ev.append((int(round(on * tpb)), 1, p))
        ev.append((int(round((on + du) * tpb)), 0, p))  # off before on at the same tick
    ev.sort()
    mid = mido.MidiFile(ticks_per_beat=tpb)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tr.append(mido.Message("program_change", program=0, time=0))
    last = 0
    for t, kind, p in ev:
        dt = max(t - last, 0)
        tr.append(mido.Message("note_on", note=p, velocity=80 if kind else 0, time=dt))
        last = t
    tr.append(mido.MetaMessage("end_of_track", time=0))
    lines = ["ticks_per_beat " + str(tpb)]
    for msg in mid.merged_track:
        lines.append(_msg_to_str(msg))
    return "\n".join(lines)


# ------------------------------------------------------------------ ABC
_NAMES = ["C", "^C", "D", "^D", "E", "F", "^F", "G", "^G", "A", "^A", "B"]


def _abc_pitch(p: int) -> str:
    name = _NAMES[p % 12]
    octave = p // 12 - 1  # MIDI 60 → 4
    acc, letter = (name[:-1], name[-1])
    if octave >= 5:
        return acc + letter.lower() + "'" * (octave - 5)
    return acc + letter + "," * (4 - octave)


def _abc_len(u: int) -> str:  # u sixteenths, L:1/8
    if u == 2:
        return ""
    if u % 2 == 0:
        return str(u // 2)
    return "/" if u == 1 else f"{u}/2"


def to_abc(notes: np.ndarray, time_unit: str, bar_units: int = 16, max_bars: int = 400) -> str:
    nb = to_beats(notes, time_unit)
    on = np.round(nb[:, 0] * 4).astype(int)
    off = np.maximum(np.round((nb[:, 0] + nb[:, 1]) * 4).astype(int), on + 1)
    base = on.min()
    on, off = on - base, off - base
    # event list of (start, length, pitch or None=rest), non-overlapping
    ev, t = [], 0
    for s, e, p in zip(on, off, nb[:, 2].astype(int)):
        if s < t:
            s = t
        if e <= s:
            continue
        if s > t:
            ev.append((t, s - t, None))
        ev.append((s, e - s, p))
        t = e
    bars, cur, pos = [], "", 0
    for s, ln, p in ev:
        while ln > 0:
            room = bar_units - pos
            take = min(ln, room)
            sym = "z" if p is None else _abc_pitch(p)
            cur += sym + _abc_len(take)
            ln -= take
            pos += take
            if ln > 0 and p is not None:
                cur += "-"  # tie across barline
            if pos == bar_units:
                bars.append(cur)
                cur, pos = "", 0
        cur += " " if pos else ""
    if cur.strip():
        bars.append(cur.strip())
    bars = bars[:max_bars]
    head = "%%score { 1 }\nL:1/8\nQ:1/4=120\nM:4/4\nK:C\nV:1 treble nm=\"Voice\"\n"
    return head + "".join(f"[V:1]{b.strip()}|\n" for b in bars)


# ------------------------------------------------------------------ scale degrees (简谱)
_DEG = ["1", "#1", "2", "#2", "3", "4", "#4", "5", "#5", "6", "#6", "7"]


def to_degrees(notes: np.ndarray, time_unit: str, max_notes: int = 400) -> str:
    nb = to_beats(notes, time_unit)
    toks = []
    for (_, du, p) in nb[:max_notes]:
        p = int(p)
        o = p // 12 - 5  # octave relative to C4
        tok = _DEG[p % 12] + ("'" * o if o > 0 else "," * (-o))
        holds = int(min(round(du) - 1, 3)) if du >= 1.5 else 0
        if du <= 0.3:
            tok += "_"  # short (16th)
        toks.append(tok + " -" * holds)
    return " ".join(toks)
