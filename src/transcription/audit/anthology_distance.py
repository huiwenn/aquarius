"""
How far apart are our transcriptions and the Anthology scores of the same song?

Pairs: data/colour_regions/anthology_overlap.csv (verdict match or uncertain), expanded to every recording of the song.
For each (recording, Anthology score, transcription variant) the script compares the transcription with the score:

  pitch_acc     share of score notes matched by an identical pitch in the transcription, after the best transposition
                (semi-global Needleman-Wunsch: the one-verse score is located inside the multi-verse performance;
                audit/melody.py conventions: notes < 0.08 s dropped, repeats merged)
  interval_acc  the same on interval sequences (no transposition needed; intervals clipped to ±12)
  contour_acc   the same on the direction of each interval (up / down / same): robust to small pitch errors
  pc_cos        cosine similarity of duration-weighted pitch-class histograms after the best transposition
                (scale / mode content, independent of note order)
  ambitus_diff  |range of the transcription| - |range of the score|, in semitones (first verse-length span)
  note_ratio    raw transcription notes per score note in the aligned span (ornament and split-note excess)

Chance baseline: the same transcription against N_RAND random scores from the same Anthology volume. Each metric gets
a percentile against that baseline and a gap (pair value - baseline mean). A pair "confirms" the overlap when
pitch_acc is above the 95th baseline percentile.

The scores are 1950s-1990s notations of a variant of the song, not transcriptions of this recording, so distance
measures variant + notation convention + transcription error together. These numbers are EXPLORATORY: they do not
separate the three sources (docs/thesis_evidence_plan.md, evidence rule).

Outputs: data/transcription/audit/anthology_distance.csv (one row per recording × score × variant)
         data/transcription/audit/anthology_distance_summary.md
Run (py312): python src/transcription/audit/anthology_distance.py [--variants primary,game_ens3_pp,game_pp,rosvot]
             [--summary-only]  (rebuild the summary from the CSV)
"""

import argparse
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from melody import best_shift, load_notes, skeleton  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ANTH = ROOT / "data" / "raw" / "anthology_chinese_folk_songs"
CORPUS = ROOT / "data" / "colour_regions" / "corpus"
OUT = ROOT / "data" / "transcription" / "audit"
N_RAND = 30
MAX_PERF = 400  # transcription skeleton notes considered (the score's verse is searched inside them)
SEED = 20261011


@numba.njit(cache=True)
def semiglobal(a, b, cap):
    """Score b (one verse) aligned inside a (performance). Substitution cost min(|Δ|, cap)/cap, gap 1.
    Returns (#identical aligned pairs, #aligned pairs, start index in a, end index in a)."""
    n, m = len(a), len(b)
    D = np.zeros((n + 1, m + 1))
    for j in range(m + 1):
        D[0, j] = j
    for i in range(1, n + 1):
        D[i, 0] = 0.0
        for j in range(1, m + 1):
            sub = min(abs(a[i - 1] - b[j - 1]), cap) / cap
            D[i, j] = min(D[i - 1, j] + 1, D[i, j - 1] + 1, D[i - 1, j - 1] + sub)
    i = 0
    best = D[0, m]
    for k in range(1, n + 1):
        if D[k, m] < best:
            best, i = D[k, m], k
    end = i
    j, match, pairs = m, 0, 0
    while i > 0 and j > 0:
        sub = min(abs(a[i - 1] - b[j - 1]), cap) / cap
        if abs(D[i, j] - (D[i - 1, j - 1] + sub)) < 1e-9:
            pairs += 1
            if a[i - 1] == b[j - 1]:
                match += 1
            i -= 1
            j -= 1
        elif abs(D[i, j] - (D[i - 1, j] + 1)) < 1e-9:
            i -= 1
        else:
            j -= 1
    return match, pairs, i, end


def pc_hist(notes) -> np.ndarray:
    h = np.zeros(12)
    for s, e, p in notes:
        h[p % 12] += e - s
    return h / max(h.sum(), 1e-9)


