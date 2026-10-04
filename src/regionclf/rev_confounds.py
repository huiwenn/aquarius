"""
R6 (shortcut confounds) and R7 (validity of intermediate steps).

R6a  metadata-only baselines on T15: can region be predicted without notes?
       meta  = duration, #notes, notes/s, vocal-vs-accomp dB, performance type, upload year
       chan  = channel identity only (one-hot)
       both
     (grouped by song, LR + GBM). Upper bound on how much "region" is recoverable from collection artifacts.
R6b  Anthology editorial confound: n-gram classification of *volume* within a province (hebei1 vs hebei2,
     jiangsu1 vs jiangsu2) and of *province* within a 色彩区 (东北: hebei/tianjin/jilin; 江浙: jiangsu/shanghai),
     and lyrics-included vs melody-only subset. High accuracy between volumes of one province would reveal
     editor/OMR signatures.
R6c  length: macro-F1 of the n-gram model when every song is truncated to its first N notes (N = 16, 32, 64,
     128, all), for A5 and T15; and whether song length itself predicts region (A5).
R7a  宫 estimation validity:
       Anthology (简谱 rendered 1=C): the notated do is C, so estimate_gong should return 0.
       Essen: do from the kern key signature (*k[...] → major-key tonic pitch class).
       Transcriptions: agreement of 宫 between GAME and ROSVOT transcriptions of the same recording.
R7b  near-duplicate audit (A5): songs with different normalized titles but near-identical melodies
     (cosine ≥ 0.9 on degree 1–4-gram TF-IDF) that fall in different folds; re-score without them.
Results logged (family "review_confounds") and printed.

Run (py312): OMP_NUM_THREADS=2 python src/regionclf/rev_confounds.py
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf import exp_fusion as F  # noqa: E402
from regionclf.common import folds, labels, load, log_result, task  # noqa: E402
from regionclf.features import estimate_gong  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FAM = "review_confounds"


def cv_matrix(name, tname, recs, X, model="lr", by="group"):
    y = labels(recs)
    pred = np.empty(len(recs), dtype=object)
    for tr, te in folds(recs, by=by):
        m = (make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced"))
             if model == "lr" else HistGradientBoostingClassifier(class_weight="balanced", random_state=0))
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return log_result(name, FAM, tname, y, pred)


def r6a():
    recs = task("T15")
    idx = pd.read_csv(ROOT / "data" / "regions_transcription" / "dataset_index.csv").set_index("video_id")
    rows = []
    for r in recs:
        m = idx.loc[r["item_id"]]
        n = r["notes"]
        dur = float(m.duration_s) if pd.notna(m.duration_s) else n[-1, 0]
        yr = int(str(m.upload_date)[:4]) if pd.notna(m.upload_date) else 2015
        rows.append([dur, len(n), len(n) / max(dur, 1), float(np.nan_to_num(m.vocal_db)), yr,
                     m.performance_type == "原生态", m.performance_type == "民族唱法"])
    meta = np.array(rows, float)
    chans = sorted({r["channel"] for r in recs})
    chan = np.array([[r["channel"] == c for c in chans] for r in recs], float)
    for name, X in [("metadata only", meta), ("channel identity only", chan),
                    ("metadata + channel", np.hstack([meta, chan]))]:
        cv_matrix(f"shortcut: {name} (LR)", "T15", recs, X, "lr")
        cv_matrix(f"shortcut: {name} (GBM)", "T15", recs, X, "gbm")


def r6d():
    """Channel held constant: classify region within the single channel that spans most regions (Rhymoi), with
    song-grouped folds (music only; the channel can't help). Plus metadata-only under channel-grouped folds."""
    recs = task("T15")
    rhy = [r for r in recs if "Rhymoi" in r["channel"]]
    counts = pd.Series([r["region"] for r in rhy]).value_counts()
    keep = set(counts[counts >= 8].index)
    rhy = [r for r in rhy if r["region"] in keep]
    print(f"[R6d] Rhymoi-only subset: {len(rhy)} recordings, {len(keep)} regions with ≥8: {counts[counts >= 8].to_dict()}")
    y, p = F_cv(rhy)
    log_result("n-gram within one channel (Rhymoi only)", FAM, "T-Rhymoi", y, p, "channel held constant")
    idx = pd.read_csv(ROOT / "data" / "regions_transcription" / "dataset_index.csv").set_index("video_id")
    meta = np.array([[float(idx.loc[r["item_id"], "duration_s"]), len(r["notes"]),
                      len(r["notes"]) / max(1.0, float(idx.loc[r["item_id"], "duration_s"])),
                      float(np.nan_to_num(idx.loc[r["item_id"], "vocal_db"]))] for r in rhy])
    cv_matrix("shortcut: metadata only within Rhymoi (GBM)", "T-Rhymoi", rhy, meta, "gbm")
    meta_all = []
    for r in recs:
        m = idx.loc[r["item_id"]]
        meta_all.append([float(m.duration_s), len(r["notes"]), len(r["notes"]) / max(1.0, float(m.duration_s)),
                         float(np.nan_to_num(m.vocal_db)), m.performance_type == "原生态"])
    cv_matrix("shortcut: metadata only, folds by channel (GBM)", "T15", recs, np.array(meta_all, float), "gbm",
              by="channel")


def r6e():
    """Leave-one-volume-out for regions with several Anthology volumes: train on all other songs (all
    regions, excluding the held-out volume and same-title songs), test on the held-out volume. Region identity must
    then transfer to an unseen editorial unit. Compared with in-distribution (grouped CV) accuracy on that volume."""
    A = load("anthology")
    y_all, p_all = F_cv(A)
    rows = []
    for vol in ["hebei1", "hebei2", "tianjin", "jilin", "jiangsu1", "jiangsu2", "shanghai", "guangdong", "hainan"]:
        test = [r for r in A if r["channel"] == vol]
        tg = {r["group"] for r in test}
        train = [r for r in A if r["channel"] != vol and r["group"] not in tg]
        pred = F.ngram_fold(train, test)
        acc_lovo = np.mean(pred == labels(test))
        m = np.array([r["channel"] == vol for r in A])
        acc_cv = np.mean(p_all[m] == y_all[m])
        rows.append((vol, test[0]["region"], len(test), acc_lovo, acc_cv))
        print(f"[R6e] held-out volume {vol:9s} ({test[0]['region']}, n={len(test)}): accuracy {acc_lovo:.3f} "
              f"(in-distribution grouped CV on same songs: {acc_cv:.3f})", flush=True)
    d = pd.DataFrame(rows, columns=["volume", "region", "n", "acc_leave_volume_out", "acc_grouped_cv"])
    w = d.n / d.n.sum()
    print(f"[R6e] weighted accuracy: leave-volume-out {np.sum(w * d.acc_leave_volume_out):.3f} vs grouped CV "
          f"{np.sum(w * d.acc_grouped_cv):.3f}")
    d.to_csv(ROOT / "data" / "regionclf" / "review_leave_volume_out.csv", index=False)


def r6b():
    A = load("anthology")
    for vols in (("hebei1", "hebei2"), ("jiangsu1", "jiangsu2")):
        sub = [dict(r, region=r["channel"]) for r in A if r["channel"] in vols]
        y, p = F_cv(sub)
        log_result(f"volume vs volume {vols[0]}/{vols[1]} (n-gram)", FAM, "A-volumes", y, p,
                   "same province, different volume: editorial/OMR signature test")
    for reg, provs in (("东北部平原", ("Hebei", "Tianjin", "Jilin")), ("江浙平原", ("Jiangsu", "Shanghai"))):
        sub = [dict(r, region=r["province"]) for r in A if r["region"] == reg and r["province"] in provs]
        y, p = F_cv(sub)
        log_result(f"province within {reg} {'/'.join(provs)} (n-gram)", FAM, "A-provinces", y, p)
    sub = [dict(r, region=r["subset"]) for r in A]
    y, p = F_cv(sub)
    log_result("lyrics-included vs melody-only subset (n-gram)", FAM, "A-subset", y, p,
               "OMR pipeline / notation-style signature test")


def F_cv(recs):
    y = labels(recs)
    pred = np.empty(len(recs), dtype=object)
    for tr, te in folds(recs):
        pred[te] = F.ngram_fold([recs[i] for i in tr], [recs[i] for i in te])
    return y, pred


def r6c():
    for tname in ("T15", "A5"):
        recs = task(tname)
        for N in (16, 32, 64, 128):
            sub = [dict(r, notes=r["notes"][:N], item_id=f"{r['item_id']}@{N}") for r in recs]
            y, p = F_cv(sub)
            log_result(f"n-gram, songs truncated to first {N} notes", FAM, tname, y, p)
    recs = task("A5")
    X = np.array([[len(r["notes"]), r["notes"][-1, 0] + r["notes"][-1, 1]] for r in recs], float)
    cv_matrix("shortcut: song length only (#notes, duration in beats)", "A5", recs, X, "gbm")


KEY_TONIC = {"": 0, "b-": 5, "b-e-": 10, "b-e-a-": 3, "b-e-a-d-": 8, "f#": 7, "f#c#": 2, "f#c#g#": 9,
             "f#c#g#d#": 4, "b-e-a-d-g-": 1, "f#c#g#d#a#": 11}


def r7a():
    A = load("anthology")
    g = np.array([estimate_gong(r["notes"]) for r in A])
    print(f"\n[R7a] Anthology (1=C): estimate_gong == 0 for {np.mean(g == 0):.3f} of songs; "
          f"distribution of errors: {pd.Series(g[g != 0]).value_counts().head(5).to_dict()}")
    ok, n = 0, 0
    for r in load("essen"):
        p = ROOT / "data" / "raw" / "essen" / "asia" / "china" / f"{r['item_id']}.krn"
        if not p.exists():
            continue
        m = re.search(r"^\*k\[([^\]]*)\]", p.read_text(errors="ignore"), re.M)
        if not m or m.group(1) not in KEY_TONIC:
            continue
        n += 1
        ok += estimate_gong(r["notes"]) == KEY_TONIC[m.group(1)]
    print(f"[R7a] Essen: estimate_gong equals the key-signature do for {ok / max(n, 1):.3f} of {n} songs")
    gm = {r["item_id"]: estimate_gong(r["notes"]) for r in load("trans_game_pp")}
    rv = {r["item_id"]: estimate_gong(r["notes"]) for r in load("trans_rosvot")}
    both = sorted(set(gm) & set(rv))
    print(f"[R7a] transcriptions: GAME vs ROSVOT 宫 agreement {np.mean([gm[i] == rv[i] for i in both]):.3f} "
          f"(n={len(both)}); chance ≈ 0.083")


def r7b():
    recs = task("A5")
    docs = [" ".join(F.doc(r)[0].split()) for r in recs]  # degree vocabulary
    X = TfidfVectorizer(token_pattern=r"\S+", ngram_range=(1, 4), sublinear_tf=True, min_df=2).fit_transform(docs)
    fold_of = np.empty(len(recs), int)
    for k, (_, te) in enumerate(folds(recs)):
        fold_of[te] = k
    dup = np.zeros(len(recs), bool)
    for start in range(0, len(recs), 1000):
        S = cosine_similarity(X[start:start + 1000], X)
        for i in range(S.shape[0]):
            gi = start + i
            S[i, gi] = 0
            cand = np.where(S[i] >= 0.9)[0]
            if any(fold_of[c] != fold_of[gi] and recs[c]["group"] != recs[gi]["group"] for c in cand):
                dup[gi] = True
    print(f"\n[R7b] A5 near-duplicates across folds (cosine ≥ 0.9, different titles): {dup.sum()} songs "
          f"({dup.mean():.3%})")
    y, p = F_cv(recs)
    keep = ~dup
    log_result("n-gram, test songs without cross-fold near-duplicates", FAM, "A5", y[keep], p[keep],
               f"excluded {dup.sum()} near-duplicate test songs")
    log_result("n-gram, all test songs (same run)", FAM, "A5", y, p)


def main() -> None:
    for step in sys.argv[1:] or ["r7a", "r6a", "r6b", "r6c", "r7b"]:
        print(f"\n===== {step}", flush=True)
        globals()[step]()


if __name__ == "__main__":
    main()
