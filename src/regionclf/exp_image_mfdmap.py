"""
Family "image": MFDMap (musical feature density map) replication + external comparison point (task E5prior).

Prior work. MFDMap is from Khoo, Man & Cao (Swinburne): "Automatic Han Chinese folk song classification using
the musical feature density map" (ICSPCS 2012, R-ELM 72%), "... using extreme learning machines" (AI 2012,
FIR-ELM 80.65%), and S. S. Khoo's PhD thesis (Swinburne 2013, doi:10.25916/sut.26259335, open access) which
gives the full definition. (The 84.7% "CRF-RBM" figure is Juan Li et al., Multimedia Tools & Applications 2018,
on *audio* recordings, not on Essen, so it is not a like-for-like comparison.)

Definition (thesis §3.3-3.4, faithfully implemented in `mfdmap_tokens`):
  - four "music elements" per song: solfege (key-relative pitch *with octave*: tonic of the principal octave
    C4-B4 = 25, one step per semitone, rest = 0; minor keys use the relative major), interval (semitones between
    consecutive notes, rests skipped), duration (quarter = 1; rests negative), duration ratio (d_n / d_{n-1},
    negative across a note/rest boundary). Tied notes count as one note.
  - MFDMap = concatenation, in that order and sorted by value, of the occurrence percentage of every value of each
    element (percentage within the element: /N, /(N - rests - 1), /N, /(N - 1)).
  - vocabulary = union of values over the corpus; "reduced" maps keep a value only if >= x% of the songs of some
    class contain it (x in 1..50; best x = 15). Case 1 includes rests, Case 2 drops them (Case 2 was better).
  - classifier: ELM / R-ELM (tanh hidden layer, random input weights, regularized least-squares output weights)
    and FIR-ELM; 10-fold stratified CV (random, not song-grouped), accuracy averaged over 50 repetitions,
    best over (x, hidden size, gamma) reported.
Their data: 333 Han songs of Essen, 5 classes: Dongbei (Liaoning+Jilin+Heilongjiang) 70, Shanxi 75, Sichuan 43,
Guangdong 61, Jiangsu 84. Ours (E5prior, from the Essen `han` subset via corpus.py province parsing): Dongbei 66,
Shanxi 110 (Essen spells several Shaanxi sites "shanxi"; exact 75-song list is unpublished), Sichuan 44,
Guangdong 61, Jiangsu 84 = 365 songs.

Two MFDMap variants:
  faithful  re-parsed from the **kern files with music21 (ties stripped, explicit rests, key from the *X: token
            or else the major key of the key signature) — only possible for Essen (E5prior).
  gong      from corpus notes (any task): solfege = semitones from do0 (the 宫 pitch nearest the median pitch,
            see exp_image_render.normalize) + 25; rests = inter-onset gaps; durations in beats for scores, and for
            transcriptions in median-IOI units snapped to the score duration grid. No tie merging available.

Experiments logged (family="image"):
  E5prior  mfdmap-faithful/{relm, elm, logreg} under (i) the prior protocol: stratified random 10-fold,
           accuracy (logged with notes) and (ii) our song-grouped 5 folds (common.folds).
  A5,E,T15,T5  mfdmap-gong/{relm, logreg} on the shared folds.
Vocabulary and the x% selection are fit inside each training fold (the thesis fit them on all 333 songs).

Run (arm64 env; music21 installed there):
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_mfdmap.py [--tasks E5prior,A5,E,T15,T5]
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/regionimg/bin/python src/regionclf/exp_image_mfdmap.py --diag
"""

import argparse
import pickle
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import ROOT, cv_predict, labels, load, log_result, scores, task  # noqa: E402
from regionclf.exp_image_render import IMG, already_logged, normalize  # noqa: E402

