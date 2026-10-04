"""
Shared melodic-comparison utilities for reference-free / in-domain auditing.

A performance transcription and a score (or another performance) of the same folk song differ in
key, tempo, ornaments and small variants, so comparisons must be:
  - transposition-invariant: best transposition chosen from duration-weighted pitch-class histograms
    (all 12 shifts × the octave that best aligns median pitch)
  - tempo-invariant: compare note *sequences*, not timestamps
  - ornament-tolerant: drop notes shorter than `min_dur` and merge repeated same-pitch notes
    before comparison (scores carry the skeleton melody; 滑音/倚音 appear as short notes in audio)

melodic_agreement(a, b) returns:
  acc    fraction of aligned positions with identical pitch after transposition
         (Needleman–Wunsch, gap cost 1, substitution cost min(|Δ|,2)/2)
  shift  transposition applied to b (semitones)
  cov    aligned length / max(len(a), len(b))
"""

from pathlib import Path

import numpy as np
import pretty_midi


def load_notes(path: Path, track_filter: str | None = None) -> list[tuple[float, float, int]]:
    pm = pretty_midi.PrettyMIDI(str(path))
    out = []
    for inst in pm.instruments:
        if inst.is_drum or (track_filter and track_filter.lower() not in (inst.name or "").lower()):
            continue
        out += [(n.start, n.end, n.pitch) for n in inst.notes if n.end > n.start]
    return sorted(out)


def skeleton(notes, min_dur: float = 0.08, beats: bool = False) -> np.ndarray:
    """Monophonic pitch sequence: drop short notes, keep the highest of overlapping onsets,
    merge consecutive repeats. For scores pass min_dur in beats (beats=True) and a smaller value."""
    notes = [n for n in notes if n[1] - n[0] >= min_dur]
    seq = []
    last_on = -1.0
    for s, e, p in notes:
        if seq and abs(s - last_on) < 1e-3:  # simultaneous onset → keep higher (melody on top)
            seq[-1] = max(seq[-1], p)
            continue
        if not seq or seq[-1] != p:
            seq.append(p)
        last_on = s
    return np.array(seq, dtype=int)


def best_shift(a: np.ndarray, b: np.ndarray) -> int:
    """Transposition for b that best matches a's pitch-class content and register."""
    ha = np.bincount(a % 12, minlength=12).astype(float)
    hb = np.bincount(b % 12, minlength=12).astype(float)
    k = int(np.argmax([np.dot(ha, np.roll(hb, s)) for s in range(12)]))
    oct_ = int(np.round((np.median(a) - (np.median(b) + k)) / 12))
    return k + 12 * oct_


def align(a: np.ndarray, b: np.ndarray, local_a: bool = False) -> tuple[int, int]:
    """Needleman–Wunsch; returns (#exact matches, #aligned pairs).
    local_a=True: semi-global — leading/trailing parts of `a` are free (b must be matched inside a).
    Use it when a is a multi-verse performance and b a single-verse score."""
    n, m = len(a), len(b)
    D = np.zeros((n + 1, m + 1))
    D[:, 0] = 0 if local_a else np.arange(n + 1)
    D[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        sub = np.minimum(np.abs(a[i - 1] - b), 2) / 2
        for j in range(1, m + 1):
            D[i, j] = min(D[i - 1, j] + 1, D[i, j - 1] + 1, D[i - 1, j - 1] + sub[j - 1])
    i = int(np.argmin(D[:, m])) if local_a else n
    j, match, pairs = m, 0, 0
    while i > 0 and j > 0:
        sub = min(abs(a[i - 1] - b[j - 1]), 2) / 2
        if D[i, j] == D[i - 1, j - 1] + sub:
            pairs += 1
            match += a[i - 1] == b[j - 1]
            i, j = i - 1, j - 1
        elif D[i, j] == D[i - 1, j] + 1:
            i -= 1
        else:
            j -= 1
    return match, pairs


def melodic_agreement(a: np.ndarray, b: np.ndarray, max_len: int = 400, local_a: bool = False) -> dict:
    """local_a: b (e.g. a one-verse score) is located inside a (a multi-verse performance);
    acc is then matches / len(b)."""
    if len(a) < 4 or len(b) < 4:
        return {"acc": np.nan, "shift": np.nan, "cov": np.nan}
    a, b = a[:max_len], b[:max_len]
    s = best_shift(a, b)
    match, pairs = align(a, b + s, local_a)
    denom = len(b) if local_a else max(1, pairs)
    return {"acc": match / denom, "shift": s, "cov": pairs / (len(b) if local_a else max(len(a), len(b)))}
