"""
Family "markov": per-region n-gram language models over melodic viewpoints (after Conklin & Witten's
multiple-viewpoint systems). A song is assigned to the region whose model gives it the highest mean
per-token log-likelihood (+ class prior). Interpretable and data-efficient: it asks directly
"whose melodic grammar does this song speak?"

Viewpoints (sequences derived per song):
  deg   scale degree relative to 宫 (estimate_gong), with octave folded: 0..11
  int   melodic interval in semitones, clipped to ±12
  degd  scale degree × relative-duration class (short/normal/long vs median IOI)
  ctr   contour symbol (U/D/R) × interval size class (step ≤2, skip 3–4, leap ≥5)
Models: interpolated Kneser-Ney-free "add-k + Witten-Bell-like backoff": P(x|ctx) = λ·ML(x|ctx) + (1−λ)·P(x|shorter ctx),
λ = c(ctx)/(c(ctx)+k·types(ctx)); orders 1–4. Viewpoint combination = sum of log-likelihoods (product of experts).

Run (py312): python src/regionclf/exp_markov.py [--tasks A5,E,T15,T5]
"""

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import cv_predict, log_result, task  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402


def viewpoint(notes: np.ndarray, kind: str) -> list:
    p = notes[:, 2].astype(int)
    if kind == "deg":
        g = estimate_gong(notes)
        return list((p - g) % 12)
    if kind == "int":
        return list(np.clip(np.diff(p), -12, 12))
    ioi = np.diff(notes[:, 0])
    med = np.median(ioi[ioi > 0]) if (ioi > 0).any() else 1.0
    dcls = np.r_[np.digitize(ioi / med, [0.7, 1.5]), 1]  # last note: normal
    if kind == "degd":
        g = estimate_gong(notes)
        return [f"{d}.{c}" for d, c in zip((p - g) % 12, dcls)]
    if kind == "ctr":
        iv = np.diff(p)
        size = np.digitize(np.abs(iv), [1, 3, 5])  # 0 repeat, 1 step, 2 skip, 3 leap
        return [f"{'U' if i > 0 else 'D' if i < 0 else 'R'}{s}" for i, s in zip(iv, size)]
    raise ValueError(kind)


class NGram:
    def __init__(self, order: int, k: float = 1.0):
        self.order, self.k = order, k
        self.counts = defaultdict(Counter)  # context tuple → Counter(next)
        self.vocab = set()

    def fit(self, seqs):
        for s in seqs:
            s = ["<s>"] * (self.order - 1) + list(s)
            self.vocab.update(s)
            for i in range(self.order - 1, len(s)):
                for n in range(self.order):
                    self.counts[tuple(s[i - n:i])][s[i]] += 1
        return self

    def prob(self, ctx: tuple, x) -> float:
        V = len(self.vocab) + 1
        p = 1.0 / V
        for n in range(0, len(ctx) + 1):
            c = self.counts.get(ctx[len(ctx) - n:] if n else (), None)
            if not c:
                continue
            tot, types = sum(c.values()), len(c)
            lam = tot / (tot + self.k * types)
            p = lam * c[x] / tot + (1 - lam) * p
        return p

    def score(self, s) -> float:
        s = ["<s>"] * (self.order - 1) + list(s)
        lp = [np.log(self.prob(tuple(s[i - self.order + 1:i]), s[i])) for i in range(self.order - 1, len(s))]
        return float(np.mean(lp)) if lp else -99.0


def make_fp(views, order):
    def fp(tr, te):
        regions = sorted({r["region"] for r in tr})
        models = {(reg, v): NGram(order).fit([viewpoint(r["notes"], v) for r in tr if r["region"] == reg])
                  for reg in regions for v in views}
        out = []
        for r in te:
            seqs = {v: viewpoint(r["notes"], v) for v in views}
            s = [sum(models[(reg, v)].score(seqs[v]) for v in views) for reg in regions]
            out.append(regions[int(np.argmax(s))])
        return np.array(out)
    return fp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="A5,E,T15,T5")
    args = ap.parse_args()
    configs = [(("deg",), 2), (("deg",), 3), (("deg",), 4), (("int",), 3), (("degd",), 3), (("ctr",), 3),
               (("deg", "int"), 3), (("deg", "int", "degd", "ctr"), 3)]
    for t in args.tasks.split(","):
        recs = task(t)
        for views, order in configs:
            y, pred = cv_predict(recs, make_fp(views, order))
            log_result(f"markov[{'+'.join(views)}]/order{order}", "markov", t, y, pred,
                       "argmax per-region n-gram log-likelihood (uniform prior)")


if __name__ == "__main__":
    main()