ESSEN = ROOT / "data" / "raw" / "essen" / "asia" / "china"
DONGBEI = {"Liaoning", "Jilin", "Heilongjiang"}
PRIOR = {"Shanxi": "Shanxi", "Sichuan": "Sichuan", "Guangdong": "Guangdong", "Jiangsu": "Jiangsu"}
DUR_GRID = np.array([1 / 12, 1 / 8, 1 / 6, 3 / 16, 1 / 4, 1 / 3, 3 / 8, 1 / 2, 2 / 3, 3 / 4, 1, 4 / 3, 3 / 2, 2, 3, 4,
                     6, 8])


# ---------------------------------------------------------------- data
def e5prior() -> list[dict]:
    out = []
    for r in load("essen"):
        if r["subset"] != "han":
            continue
        p = r["province"]
        lab = "Dongbei" if p in DONGBEI else PRIOR.get(p)
        if lab:
            out.append({**r, "region": lab})
    return out


def kern_events(item_id: str):
    """(solfege-ready) events from the kern file: list of (midi or None for rest, quarterLength), tonic pc."""
    import music21 as m21
    path = ESSEN / f"{item_id}.krn"
    s = m21.converter.parse(str(path), format="humdrum").stripTies()
    tonic = None
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith("*") and line.endswith(":") and line[1:2].isalpha() and line[1].lower() in "abcdefg":
            k = m21.key.Key(line[1:-1].replace("-", "-"))
            tonic = (k.relative if k.mode == "minor" else k).tonic.pitchClass
            break
    if tonic is None:
        ks = next(iter(s.recurse().getElementsByClass(m21.key.KeySignature)), None)
        tonic = ks.asKey("major").tonic.pitchClass if ks is not None else 0
    ev = []
    for n in s.flatten().notesAndRests:
        if n.duration.isGrace or n.quarterLength <= 0:
            continue
        ev.append((None if n.isRest else max(p.midi for p in n.pitches), float(n.quarterLength)))
    return ev, tonic


def faithful_events(recs):
    cache = IMG / "mfdmap_kern_events.pkl"
    d = pickle.load(open(cache, "rb")) if cache.exists() else {}
    miss = [r["item_id"] for r in recs if r["item_id"] not in d]
    for i in miss:
        d[i] = kern_events(i)
    if miss:
        pickle.dump(d, open(cache, "wb"))
    out = []
    for r in recs:
        ev, tonic = d[r["item_id"]]
        tonic_midi = 60 + tonic  # tonic within the principal octave C4-B4
        out.append([(None if p is None else p - tonic_midi + 25, q) for p, q in ev])
    return out


def gong_events(r):
    """Events from corpus notes: solfege from do0, rests from onset gaps, durations on the score grid."""
    t, d, rel, _ = normalize(r["notes"])
    if r["time_unit"] == "beat":
        on, du = r["notes"][:, 0] - r["notes"][0, 0], r["notes"][:, 1]
    else:  # seconds -> median-IOI units, snapped to the notated-duration grid
        on, du = t, d
        du = DUR_GRID[np.argmin(np.abs(np.log(np.maximum(du, 1e-3))[:, None] - np.log(DUR_GRID)[None]), axis=1)]
    ev = []
    for i in range(len(rel)):
        ev.append((int(rel[i]) + 25, float(du[i])))
        if i + 1 < len(rel):
            gap = on[i + 1] - (on[i] + r["notes"][i, 1] if r["time_unit"] == "beat" else on[i] + d[i])
            if gap > 0.05 * (1 if r["time_unit"] == "beat" else 1):
                g = gap if r["time_unit"] == "beat" else DUR_GRID[np.argmin(np.abs(np.log(gap) - np.log(DUR_GRID)))]
                ev.append((None, float(g)))
    return ev


# ---------------------------------------------------------------- MFDMap
def mfdmap_tokens(ev, case: int = 2) -> Counter:
    """Occurrence percentages of every (element, value) token, per thesis eq. 3.4."""
    if case == 2:
        ev = [e for e in ev if e[0] is not None]
    rq = lambda v: round(v, 4)  # noqa: E731
    sol = [0 if p is None else p for p, _ in ev]
    notes = [p for p, _ in ev if p is not None]
    ints = list(np.diff(notes)) if len(notes) > 1 else []
    dur = [rq(q if p is not None else -q) for p, q in ev]
    dr = [rq(dur[i] / dur[i - 1]) for i in range(1, len(dur))]
    c = Counter()
    for name, seq in (("s", sol), ("i", ints), ("d", dur), ("r", dr)):
        n = max(len(seq), 1)
        for v, k in Counter(seq).items():
            c[(name, float(v))] = 100.0 * k / n
    return c


