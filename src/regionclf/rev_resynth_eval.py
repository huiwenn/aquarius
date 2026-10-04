"""
Reviewer R3, steps 4–7: transcriber fidelity and region classification of resynthesized transcriptions.

Inputs: data/regionclf/resynth/{sample.csv, ref/, midi/game_pp/<cond>/} from rev_resynth_render.py and
rev_resynth_transcribe.sh. Resynthesized transcriptions are read exactly like the real ones
(corpus.midi_notes(beats=False): seconds, monophonized).

Fidelity (per condition, vs the rendered reference = score notes at the rendered timing / transposition):
  mir_eval note F1 — COnP (onset ±50 ms, pitch ±50 c), COnP@100 ms, COnPOff (+ offset 20%), onset-only F1,
  note-count ratio, and melodic-skeleton agreement (transcription/audit/melody.py: skeleton + transposition-
  invariant NW alignment accuracy). Plus the surface statistics from describe.py (偏音 share, # degrees in use,
  fourth-leap share) that separated scores from real transcriptions in §4 of docs/region_classification.md.

Classification: StratifiedGroupKFold(5, shuffle, seed 0) over the 600 sampled songs. Each fold trains on ALL other
Anthology songs (clean scores, all 8.6k minus any song whose title group is in the test fold) and tests the same
held-out songs as (i) clean scores and (ii) each resynthesized-transcription condition. Models: multi-viewpoint
n-gram TF-IDF + LR (exp_fusion.fit_ngram), the same with skeleton reduction L2 applied to train and test
(as in exp_reduce), and theory features + HGB. Real-transcription reference, recomputed here with the same models
so CIs are comparable: A→T5 transfer (train all Anthology except T5 title groups) and T5 within-domain grouped CV.
Macro-F1 with 95% bootstrap CIs (2000 resamples of songs); step differences use paired bootstrap on the same songs
(unpaired for the step to real recordings, which are different songs).
Logged with family "review_resynth", task A5resynth_<cond> (and T5 for the real-recording reference).

Outputs: data/regionclf/resynth/{fidelity.csv, fidelity_summary.csv, predictions.csv, summary.csv, steps.csv}

Run (py312, ~30–60 min):
  OMP_NUM_THREADS=3 /usr/local/Caskroom/miniforge/base/envs/py312/bin/python src/regionclf/rev_resynth_eval.py \
      [--conds plain,expressive,heavy,ornamented,accompanied] [--skip-real]
"""

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "3")

import mir_eval  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.model_selection import StratifiedGroupKFold  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import A5_REGIONS, D, labels, load, log_result, task  # noqa: E402
from regionclf.corpus import midi_notes  # noqa: E402
from regionclf.describe import song_stats  # noqa: E402
from regionclf.exp_fusion import doc, feat, fit_ngram, folds, hgb  # noqa: E402
from transcription.audit.melody import melodic_agreement, skeleton  # noqa: E402

R = D / "resynth"
FAMILY = "review_resynth"
B = 2000


def hz(m):
    return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def ref_dir(cond):
    return {"plain": "plain", "heavy": "heavy"}.get(cond, "expressive")


def seconds_notes(path: Path) -> np.ndarray:
    return midi_notes(path, beats=False) if path.exists() else np.zeros((0, 3))


# ---------------------------------------------------------------- fidelity
def fidelity(sample: pd.DataFrame, conds, A) -> pd.DataFrame:
    rows = []
    for c in ["clean"] + conds:
        for s in sample.itertuples():
            if c == "clean":
                st = song_stats(A[s.idx]["notes"])
                rows.append({"cond": c, "sid": s.sid, "region": s.region, **st})
                continue
            ref = seconds_notes(R / "ref" / ref_dir(c) / f"{s.sid}.mid")
            est = seconds_notes(R / "midi" / "game_pp" / c / f"{s.sid}.mid")
            row = {"cond": c, "sid": s.sid, "region": s.region, "n_ref": len(ref), "n_est": len(est)}
            if len(est) >= 2:
                ri, rp = np.c_[ref[:, 0], ref[:, 0] + ref[:, 1]], hz(ref[:, 2])
                ei, ep = np.c_[est[:, 0], est[:, 0] + est[:, 1]], hz(est[:, 2])
                T = mir_eval.transcription
                row["conp"] = T.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.05, offset_ratio=None)[2]
                row["conp100"] = T.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.1,
                                                               offset_ratio=None)[2]
                row["conpoff"] = T.precision_recall_f1_overlap(ri, rp, ei, ep, onset_tolerance=0.05)[2]
                row["onset"] = T.onset_precision_recall_f1(ri, ei, onset_tolerance=0.05)[2]
                sk_r = skeleton([(a, a + d, int(p)) for a, d, p in ref], min_dur=0.0)
                sk_e = skeleton([(a, a + d, int(p)) for a, d, p in est])
                row["skel_acc"] = melodic_agreement(sk_r, sk_e)["acc"]
                row.update(song_stats(est))
            else:
                row.update(conp=0.0, conp100=0.0, conpoff=0.0, onset=0.0, skel_acc=np.nan)
            rows.append(row)
    for r in task("T5"):
        rows.append({"cond": "real_T5", "sid": r["item_id"], "region": r["region"], **song_stats(r["notes"])})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- bootstrap
