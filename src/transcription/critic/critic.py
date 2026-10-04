"""
Transcription critic: audits a vocal-melody MIDI against independent pitch evidence and proposes fixes.

Evidence (10 ms frames, from separated vocals):
  RMVPE f0 (primary), PESTO f0 + confidence (secondary).
  "Confident" frame = both voiced (PESTO conf > PESTO_CONF) and within 0.5 st of each other.
  Pitch per note = median of confident frames in the note's *core* (middle 60%, which excludes attack/release
  glides; a whole-note median is pulled by 滑音 and vibrato extremes).

Per-note verdicts:
  ok            core evidence agrees with note pitch (|dev| < 0.5 st)
  wrong_pitch   ≥ MIN_CORE confident core frames and |dev| ≥ 0.5 st   (octave_error if |dev| ≈ 12)
  unvoiced      RMVPE voiced fraction inside note < UNVOICED_FRAC      (likely spurious note)
  uncertain     too few confident frames to judge
Recording-level:
  missed segments: confident-voiced runs ≥ MISS_MIN_S not covered by any note.

Corrections (`correct()`), each switchable so their effect can be measured separately on the benchmark:
  repitch  wrong_pitch → round(core median − tuning offset), only if a second transcriber (ROSVOT)
           has an overlapping note at that same pitch (consensus; see docs/transcription.md §7)
  delete   unvoiced → removed
  fill     missed segments → new notes (split at stable pitch steps)
"""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pretty_midi

HOP = 0.01
PESTO_CONF = 0.5
DOM_DB = 12.0  # vocal-over-accompaniment margin at f0 that makes an RMVPE-only frame trustworthy (in-domain)


def st(hz: np.ndarray) -> np.ndarray:
    return 12 * np.log2(np.maximum(hz, 1e-3) / 440) + 69


@dataclass
class Params:
    min_core: int = 5            # confident core frames needed to judge pitch
    unvoiced_frac: float = 0.2   # RMVPE voiced fraction below which a note is "unvoiced"
    miss_min_s: float = 0.15     # min length of an uncovered confident-voiced run to count as missed
    step_st: float = 0.7         # pitch step that splits a filled segment
    step_min_s: float = 0.06     # a new pitch must hold this long to split
    dev_thr: float = 0.5         # |dev| (after tuning compensation) needed to call wrong_pitch
    tuning: bool = True          # compensate the singer's global tuning offset before rounding
    consensus: bool = True       # repitch only if a second transcriber agrees with the evidence


@dataclass
class Evidence:
    """confident = RMVPE voiced AND (PESTO confident and within 0.5 st  OR  vocal stem dominates the
    accompaniment by ≥ DOM_DB at the RMVPE pitch). The dominance route exists because in-domain PESTO is
    under-confident on soft/breathy/reverberant singing (docs/transcription.md §7); benchmark clips have no
    accompaniment stem, so there only the PESTO route applies."""
    rmvpe: np.ndarray
    pesto: np.ndarray
    conf: np.ndarray
    dom: np.ndarray | None = None
    confident: np.ndarray = field(init=False)
    semis: np.ndarray = field(init=False)

    def __post_init__(self):
        n = min(len(self.rmvpe), len(self.pesto))
        if self.dom is not None:
            n = min(n, len(self.dom))
            self.dom = self.dom[:n]
        self.rmvpe, self.pesto, self.conf = self.rmvpe[:n], self.pesto[:n], self.conf[:n]
        rv, pv = self.rmvpe > 0, self.conf > PESTO_CONF
        self.semis = st(self.rmvpe)
        self.agree = rv & pv & (np.abs(self.semis - st(self.pesto)) < 0.5)
        self.confident = self.agree.copy()
        if self.dom is not None:
            self.confident |= rv & (np.nan_to_num(self.dom, nan=-99) >= DOM_DB)

    @classmethod
    def load(cls, rmvpe_npz: Path, pesto_npz: Path, dom_npz: Path | None = None) -> "Evidence":
        r, p = np.load(rmvpe_npz), np.load(pesto_npz)
        dom = np.load(dom_npz)["dom_db"].astype(float) if dom_npz is not None and Path(dom_npz).exists() else None
        return cls(r["f0"].astype(float), p["f0"].astype(float), p["conf"].astype(float), dom)


def frames(start: float, end: float, n: int) -> slice:
    return slice(max(0, int(round(start / HOP))), min(n, int(round(end / HOP))))


def tuning_offset(ev: Evidence) -> float:
    """Global tuning deviation from A440 (st, in [-0.5, 0.5)): circular mean of the fractional part
    of confident frames. Singers (and unaccompanied field recordings) are often a quarter-tone off."""
    x = ev.semis[ev.confident]
    if len(x) < 50:
        return 0.0
    ang = 2 * np.pi * (x - np.round(x))
    return float(np.angle(np.mean(np.exp(1j * ang))) / (2 * np.pi))