class MFDMap:
    """Vocabulary + x% class-significance selection fit on training songs only."""

    def __init__(self, x: float = 15):
        self.x = x

    def fit(self, toks, y):
        y = np.asarray(y)
        keep = set()
        for cl in np.unique(y):
            idx = np.where(y == cl)[0]
            cnt = Counter(k for i in idx for k in toks[i])
            keep |= {k for k, v in cnt.items() if v >= self.x / 100 * len(idx)}
        order = {"s": 0, "i": 1, "d": 2, "r": 3}
        self.vocab = sorted(keep, key=lambda k: (order[k[0]], k[1]))
        self.index = {k: j for j, k in enumerate(self.vocab)}
        return self

    def transform(self, toks):
        X = np.zeros((len(toks), len(self.vocab)), np.float32)
        for i, c in enumerate(toks):
            for k, v in c.items():
                j = self.index.get(k)
                if j is not None:
                    X[i, j] = v
        return X


class RELM:
    """(Regularized) extreme learning machine: tanh hidden layer with random weights; ridge output weights.
    gamma=None -> plain ELM (pseudo-inverse). Inputs are MFDMap percentages scaled to [0, 1]."""

    def __init__(self, n_hidden=1000, gamma=None, seed=0, lowpass=0):
        self.n_hidden, self.gamma, self.seed, self.lowpass = n_hidden, gamma, seed, lowpass

    def _h(self, X):
        X = X / 100.0
        if self.lowpass:  # crude stand-in for FIR-ELM's low-pass input filtering along the sorted-value axis
            k = np.ones(self.lowpass) / self.lowpass
            X = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, X)
        return np.tanh(X @ self.W + self.b)

    def fit(self, X, y):
        rng = np.random.RandomState(self.seed)
        self.classes_ = np.unique(y)
        T = (np.asarray(y)[:, None] == self.classes_[None]).astype(float) * 2 - 1
        self.W = rng.uniform(-1, 1, (X.shape[1], self.n_hidden))
        self.b = rng.uniform(-1, 1, self.n_hidden)
        H = self._h(X)
        if self.gamma is None:
            self.beta = np.linalg.pinv(H) @ T
        else:  # beta = (I/gamma + H'H)^-1 H'T
            self.beta = np.linalg.solve(np.eye(self.n_hidden) / self.gamma + H.T @ H, H.T @ T)
        return self

    def predict(self, X):
        return self.classes_[np.argmax(self._h(X) @ self.beta, 1)]


def make_clf(name):
    if name == "relm":
        return RELM(n_hidden=2000, gamma=1.0)
    if name == "elm":
        return RELM(n_hidden=200, gamma=None)
    if name == "relm_lp":
        return RELM(n_hidden=2000, gamma=1.0, lowpass=3)
    if name == "logreg":
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=3000, class_weight="balanced"))
    raise ValueError(name)


def fp_factory(toks_by_id, clf_name, x=15):
    def fp(tr, te):
        m = MFDMap(x).fit([toks_by_id[r["item_id"]] for r in tr], labels(tr))
        Xtr = m.transform([toks_by_id[r["item_id"]] for r in tr])
        Xte = m.transform([toks_by_id[r["item_id"]] for r in te])
        return make_clf(clf_name).fit(Xtr, labels(tr)).predict(Xte)
    return fp