def macro_f1(y, p):
    return f1_score(y, p, average="macro", labels=sorted(set(y)))


def boot_ci(y, p, rng):
    n = len(y)
    v = [macro_f1(y[i], p[i]) for i in (rng.randint(0, n, n) for _ in range(B))]
    return np.percentile(v, [2.5, 97.5])


def paired_diff(y, p1, p2, rng):
    n = len(y)
    v = []
    for _ in range(B):
        i = rng.randint(0, n, n)
        v.append(macro_f1(y[i], p1[i]) - macro_f1(y[i], p2[i]))
    return np.percentile(v, [2.5, 97.5])


def unpaired_diff(y1, p1, y2, p2, rng):
    v = []
    for _ in range(B):
        i, j = rng.randint(0, len(y1), len(y1)), rng.randint(0, len(y2), len(y2))
        v.append(macro_f1(y1[i], p1[i]) - macro_f1(y2[j], p2[j]))
    return np.percentile(v, [2.5, 97.5])


# ---------------------------------------------------------------- classification
MODELS = ["ngram", "ngram_L2", "theory"]


def predict_all(models, train, test):
    """test: list of records (may have <3 notes → majority class of train)."""
    maj = pd.Series(labels(train)).value_counts().index[0]
    ok = [i for i, r in enumerate(test) if len(r["notes"]) >= 3]
    out = {}
    for name in MODELS:
        p = np.array([maj] * len(test), dtype=object)
        if ok:
            sub = [test[i] for i in ok]
            if name == "ngram":
                p[ok] = models[name].predict([doc(r) for r in sub])
            elif name == "ngram_L2":
                p[ok] = models[name].predict([doc(r, 2) for r in sub])
            else:
                p[ok] = models[name].predict(np.vstack([feat(r) for r in sub]))
        out[name] = p
    return out


def fit_all(train):
    return {"ngram": fit_ngram(train), "ngram_L2": fit_ngram(train, level=2),
            "theory": hgb().fit(np.vstack([feat(r) for r in train]), labels(train))}


def classify(sample, conds, A, skip_real):
    test_sets = {"clean": [A[i] for i in sample.idx]}
    for c in conds:
        test_sets[c] = [dict(source=f"resynth_{c}", item_id=s.sid, region=s.region, group=s.group,
                             notes=seconds_notes(R / "midi" / "game_pp" / c / f"{s.sid}.mid"))
                        for s in sample.itertuples()]
    y = sample.region.to_numpy()
    skf = StratifiedGroupKFold(5, shuffle=True, random_state=0)
    preds = {(c, m): np.empty(len(sample), dtype=object) for c in test_sets for m in MODELS}
    for k, (_, te) in enumerate(skf.split(np.zeros(len(y)), y, sample.group), 1):
        tg = set(sample.group.iloc[te])
        train = [r for r in A if r["group"] not in tg]
        models = fit_all(train)
        for c, recs in test_sets.items():
            for m, p in predict_all(models, train, [recs[i] for i in te]).items():
                preds[(c, m)][te] = p
        print(f"fold {k}: train {len(train)}  test {len(te)}", flush=True)
    rows = []
    for (c, m), p in preds.items():
        rows.append(pd.DataFrame({"set": f"A5resynth_{c}", "model": m, "sid": sample.sid, "y": y, "pred": p}))
    if not skip_real:
        T5 = task("T5")
        yt = labels(T5)
        tg = {r["group"] for r in T5}
        models = fit_all([r for r in A if r["group"] not in tg])
        for m, p in predict_all(models, A, T5).items():
            rows.append(pd.DataFrame({"set": "real_A→T5", "model": m, "sid": [r["item_id"] for r in T5],
                                      "y": yt, "pred": p}))
        within = {m: np.empty(len(T5), dtype=object) for m in MODELS}
        for tr, te in folds(T5):
            trr = [T5[i] for i in tr]
            for m, p in predict_all(fit_all(trr), trr, [T5[i] for i in te]).items():
                within[m][te] = p
        for m, p in within.items():
            rows.append(pd.DataFrame({"set": "real_T5_within", "model": m, "sid": [r["item_id"] for r in T5],
                                      "y": yt, "pred": p}))
    return pd.concat(rows, ignore_index=True)


