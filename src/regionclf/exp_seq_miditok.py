"""
Family "sequence": MidiTok vocabularies (REMI / TSD / Structured, ± BPE) → TF-IDF n-grams → linear classifier.

Notes → MIDI (data/regionclf/tok/midi/<pitchmode>/<source>/<i>.mid, one monophonic track, 480 tpq):
  - beat-based sources (anthology, essen) keep their beat grid;
  - transcriptions (seconds, no grid) are rescaled so the song's median IOI = an eighth note (tempo-relative).
  pitchmode 'raw'  : pitches as stored (anthology 1=C, Essen real key, transcriptions absolute sung pitch)
  pitchmode 'gong' : transposed so the estimated 宫 = C, folded into octave C4..B5 around the song's median.
BPE: MidiTok `tokenizer.train(vocab_size, model="BPE")` on the union of all sources' MIDI (anthology + essen +
trans_primary + trans_rosvot; unsupervised, label-free — shared with the SSL experiments). Token caches are
written as data/regionclf/tok/<source>_mt_<tok>_<pitchmode>[_bpe<k>].pkl so exp_seq_ngram.task_tokens can read them.

Run (regionseq env):
  python src/regionclf/exp_seq_miditok.py build
  python src/regionclf/exp_seq_miditok.py eval [--tasks A5,E,T15,T5]     # sweep → tok/sweep_miditok.csv
  python src/regionclf/exp_seq_miditok.py log                           # selected configs → results.csv
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import load  # noqa: E402
from regionclf.exp_seq_tok import SOURCES, TOK  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402

TPQ = 480
TOKENIZERS = ["REMI", "TSD", "Structured"]
BPE_SIZES = [1000, 4000]


def to_beats(r) -> np.ndarray:
    n = r["notes"].copy()
    if r["time_unit"] == "sec":
        ioi = np.diff(n[:, 0])
        med = np.median(ioi[ioi > 0]) if (ioi > 0).any() else 0.25
        n[:, :2] *= 0.5 / med
    return n


def pitches(r, mode) -> np.ndarray:
    p = r["notes"][:, 2].astype(int)
    if mode == "raw":
        return p
    g = estimate_gong(r["notes"])
    q = p - g
    shift = 12 * int(np.round((np.median(q) - 66) / 12))
    return np.clip(q - shift, 24, 107)


def write_midis(mode) -> dict:
    from symusic import Note, Score, Track
    paths = {}
    for s in SOURCES:
        d = TOK / "midi" / mode / s
        d.mkdir(parents=True, exist_ok=True)
        recs = load(s)
        paths[s] = []
        for i, r in enumerate(recs):
            f = d / f"{i}.mid"
            if not f.exists():
                n = to_beats(r)
                p = pitches(r, mode)
                sc = Score(TPQ)
                tr = Track(program=0, is_drum=False, name="melody")
                for (on, du, _), pp in zip(n, p):
                    tr.notes.append(Note(int(round(on * TPQ)), max(1, int(round(du * TPQ))), int(pp), 80))
                sc.tracks.append(tr)
                sc.dump_midi(str(f))
            paths[s].append(f)
    return paths


def make_tok(name):
    import miditok
    cfg = miditok.TokenizerConfig(pitch_range=(21, 109), beat_res={(0, 4): 8, (4, 12): 4}, use_velocities=False,
                                  use_time_signatures=False, use_rests=name != "Structured", encode_ids_split="no",
                                  num_velocities=1)
    return getattr(miditok, name)(cfg)


def encode(tok, path, bpe: bool) -> list[str]:
    from symusic import Score
    seq = tok(Score(str(path)), encode_ids=bpe)
    seq = seq[0] if isinstance(seq, list) else seq
    if bpe:
        return [f"b{i}" for i in seq.ids]
    return [t.replace(" ", "") for t in seq.tokens]


def build():
    for mode in ["raw", "gong"]:
        paths = write_midis(mode)
        allp = [p for s in SOURCES for p in paths[s]]
        for name in TOKENIZERS:
            tok = make_tok(name)
            for s in SOURCES:
                f = TOK / f"{s}_mt_{name.lower()}_{mode}.pkl"
                if not f.exists():
                    pickle.dump([encode(tok, p, False) for p in paths[s]], open(f, "wb"))
            for k in BPE_SIZES:
                tk = make_tok(name)
                tk.train(vocab_size=k, model="BPE", files_paths=allp)
                for s in SOURCES:
                    toks = [encode(tk, p, True) for p in paths[s]]
                    pickle.dump(toks, open(TOK / f"{s}_mt_{name.lower()}_{mode}_bpe{k}.pkl", "wb"))
                    print(mode, name, k, s, "mean len", np.mean([len(t) for t in toks]), flush=True)


def evaluate(tasks):
    from joblib import Parallel, delayed

    from regionclf.exp_seq_ngram import run
    vocabs = [f"mt_{n.lower()}_{m}{b}" for n in TOKENIZERS for m in ["raw", "gong"]
              for b in [""] + [f"_bpe{k}" for k in BPE_SIZES]]
    jobs = []
    for t in tasks:
        for v in vocabs:
            for lo, hi in ([(1, 1), (1, 2), (1, 3)] if "bpe" in v else [(1, 2), (1, 4), (2, 6)]):
                jobs.append((t, [v], lo, hi, "logreg", 3.0))
    out = pd.DataFrame(Parallel(n_jobs=8, verbose=2)(delayed(run)(*j) for j in jobs))
    f = TOK / "sweep_miditok.csv"
    out.to_csv(f, mode="a", header=not f.exists(), index=False)
    for t in tasks:
        d = out[out.task == t]
        print(f"\n== {t}\n", d.pivot_table(index="vocab", columns="n", values="macro_f1").round(3).to_string())


LOG_CONFIGS = [("mt_tsd_raw", 1, 4), ("mt_tsd_gong", 1, 4), ("mt_tsd_raw_bpe1000", 1, 3),
               ("mt_tsd_gong_bpe1000", 1, 3), ("mt_remi_raw_bpe1000", 1, 3), ("mt_structured_raw", 2, 6)]


def log_all(tasks):
    from joblib import Parallel, delayed

    from regionclf.common import log_result
    from regionclf.exp_seq_ngram import run
    jobs = [(t, [v], lo, hi, "logreg", 3.0, "defer") for t in tasks for v, lo, hi in LOG_CONFIGS]
    for o in Parallel(n_jobs=6)(delayed(run)(*j) for j in jobs):
        log_result(o["_name"], "sequence", o["task"], o["_y"], o["_pred"], notes="MidiTok; " + o["_notes"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "eval", "log"])
    ap.add_argument("--tasks", default="A5,E,T15,T5")
    a = ap.parse_args()
    {"build": lambda t: build(), "eval": evaluate, "log": log_all}[a.mode](a.tasks.split(","))