def prior_protocol(recs, toks_by_id, clf_name, x=15, reps=5):
    """Stratified random 10-fold (NOT song-grouped), accuracy; averaged over `reps` shuffles."""
    y = labels(recs)
    accs, preds = [], None
    for rep in range(reps):
        pred = np.empty(len(y), dtype=object)
        for tr, te in StratifiedKFold(10, shuffle=True, random_state=rep).split(np.zeros(len(y)), y):
            pred[te] = fp_factory(toks_by_id, clf_name, x)([recs[i] for i in tr], [recs[i] for i in te])
        accs.append(scores(y, pred)["acc"])
        preds = pred if preds is None else preds
    return float(np.mean(accs)), float(np.std(accs)), preds


def run_e5prior():
    if already_logged("E5prior", "mfdmap-faithful-case1/logreg"):
        return None
    recs = e5prior()
    print({k: v for k, v in Counter(labels(recs)).items()}, len(recs))
    evs = faithful_events(recs)
    for case in (2, 1):
        toks = {r["item_id"]: mfdmap_tokens(e, case) for r, e in zip(recs, evs)}
        for clf in ("relm", "elm", "relm_lp", "logreg"):
            m, s, pred = prior_protocol(recs, toks, clf)
            print(f"  prior protocol case{case} {clf}: acc {m:.3f} ± {s:.3f}", flush=True)
            log_result(f"mfdmap-faithful-case{case}/{clf}/random10fold", "image", "E5prior", labels(recs), pred,
                       notes=f"PRIOR PROTOCOL (random stratified 10-fold, not song-grouped); mean acc over 5 "
                             f"shuffles {m:.4f}±{s:.4f}; Khoo 2013 thesis Essen Han 5 provinces; x=15")
            y, pred = cv_predict(recs, fp_factory(toks, clf))
            log_result(f"mfdmap-faithful-case{case}/{clf}", "image", "E5prior", y, pred,
                       notes="shared song-grouped 5-fold; Essen Han Dongbei/Shanxi/Sichuan/Guangdong/Jiangsu "
                             "(Khoo 2012/2013 MFDMap setting); vocab + x=15% selection fit in-fold")
    # sensitivity: x and hidden size, prior protocol (the thesis reported the max over such a grid)
    toks = {r["item_id"]: mfdmap_tokens(e, 2) for r, e in zip(recs, evs)}
    grid = []
    for x in (1, 5, 15, 30):
        for nh, g in ((500, 1.0), (2000, 1.0), (2000, 0.1), (5000, 10.0)):
            def fp(tr, te, x=x, nh=nh, g=g):
                mm = MFDMap(x).fit([toks[r["item_id"]] for r in tr], labels(tr))
                return RELM(nh, g).fit(mm.transform([toks[r["item_id"]] for r in tr]), labels(tr)).predict(
                    mm.transform([toks[r["item_id"]] for r in te]))
            y = labels(recs)
            accs = []
            for rep in range(3):
                pred = np.empty(len(y), dtype=object)
                for tr, te in StratifiedKFold(10, shuffle=True, random_state=rep).split(np.zeros(len(y)), y):
                    pred[te] = fp([recs[i] for i in tr], [recs[i] for i in te])
                accs.append(scores(y, pred)["acc"])
            grid.append((np.mean(accs), x, nh, g))
            print(f"  grid x={x} nh={nh} gamma={g}: acc {np.mean(accs):.3f}", flush=True)
    best = max(grid)
    print(f"  best-of-grid (optimistic, as in the thesis): acc {best[0]:.3f} at x={best[1]} nh={best[2]} "
          f"gamma={best[3]}")
    return best


SHAANXI_SITES = {"ziyang", "zhenba", "suide", "zizhou", "weinan", "yanan", "yulin", "mizhi", "jiaxian", "qingjian",
                 "hengshan", "ansai", "shenmu", "fugu", "yanchuan", "zichang", "ankang", "hanzhong", "shangluo",
                 "baoji", "dingbian", "jingbian", "luonan", "yanchang", "ganquan", "zhidan", "wuqi", "qitai"}