def compare(perf_raw, perf, score_raw, score) -> dict:
    if len(perf) < 8 or len(score) < 8:
        return {}
    a = perf[:MAX_PERF]
    shift = best_shift(a, score)
    m, pairs, i0, i1 = semiglobal(a, score + shift, 2)
    ia, ib = np.clip(np.diff(a), -12, 12), np.clip(np.diff(score), -12, 12)
    mi, _, _, _ = semiglobal(ia, ib, 2)
    ca, cb = np.sign(ia), np.sign(ib)
    mc, _, _, _ = semiglobal(ca, cb, 1)
    hp, hs = pc_hist(perf_raw), np.roll(pc_hist(score_raw), shift % 12)
    span = a[i0:i1] if i1 > i0 else a
    # raw transcription notes falling in the aligned span (by skeleton index → time is unknown, so use proportion)
    raw_per_sk = len(perf_raw) / max(len(perf), 1)
    return dict(pitch_acc=m / len(score), interval_acc=mi / len(ib), contour_acc=mc / len(cb),
                pc_cos=float(hp @ hs / max(np.linalg.norm(hp) * np.linalg.norm(hs), 1e-9)),
                ambitus_diff=int((span.max() - span.min()) - (score.max() - score.min())),
                note_ratio=raw_per_sk * len(span) / len(score), coverage=pairs / len(score), shift=int(shift))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="primary,game_ens3_pp,game_pp,rosvot")
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if a.summary_only:
        return summarise(pd.read_csv(OUT / "anthology_distance.csv"))
    variants = a.variants.split(",")
    rng = np.random.default_rng(SEED)
    ov = pd.read_csv(ROOT / "data" / "colour_regions" / "anthology_overlap.csv")
    rec = pd.read_csv(ROOT / "data" / "colour_regions" / "recordings.csv").set_index("item_id")
    files = pd.read_csv(CORPUS / "files.csv")
    midi = files[files.layer == "midi"].set_index(["item_id", "variant"]).path
    by_vol = {}
    for p in ANTH.rglob("*.mid"):
        by_vol.setdefault(p.parent.name, []).append(p)

    def score_file(aid: str) -> Path:
        vol, stem = aid.split(":", 1)[1].split("/", 1)
        return next(ANTH.glob(f"*/{vol}/{stem}.mid"))

    cache = {}

    def score_seq(p: Path):
        if p not in cache:
            raw = load_notes(p)
            cache[p] = (raw, skeleton(raw, min_dur=0.06))
        return cache[p]

    rows = []
    pairs = [(r, i) for r in ov.itertuples() for i in str(r.item_ids).split("; ")]
    print(len(ov), "song-score pairs →", len(pairs), "recording-score pairs", flush=True)
    for n, (r, iid) in enumerate(pairs, 1):
        sp = score_file(r.anthology_item_id)
        s_raw, s_sk = score_seq(sp)
        pool = [p for p in by_vol[r.anthology_volume] if p != sp]
        rand = [pool[k] for k in rng.choice(len(pool), N_RAND, replace=False)]
        for v in variants:
            path = midi.get((iid, v))
            if not isinstance(path, str):
                continue
            p_raw = load_notes(CORPUS / path)
            p_sk = skeleton(p_raw, min_dur=0.08)
            res = compare(p_raw, p_sk, s_raw, s_sk)
            if not res:
                continue
            base = [compare(p_raw, p_sk, *score_seq(q)) for q in rand]
            base = pd.DataFrame([b for b in base if b])
            row = dict(song_id=r.song_id, song_name=r.song_name, region=r.region, item_id=iid,
                       round=rec.at[iid, "round"] if iid in rec.index else None,
                       song_class=None, anthology_item_id=r.anthology_item_id, anthology_volume=r.anthology_volume,
                       same_province=r.same_province, overlap_verdict=r.verdict, variant=v,
                       transcription_model=rec.at[iid, "transcription_model"] if iid in rec.index else None, **res)
            for k in ("pitch_acc", "interval_acc", "contour_acc", "pc_cos"):
                row[k + "_base"] = base[k].mean()
                row[k + "_pct"] = 100 * (base[k] < res[k]).mean()
            rows.append(row)
        if n % 50 == 0:
            print(f"[{n}/{len(pairs)}]", flush=True)
    d = pd.DataFrame(rows)
    sl = pd.read_csv(ROOT / "data" / "colour_regions" / "song_labels.csv").set_index("song_id")
    d["song_class"] = d.song_id.map(sl.song_class)
    d["confirms"] = d.pitch_acc_pct >= 95
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "anthology_distance.csv", index=False)
    summarise(d)


def summarise(d: pd.DataFrame) -> None:
    met = ["pitch_acc", "interval_acc", "contour_acc", "pc_cos"]
    # best score per (recording, variant): a song printed in several versions counts once, at its closest version
    best = d.sort_values("pitch_acc").groupby(["item_id", "variant", "overlap_verdict"]).tail(1)
    L = ["# Transcriptions vs Anthology scores (exploratory)", "",
         f"{d.item_id.nunique()} recordings, {d.anthology_item_id.nunique()} Anthology scores, "
         f"{d.song_id.nunique()} songs; baseline = {N_RAND} random scores from the same volume.", "",
         "## Best-matching score per recording, by variant (verdict = match)", ""]
    b = best[best.overlap_verdict == "match"]
    t = b.groupby("variant").agg(recordings=("item_id", "nunique"),
                                 **{f"{k}": (k, "median") for k in met},
                                 **{f"{k}_base": (k + "_base", "median") for k in ("pitch_acc", "contour_acc")},
                                 confirms=("confirms", "mean"), note_ratio=("note_ratio", "median"),
                                 ambitus_diff=("ambitus_diff", "median"))
    L += [t.round(3).to_markdown(), ""]
    p = best[best.variant == "primary"]
    g = p.groupby("overlap_verdict").agg(recordings=("item_id", "nunique"), pitch_acc=("pitch_acc", "median"),
                                         pitch_base=("pitch_acc_base", "median"), contour_acc=("contour_acc", "median"),
                                         pc_cos=("pc_cos", "median"), confirms=("confirms", "mean"))
    L += ["## Primary transcription by overlap verdict", "", g.round(3).to_markdown(), ""]
    p = p[p.overlap_verdict == "match"]  # breakdowns below: confirmed overlap pairs only
    for col, title in (("same_province", "same province"),
                       ("region", "region"), ("song_class", "song class"), ("round", "collection round"),
                       ("transcription_model", "primary model")):
        g = p.groupby(col).agg(recordings=("item_id", "nunique"), pitch_acc=("pitch_acc", "median"),
                               pitch_base=("pitch_acc_base", "median"), contour_acc=("contour_acc", "median"),
                               pc_cos=("pc_cos", "median"), confirms=("confirms", "mean"))
        L += [f"## Primary transcription by {title} (verdict = match)", "", g.round(3).to_markdown(), ""]
    (OUT / "anthology_distance_summary.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
