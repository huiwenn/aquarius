"""
Melodic reduction: turn a performance transcription into a score-like skeleton melody.

Motivation (docs/region_classification.md §4): transcriptions are "chromaticized" (偏音 8–20% vs 1–3% in
scores, 7–8 scale degrees in use vs 5) and ornament-fragmented (fourth leaps 0.05–0.07 vs 0.09–0.14), which is why
score-trained models don't transfer. 简谱 collectors notate the *骨干音* (skeleton tones), not 润腔 ornaments.

reduce(notes, level):
  1  drop ornament notes: IOI < `orn` × median IOI (their duration is given to the preceding note)
  2  + merge consecutive notes of the same pitch
  3  + snap non-pentatonic degrees (relative to estimated 宫) to the nearest 宫商角徵羽 degree, then re-merge
The operations are also safe on scores (they barely change clean skeletons), so both domains can be reduced.
"""

import numpy as np

from regionclf.features import estimate_gong

PENTA_DEG = np.array([0, 2, 4, 7, 9])


def _merge_repeats(notes: np.ndarray) -> np.ndarray:
    out = [notes[0].copy()]
    for n in notes[1:]:
        if n[2] == out[-1][2]:
            out[-1][1] = n[0] + n[1] - out[-1][0]
        else:
            out.append(n.copy())
    return np.array(out)


def reduce(notes: np.ndarray, level: int = 3, orn: float = 0.5) -> np.ndarray:
    if len(notes) < 4:
        return notes
    notes = notes.copy()
    ioi = np.diff(notes[:, 0])
    med = np.median(ioi[ioi > 0]) if (ioi > 0).any() else 1.0
    if level >= 1:
        keep = [0]
        for i in range(1, len(notes)):
            nxt = notes[i + 1, 0] if i + 1 < len(notes) else notes[i, 0] + notes[i, 1]
            if nxt - notes[i, 0] < orn * med:  # short ornament note: absorb into previous
                prev = keep[-1]
                notes[prev, 1] = max(notes[prev, 1], nxt - notes[prev, 0])
            else:
                keep.append(i)
        notes = notes[keep]
    if level >= 2 and len(notes) > 1:
        notes = _merge_repeats(notes)
    if level >= 3 and len(notes) > 1:
        g = estimate_gong(notes)
        rel = (notes[:, 2].astype(int) - g) % 12
        d = rel[:, None] - PENTA_DEG[None, :]
        d = (d + 6) % 12 - 6  # circular distance
        k = np.abs(d).argmin(1)
        notes[:, 2] = notes[:, 2] - d[np.arange(len(d)), k]
        notes = _merge_repeats(notes)
    return notes