def summarize(P: pd.DataFrame, conds, log=True):
    rng = np.random.RandomState(0)
    desc = {"ngram": "ngram7[1-4]/LR", "ngram_L2": "ngram7[1-4]/LR, skeleton L2 (train+test)", "theory": "theory/hgb"}
    rows = []
    for (s, m), g in P.groupby(["set", "model"], sort=False):
        y, p = g.y.to_numpy(), g.pred.to_numpy()
        lo, hi = boot_ci(y, p, rng)
        task_name = "T5" if s.startswith("real") else s
        exp = f"{desc[m]} [{s}]"
        note = ("R3 reference: T5 within-domain grouped CV" if s.endswith("within")
                else "R3 resynthesis test; train = clean Anthology")
        if log:
            sc = log_result(exp, FAMILY, task_name, y, p, notes=f"{note}; macro-F1 95% CI [{lo:.3f}, {hi:.3f}]")
        else:
            sc = {"macro_f1": macro_f1(y, p), "bal_acc": np.nan}
        rows.append({"set": s, "model": m, "n": len(y), "macro_f1": sc["macro_f1"], "ci_lo": lo, "ci_hi": hi,
                     "bal_acc": sc["bal_acc"]})
    summ = pd.DataFrame(rows)
    # gap decomposition: paired steps on the same 600 songs, unpaired step to real recordings
    chain = [("clean", "plain"), ("plain", "expressive"), ("expressive", "heavy"), ("expressive", "ornamented"),
             ("expressive", "accompanied"), ("clean", "expressive"), ("clean", "heavy")]
    steps = []
    for m in MODELS:
        get = lambda s: P[(P.set == s) & (P.model == m)]  # noqa: E731
        for a, b in chain:
            if a != "clean" and a not in conds or b not in conds:
                continue
            ga, gb = get(f"A5resynth_{a}"), get(f"A5resynth_{b}")
            y = ga.y.to_numpy()
            d = macro_f1(y, gb.pred.to_numpy()) - macro_f1(y, ga.pred.to_numpy())
            lo, hi = -paired_diff(y, ga.pred.to_numpy(), gb.pred.to_numpy(), rng)[::-1]
            steps.append({"model": m, "step": f"{a} → {b}", "delta": d, "ci_lo": lo, "ci_hi": hi, "paired": True})
        gr = get("real_A→T5")
        if len(gr):
            for a in ["clean"] + [c for c in conds if c in ("expressive", "heavy", "accompanied")]:
                ga = get(f"A5resynth_{a}")
                y1, p1 = ga.y.to_numpy(), ga.pred.to_numpy()
                y2, p2 = gr.y.to_numpy(), gr.pred.to_numpy()
                d = macro_f1(y2, p2) - macro_f1(y1, p1)
                lo, hi = -unpaired_diff(y1, p1, y2, p2, rng)[::-1]
                steps.append({"model": m, "step": f"{a} → real A→T5", "delta": d, "ci_lo": lo, "ci_hi": hi,
                              "paired": False})
    return summ, pd.DataFrame(steps)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conds", default="plain,expressive,heavy,ornamented,accompanied")
    ap.add_argument("--skip-real", action="store_true")
    ap.add_argument("--skip-fidelity", action="store_true")
    ap.add_argument("--no-log", action="store_true", help="preview: do not append to results.csv / write outputs")
    args = ap.parse_args()
    conds = [c for c in args.conds.split(",") if (R / "midi" / "game_pp" / c).exists()]
    print("conditions:", conds, flush=True)
    sample = pd.read_csv(R / "sample.csv")
    A = load("anthology")
    pd.set_option("display.width", 220)
    if not args.skip_fidelity:
        F = fidelity(sample, conds, A)
        F.to_csv(R / "fidelity.csv", index=False)
        cols = ["n_ref", "n_est", "conp", "conp100", "conpoff", "onset", "skel_acc", "pianyin", "n_degrees",
                "fourth", "step"]
        FS = F.groupby("cond", sort=False)[cols].mean()
        FS["est/ref"] = F.groupby("cond", sort=False).apply(lambda g: g.n_est.sum() / max(g.n_ref.sum(), 1))
        FS["n_empty(<3 notes)"] = F.groupby("cond", sort=False).apply(lambda g: int((g.n_est < 3).sum()))
        FS.to_csv(R / "fidelity_summary.csv")
        print(FS.round(3).to_string(), flush=True)
    P = classify(sample, conds, A, args.skip_real)
    summ, steps = summarize(P, conds, log=not args.no_log)
    if not args.no_log:
        P.to_csv(R / "predictions.csv", index=False)
        summ.to_csv(R / "summary.csv", index=False)
        steps.to_csv(R / "steps.csv", index=False)
    print(summ.round(3).to_string())
    print(steps.round(3).to_string())


if __name__ == "__main__":
    main()