def audit_notes(notes: list, ev: Evidence, p: Params, second: list | None = None) -> list[dict]:
    """second: notes of an independent transcription (e.g. ROSVOT) used as a consensus check."""
    n = len(ev.rmvpe)
    tau = tuning_offset(ev) if p.tuning else 0.0
    out = []
    for note in notes:
        dur = note.end - note.start
        whole = frames(note.start, note.end, n)
        core = frames(note.start + 0.2 * dur, note.end - 0.2 * dur, n)
        voiced = (ev.rmvpe[whole] > 0).mean() if whole.stop > whole.start else 0.0
        c = ev.confident[core]
        k = int(c.sum())
        med = float(np.median(ev.semis[core][c])) - tau if k else np.nan  # tuning-compensated
        dev = med - note.pitch if k else np.nan
        target = int(round(med)) if k else None
        agree2 = None
        if second is not None and k:
            ov = [s2 for s2 in second if min(s2.end, note.end) - max(s2.start, note.start) > 0.5 * dur]
            agree2 = any(s2.pitch == target for s2 in ov)
        if voiced < p.unvoiced_frac:
            verdict = "unvoiced"
        elif k < p.min_core:
            verdict = "uncertain"
        elif abs(dev) >= p.dev_thr and target != note.pitch:
            verdict = "octave_error" if abs(abs(dev) - 12) < 1 else "wrong_pitch"
        else:
            verdict = "ok"
        out.append({"start": note.start, "end": note.end, "pitch": note.pitch, "core_median": med,
                    "target": target, "dev": dev, "n_core": k, "voiced": voiced, "verdict": verdict,
                    "second_agrees": agree2})
    return out


def missed_segments(notes: list, ev: Evidence, p: Params) -> list[tuple[int, int]]:
    covered = np.zeros(len(ev.rmvpe), bool)
    for note in notes:
        covered[frames(note.start, note.end, len(covered))] = True
    free = ev.confident & ~covered
    segs, i = [], 0
    while i < len(free):
        if free[i]:
            j = i
            while j < len(free) and free[j]:
                j += 1
            if (j - i) * HOP >= p.miss_min_s:
                segs.append((i, j))
            i = j
        else:
            i += 1
    return segs


def split_segment(i: int, j: int, ev: Evidence, p: Params, tau: float = 0.0) -> list[tuple[float, float, int]]:
    """Split a voiced run into notes at pitch steps that hold ≥ step_min_s."""
    s = ev.semis[i:j] - tau
    hold = max(1, int(p.step_min_s / HOP))
    cuts, cur = [0], np.median(s[:hold])
    k = hold
    while k < len(s) - hold:
        nxt = np.median(s[k:k + hold])
        if abs(nxt - cur) >= p.step_st:
            cuts.append(k)
            cur = nxt
            k += hold
        else:
            k += 1
    cuts.append(len(s))
    out = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        if (b - a) * HOP >= p.step_min_s:
            out.append(((i + a) * HOP, (i + b) * HOP, int(round(np.median(s[a:b])))))
    return out


def correct(midi_in: Path, ev: Evidence, p: Params, repitch=True, delete=True, fill=True,
            second_midi: Path | None = None) -> tuple[pretty_midi.PrettyMIDI, dict]:
    pm = pretty_midi.PrettyMIDI(str(midi_in))
    inst = next((i for i in pm.instruments if not i.is_drum), None)
    if inst is None:
        return pm, {}
    inst.notes.sort(key=lambda x: x.start)
    second = None
    if second_midi is not None and Path(second_midi).exists():
        second = [x for i in pretty_midi.PrettyMIDI(str(second_midi)).instruments for x in i.notes]
    audit = audit_notes(inst.notes, ev, p, second if p.consensus else None)
    stats = {"notes": len(inst.notes), "repitched": 0, "octave": 0, "deleted": 0, "filled": 0,
             **{f"v_{v}": sum(a["verdict"] == v for a in audit)
                for v in ("ok", "wrong_pitch", "octave_error", "unvoiced", "uncertain")}}
    kept = []
    for note, a in zip(inst.notes, audit):
        if delete and a["verdict"] == "unvoiced":
            stats["deleted"] += 1
            continue
        if repitch and a["verdict"] in ("wrong_pitch", "octave_error") and (
                not p.consensus or a["second_agrees"]):
            note.pitch = int(np.clip(a["target"], 0, 127))
            stats["repitched"] += 1
            stats["octave"] += a["verdict"] == "octave_error"
        kept.append(note)
    if fill:
        for i, j in missed_segments(kept, ev, p):
            tau = tuning_offset(ev) if p.tuning else 0.0
            for s, e, ptc in split_segment(i, j, ev, p, tau):
                kept.append(pretty_midi.Note(velocity=90, pitch=int(np.clip(ptc, 0, 127)), start=s, end=e))
                stats["filled"] += 1
    inst.notes = sorted(kept, key=lambda x: x.start)
    return pm, stats
