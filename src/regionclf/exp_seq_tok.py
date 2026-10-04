"""
Family "sequence" — symbolic token vocabularies for 色彩区 classification (shared by exp_seq_*.py).

Every vocabulary maps a record's monophonic notes (onset, dur, midi) to a list of string tokens. All are
tempo-relative (rhythm = IOI / median IOI of the song, log2-quantized) so beat-based scores and second-based
transcriptions share one vocabulary, and all but `abs`/MidiTok are key-invariant (relative to the estimated 宫).

  int      melodic interval in semitones, clipped to ±12 (+ 'R' = repeat)
  deg      scale degree relative to 宫 (宫 商 角 徵 羽 + 偏音 清角 变徵 闰 变宫 + chromatic ♯宫 ♯商 ♯徵)
  degoct   degree + register (low / mid / high relative to the song's median pitch, ±6 semitones)
  degdur   degree + quantized relative duration  (e.g. '徵_1' = 徵 held 2× median IOI)
  intdur   interval + quantized relative duration
  dur      relative-duration only (rhythm)
  contour  U/D/S + step/leap (5-letter contour alphabet)
  abs      absolute pitch class (non-normalized, for confound checks)
  cad      phrase-final ("落音") degrees only: notes whose IOI ≥ 2× the median IOI (phrase-final lengthening / breath),
           plus the last note — a coarse phrase-level (hierarchical) view of the cadence plan
Relative-duration bins: q = clip(round(log2(IOI / median IOI)), -2, 3)  (IOI of the last note = its duration).

MidiTok vocabularies (REMI / TSD / Structured, ± BPE) are built in exp_seq_miditok.py.

Cache: data/regionclf/tok/<source>_<vocab>.pkl  (list of token lists aligned with load(source)).
Run (py312 or regionseq): python src/regionclf/exp_seq_tok.py      # builds all caches
"""

import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import D, load  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402

TOK = D / "tok"
SOURCES = ["anthology", "essen", "trans_primary", "trans_rosvot"]
DEG = ["宫", "♯宫", "商", "♯商", "角", "清角", "变徵", "徵", "♯徵", "羽", "闰", "变宫"]
VOCABS = ["int", "deg", "degoct", "degdur", "intdur", "dur", "contour", "abs", "cad"]


def rel_dur(notes: np.ndarray) -> np.ndarray:
    on = notes[:, 0]
    ioi = np.r_[np.diff(on), notes[-1, 1]]
    ioi = np.where(ioi <= 0, notes[:, 1], ioi)
    pos = ioi[ioi > 0]
    med = np.median(pos) if len(pos) else 1.0
    return np.clip(np.round(np.log2(np.maximum(ioi, 1e-4) / med)), -2, 3).astype(int)


def iv_tok(i: int) -> str:
    if i == 0:
        return "R"
    return f"{'+' if i > 0 else '-'}{min(abs(i), 12)}"


def tokenize(notes: np.ndarray, vocab: str, gong: int | None = None) -> list[str]:
    p = notes[:, 2].astype(int)
    if gong is None:
        gong = estimate_gong(notes)
    rel = (p - gong) % 12
    if vocab == "int":
        return [iv_tok(i) for i in np.diff(p)]
    if vocab == "deg":
        return [DEG[d] for d in rel]
    if vocab == "degoct":
        med = np.median(p)
        reg = np.where(p < med - 6, "L", np.where(p > med + 6, "H", "M"))
        return [f"{DEG[d]}{r}" for d, r in zip(rel, reg)]
    if vocab == "degdur":
        return [f"{DEG[d]}_{q}" for d, q in zip(rel, rel_dur(notes))]
    if vocab == "intdur":
        q = rel_dur(notes)
        return [f"{iv_tok(i)}_{d}" for i, d in zip(np.diff(p), q[1:])]
    if vocab == "dur":
        return [f"d{q}" for q in rel_dur(notes)]
    if vocab == "contour":
        out = []
        for i in np.diff(p):
            out.append("S" if i == 0 else ("u" if 0 < i <= 2 else "U" if i > 2 else "d" if i >= -2 else "D"))
        return out
    if vocab == "cad":
        q = rel_dur(notes)
        keep = q >= 1
        keep[-1] = True
        return [DEG[d] for d in rel[keep]]
    if vocab == "abs":
        return [f"pc{x % 12}" for x in p]
    raise ValueError(vocab)


def cached(source: str, vocab: str) -> list[list[str]]:
    f = TOK / f"{source}_{vocab}.pkl"
    if f.exists():
        return pickle.load(open(f, "rb"))
    recs = load(source)
    toks = [tokenize(r["notes"], vocab) for r in recs]
    TOK.mkdir(parents=True, exist_ok=True)
    pickle.dump(toks, open(f, "wb"))
    return toks


def task_tokens(task_name: str, vocab: str, recs) -> list[list[str]]:
    """Token lists aligned with `task(task_name)` records (looked up by item_id in the source cache)."""
    src = recs[0]["source"]
    full = load(src)
    toks = cached(src, vocab)
    m = {r["item_id"]: t for r, t in zip(full, toks)}
    return [m[r["item_id"]] for r in recs]


if __name__ == "__main__":
    for s in SOURCES:
        for v in VOCABS:
            t = cached(s, v)
            print(s, v, len(t), t[0][:12], flush=True)
