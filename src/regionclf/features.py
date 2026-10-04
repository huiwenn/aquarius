"""
Music-theory feature representation (family: "theory").

Chinese folk music is overwhelmingly pentatonic-based and 色彩区 are defined in the literature (江明惇) by
scale (五声/六声/七声, 偏音 use), mode (宫商角徵羽 final), characteristic intervals (e.g. 西北 fourths,
江浙 stepwise, 湘 "羽音调"), phrase structure and rhythm. The features operationalise exactly that:

  tonic     宫 ("do") = argmax over 12 transpositions of the duration-weighted pitch-class profile against a
            pentatonic template (宫商角徵羽 = 1, 清角/变宫 fa/ti = 0.3, others 0). Tonic-relative features are
            invariant to key and to singer register — required because anthology pitches are 1=C, Essen is in
            real keys, transcriptions are absolute sung pitch.
  pc12      duration-weighted scale-degree histogram relative to 宫
  final12   one-hot degree of the last note (the mode's final, 调式主音) + degree of the longest note
  scale     # degrees with >3% mass; mass on 偏音 (fa=5, ti=11, 变徵=6, 闰=10)
  int25     interval histogram −12..+12 semitones (+ |i|>12 bucket), contour up/down/repeat, mean |i|, leap share
  trans144  12×12 scale-degree transition matrix (first-order Markov), normalized
  rhythm    log2(IOI / median IOI) histogram (7 bins), duration CV, long-note share (phrase-final lengthening),
            short-note share (ornaments) — tempo-free, so seconds (transcriptions) and beats (scores) compare
  register  range (p95−p5), pitch std — relative, not absolute
Optionally `absolute=True` adds the absolute pitch-class histogram and mean MIDI pitch, to expose confounds.
"""

import numpy as np

PENTA = np.zeros(12)
PENTA[[0, 2, 4, 7, 9]] = 1.0
PENTA[[5, 11]] = 0.3


def pc_profile(notes: np.ndarray) -> np.ndarray:
    h = np.bincount(notes[:, 2].astype(int) % 12, weights=notes[:, 1], minlength=12)
    return h / max(h.sum(), 1e-9)


def estimate_gong(notes: np.ndarray) -> int:
    h = pc_profile(notes)
    return int(np.argmax([np.dot(np.roll(h, -k), PENTA) for k in range(12)]))


def theory_features(notes: np.ndarray, absolute: bool = False) -> np.ndarray:
    pitch = notes[:, 2].astype(int)
    dur = notes[:, 1]
    gong = estimate_gong(notes)
    rel = (pitch - gong) % 12
    pc12 = np.bincount(rel, weights=dur, minlength=12)
    pc12 = pc12 / max(pc12.sum(), 1e-9)
    final12 = np.eye(12)[rel[-1]]
    longest12 = np.eye(12)[rel[int(np.argmax(dur))]]
    scale = [np.sum(pc12 > 0.03), pc12[[5, 11]].sum(), pc12[6] + pc12[10]]

    iv = np.diff(pitch)
    ih = np.bincount(np.clip(iv, -13, 13) + 13, minlength=27).astype(float)
    ih = ih / max(ih.sum(), 1)
    contour = [np.mean(iv > 0), np.mean(iv < 0), np.mean(iv == 0), np.mean(np.abs(iv)),
               np.mean(np.abs(iv) >= 5), np.abs(iv).max() if len(iv) else 0] if len(iv) else [0] * 6

    tm = np.zeros((12, 12))
    np.add.at(tm, (rel[:-1], rel[1:]), 1)
    tm = (tm / max(tm.sum(), 1)).ravel()

    ioi = np.diff(notes[:, 0])
    ioi = ioi[ioi > 0]
    if len(ioi) > 2:
        r = np.log2(ioi / np.median(ioi))
        rh = np.histogram(np.clip(r, -3, 3), bins=7, range=(-3.5, 3.5))[0].astype(float)
        rh /= rh.sum()
        rhythm = list(rh) + [np.std(ioi) / np.mean(ioi), np.mean(ioi >= 2 * np.median(ioi)),
                             np.mean(ioi <= 0.5 * np.median(ioi))]
    else:
        rhythm = [0] * 10
    register = [np.percentile(pitch, 95) - np.percentile(pitch, 5), np.std(pitch)]
    feats = [pc12, final12, longest12, scale, ih, contour, tm, rhythm, register]
    if absolute:
        feats += [pc_profile(notes), [np.mean(pitch)]]
    return np.concatenate([np.asarray(f, float).ravel() for f in feats])


FEATURE_BLOCKS = {"pc12": 12, "final12": 12, "longest12": 12, "scale": 3, "int27": 27, "contour": 6,
                  "trans144": 144, "rhythm": 10, "register": 2}


def matrix(recs, absolute: bool = False) -> np.ndarray:
    return np.vstack([theory_features(r["notes"], absolute) for r in recs])