def run_diag():
    """Why is the replication below the published 72-85%? Prior protocol (random 10-fold, accuracy, 2 shuffles):
    (a) vocabulary + x% selection fit on ALL songs (as in the thesis) vs in-fold; (b) hidden size / gamma grid incl.
    the thesis' gamma=0.001; (c) HGB on MFDMap and on our theory features; (d) Shanxi restricted to true Shanxi
    sites (Essen spells Shaanxi 'shanxi'); (e) song-title duplicates across folds."""
    import re
    from sklearn.ensemble import HistGradientBoostingClassifier
    from regionclf.features import matrix
    recs = e5prior()
    y = labels(recs)
    dup = Counter(r["group"] for r in recs)
    print(f"  title groups with >1 song: {sum(v > 1 for v in dup.values())} ({sum(v for v in dup.values() if v > 1)} songs)")
    toks = [mfdmap_tokens(e, 2) for e in faithful_events(recs)]

    def rand_acc(X, mk, yy=y, reps=2):
        a = []
        for rep in range(reps):
            p = np.empty(len(yy), dtype=object)
            for tr, te in StratifiedKFold(10, shuffle=True, random_state=rep).split(X, yy):
                p[te] = mk().fit(X[tr], yy[tr]).predict(X[te])
            a.append((p == yy).mean())
        return float(np.mean(a))
    for x in (1, 15):
        X = MFDMap(x).fit(toks, y).transform(toks)
        for nh, g in ((500, 0.001), (1000, 0.01), (2000, 0.1), (1000, 1.0)):
            print(f"  all-song vocab x={x} dim={X.shape[1]} R-ELM nh={nh} gamma={g}: acc {rand_acc(X, lambda: RELM(nh, g)):.3f}",
                  flush=True)
        print(f"  all-song vocab x={x} HGB: acc {rand_acc(X, lambda: HistGradientBoostingClassifier(max_iter=200)):.3f}",
              flush=True)
    T = matrix(recs)
    print(f"  theory features HGB (prior protocol): acc {rand_acc(T, lambda: HistGradientBoostingClassifier(max_iter=200)):.3f}",
          flush=True)
    y_g, p_g = cv_predict(recs, lambda tr, te: HistGradientBoostingClassifier(max_iter=200).fit(
        matrix(tr), labels(tr)).predict(matrix(te)))
    log_result("ref-theory/hgb", "image", "E5prior", y_g, p_g,
               notes="REFERENCE: exp_theory features + HGB on the E5prior subset (shared grouped folds)")

    def are(r):
        t = (ESSEN / f"{r['item_id']}.krn").read_text(errors="ignore")
        m = re.search(r"!!!ARE:(.*)", t)
        return set(re.findall("[a-z]+", m.group(1).lower())) if m else set()
    keep = np.array([r["region"] != "Shanxi" or not (are(r) & SHAANXI_SITES) for r in recs])
    tk = [t for t, k in zip(toks, keep) if k]
    X2 = MFDMap(15).fit(tk, y[keep]).transform(tk)
    print(f"  true-Shanxi only ({(y[keep] == 'Shanxi').sum()} Shanxi songs), all-song vocab R-ELM: "
          f"acc {rand_acc(X2, lambda: RELM(1000, 0.01), y[keep]):.3f}", flush=True)


def run_task(name):
    if already_logged(name, "mfdmap-gong-case2/logreg"):
        return
    recs = task(name)
    toks = {r["item_id"]: mfdmap_tokens(gong_events(r), 2) for r in recs}
    for clf in ("relm", "logreg"):
        y, pred = cv_predict(recs, fp_factory(toks, clf))
        log_result(f"mfdmap-gong-case2/{clf}", "image", name, y, pred,
                   notes="MFDMap (Khoo 2013) from corpus notes, solfege rel. to estimated 宫; x=15 in-fold")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="E5prior,A5,E,T15,T5")
    ap.add_argument("--diag", action="store_true", help="replication-gap diagnostics on E5prior")
    a = ap.parse_args()
    if a.diag:
        run_diag()
        sys.exit()
    for t in a.tasks.split(","):
        run_e5prior() if t == "E5prior" else run_task(t)
