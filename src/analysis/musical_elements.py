"""
Musical elements by colour region and over time (exploratory).

Two inputs:
  1. Essen Folksong Collection, China subset (Humdrum **kern), mapped to colour
     regions with the same rules as src/regionclf/corpus.py (essen_region).
     Gives melody, rhythm, tonality (pentatonic mode) and form features.
     Get it with: git clone --depth 1 --filter=blob:none --sparse
       https://github.com/ccarh/essen-folksong-collection data/raw/essen_src
       (sparse-checkout set asia/china), then copy asia/china to data/raw/essen/asia/china.
  2. metadata/recordings.csv (the released corpus): performance practice
     (performance type, accompaniment, singers), song class and genre, length,
     composition period/year and upload year.

Timbre, dynamics and texture need audio and are not measured here. Harmony
does not apply to these monophonic songs.

Tests: Kruskal-Wallis (numeric) or chi-square (categorical) across regions with
at least MIN_N items, Benjamin-Hochberg FDR over all tests in a family, with
effect sizes (epsilon squared, Cramer's V). Spearman for trends. Everything is
exploratory: see CLAUDE.md "Evidence rule".

Run: python src/analysis/musical_elements.py
Writes: notebooks/elements_results/*.csv (region-level tables) and
notebooks/figures/elements_*.png. The per-song Essen table goes to
data/analysis/ (not tracked): the Essen licence restricts redistribution.
"""

import math
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from colour_regions.regions import EN, ORDER  # noqa: E402

ESSEN = ROOT / "data" / "raw" / "essen" / "asia" / "china"
REC = ROOT / "metadata" / "recordings.csv"
OUT = ROOT / "notebooks" / "elements_results"
FIG = ROOT / "notebooks" / "figures"
PER_SONG = ROOT / "data" / "analysis" / "essen_song_features.csv"
MIN_N = 20
ALPHA = 0.05

# Region mapping for Essen: same tables and rule as src/regionclf/corpus.py.
# (Copied, not imported, because corpus.py needs pretty_midi at import time.)
from secaiqu.mapping import PROVINCE_TO_SECAIQU  # noqa: E402

ESSEN_PROVINCES = {"shanbei": "Northern Shaanxi", "shaanxi": "Shaanxi", "shsanxi": "Shanxi", "shanxi": "Shanxi",
                   "fujian": "Fujian", "hebei": "Hebei", "jiangsu": "Jiangsu", "sichuan": "Sichuan",
                   "henan": "Henan", "gansu": "Gansu", "yunnan": "Yunnan", "taiwan": "Taiwan",
                   "qinghai": "Qinghai", "hubei": "Hubei", "anhui": "Anhui", "zhejiang": "Zhejiang",
                   "shandong": "Shandong", "hunan": "Hunan", "jiangxi": "Jiangxi", "guangdong": "Guangdong",
                   "guangxi": "Guangxi", "guizhou": "Guizhou", "liaoning": "Liaoning", "jilin": "Jilin",
                   "heilongjiang": "Heilongjiang", "ningxia": "Ningxia", "neimeng": "Inner Mongolia"}
ESSEN_ETHNIC = {"menggu": "北方草原文化民歌区", "dawoer": "北方草原文化民歌区", "elunchun": "北方草原文化民歌区",
                "ewenke": "北方草原文化民歌区", "hezhe": "北方草原文化民歌区",
                "weiwuer": "新疆民歌区", "hasake": "新疆民歌区", "keerkezi": "新疆民歌区", "tajike": "新疆民歌区",
                "zang": "藏族民歌区",
                "miao": "西南多民族古老原始文化民歌区", "dong": "西南多民族古老原始文化民歌区",
                "zhuang": "西南多民族古老原始文化民歌区", "yao": "西南多民族古老原始文化民歌区",
                "yi": "西南多民族古老原始文化民歌区", "bai": "西南多民族古老原始文化民歌区",
                "maonan": "西南多民族古老原始文化民歌区", "hani": "西南多民族古老原始文化民歌区",
                "naxi": "西南多民族古老原始文化民歌区", "lisu": "西南多民族古老原始文化民歌区",
                "hui": "西北部高原", "yugu": "西北部高原"}

# Approximate province centres (lat, lon), for the north-south / east-west trends.
PROVINCE_LATLON = {
    "Northern Shaanxi": (37.5, 109.5), "Shaanxi": (34.3, 108.9), "Shanxi": (37.6, 112.3), "Fujian": (26.1, 118.3),
    "Hebei": (38.5, 115.5), "Jiangsu": (32.9, 119.5), "Sichuan": (30.6, 103.9), "Henan": (34.3, 113.6),
    "Gansu": (36.1, 103.8), "Yunnan": (25.0, 101.7), "Taiwan": (23.7, 121.0), "Qinghai": (36.6, 101.8),
    "Hubei": (30.9, 112.3), "Anhui": (31.8, 117.2), "Zhejiang": (29.2, 120.2), "Shandong": (36.4, 118.0),
    "Hunan": (27.6, 111.7), "Jiangxi": (27.6, 115.8), "Guangdong": (23.3, 113.4), "Guangxi": (23.7, 108.6),
    "Guizhou": (26.8, 106.7), "Liaoning": (41.3, 122.6), "Jilin": (43.7, 126.2), "Heilongjiang": (47.0, 128.0),
    "Ningxia": (37.3, 106.2), "Inner Mongolia": (44.0, 113.5),
}


def essen_meta(text):
    meta = {}
    for line in text.splitlines():
        if line.startswith("!!!OTL:"):
            meta["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("!!!ARE:"):
            meta["are"] = line.split(":", 1)[1].strip()
        elif "Ethnic Group:" in line:
            meta["ethnic"] = line.split(":", 1)[1].strip()
    return meta


def essen_region(meta):
    eth = re.sub(r"[^a-z]", " ", meta.get("ethnic", "").lower()).split()
    if eth and eth[0] not in ("han", "ha", "hanzu"):
        return (ESSEN_ETHNIC.get(eth[0]), None)
    are = meta.get("are", "").lower().replace(",", " ")
    for kw, prov in ESSEN_PROVINCES.items():
        if re.search(rf"\b{kw}\b", are):
            if prov == "Inner Mongolia":
                return "北方草原文化民歌区", prov
            return PROVINCE_TO_SECAIQU.get(prov), prov
    return None, None


# ---------------------------------------------------------------- kern parse --
NOTE_RE = re.compile(r"^([{(\[]*)(\d+)(\.*)([a-gA-GrR]+)([#\-n]*)(.*)$")


def kern_pitch(letters, acc):
    base = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}[letters[0].lower()]
    octave = 4 + (len(letters) - 1) if letters[0].islower() else 3 - (len(letters) - 1)
    return 12 * (octave + 1) + base + acc.count("#") - acc.count("-")


def parse_kern(text):
    """Monophonic Essen kern -> notes [(pitch, quarter_length, phrase_no)], meters list."""
    notes, meters, phrase, open_tie = [], [], 0, False
    started = False
    for line in text.splitlines():
        if not line or line.startswith("!"):
            continue
        tok = line.split("\t")[0].strip()
        if tok.startswith("*M") and re.match(r"\*M\d+/\d+", tok):
            meters.append(tok[2:])
        if tok.startswith("*MX") or tok.startswith("*met"):
            meters.append("free") if tok.startswith("*MX") else None
        if tok.startswith("*") or tok.startswith("="):
            continue
        if "q" in tok:          # grace note
            continue
        if tok.startswith("{"):
            phrase += 1 if started else 0
            started = True
        m = NOTE_RE.match(tok)
        if not m:
            continue
        _, dur, dots, letters, acc, rest = m.groups()
        ql = 4.0 / int(dur) if int(dur) > 0 else 8.0
        ql *= (2 - 0.5 ** len(dots)) if dots else 1
        if letters[0] in "rR":
            continue
        p = kern_pitch(letters, acc)
        tie_cont = "_" in rest or "]" in rest
        if (tie_cont or tok.startswith("]") or "_" in tok) and open_tie and notes and notes[-1][0] == p:
            notes[-1] = (p, notes[-1][1] + ql, notes[-1][2])
        else:
            notes.append((p, ql, phrase))
        open_tie = "[" in tok or "_" in tok
    return notes, meters


PENTA = [0, 2, 4, 7, 9]
MODE_NAMES = {0: "gong", 2: "shang", 4: "jue", 7: "zhi", 9: "yu"}


def song_features(notes, meters):
    p = np.array([n[0] for n in notes], float)
    d = np.array([n[1] for n in notes], float)
    ph = np.array([n[2] for n in notes])
    iv = np.diff(p)
    aiv = np.abs(iv)
    final_pc = int(p[-1]) % 12
    # Pentatonic collection that covers the most sounding time; mode = role of the final.
    w = Counter()
    for pc, dur in zip(p.astype(int) % 12, d):
        w[pc] += dur
    best = max(range(12), key=lambda g: (sum(w[(g + k) % 12] for k in PENTA), w[g]))
    coll = {(best + k) % 12 for k in PENTA}
    total = sum(w.values())
    rel = (final_pc - best) % 12
    mode = MODE_NAMES.get(rel, "other")
    # Phrases (from kern {...} marks); a song with none counts as one phrase.
    n_phr = int(ph.max()) + 1 if len(ph) else 1
    phrase_ivs = []
    for k in range(n_phr):
        idx = np.where(ph == k)[0]
        if len(idx) > 1:
            phrase_ivs.append(tuple(np.diff(p[idx]).astype(int)))
    rep = sum(1 for i, s in enumerate(phrase_ivs) if s in phrase_ivs[:i]) / max(1, len(phrase_ivs))
    ends = [p[np.where(ph == k)[0][-1]] for k in range(n_phr) if (ph == k).any()]
    ends_on_final = np.mean([int(e) % 12 == final_pc for e in ends]) if ends else np.nan
    probs = np.array(list(Counter(np.round(d, 3)).values()), float)
    probs /= probs.sum()
    meter0 = meters[0] if meters else "free"
    num = int(meter0.split("/")[0]) if "/" in meter0 else 0
    return {
        # melody
        "ambitus": float(p.max() - p.min()),
        "mean_abs_interval": float(aiv.mean()),
        "step_share": float((aiv <= 2).mean()),
        "leap_share": float((aiv >= 5).mean()),
        "large_leap_share": float((aiv >= 7).mean()),
        "descending_share": float((iv < 0).mean()),
        "final_below_mean": float(p.mean() - p[-1]),
        # tonality
        "mode": mode,
        "non_pentatonic_share": float(1 - sum(w[pc] for pc in coll) / total),
        # rhythm
        "n_durations": int(len(probs)),
        "duration_entropy": float(-(probs * np.log2(probs)).sum()),
        "dotted_share": float(np.isin(np.round(d, 4), [0.375, 0.75, 1.5, 3.0]).mean()),
        "short_note_share": float((d <= 0.25).mean()),
        # 3/4, 3/8, 9/8 count as triple; 6/8 is compound duple.
        "meter_class": "free" if meter0 == "free" else ("triple" if num in (3, 9) else "duple"),
        "meter_changes": int(len(set(meters)) > 1),
        # form
        "n_phrases": n_phr,
        "notes_per_phrase": float(len(p) / n_phr),
        "phrase_repetition": float(rep),
        "phrase_ends_on_final": float(ends_on_final),
        "n_notes": int(len(p)),
    }


def load_essen():
    rows = []
    for f in sorted(ESSEN.glob("*/*.krn")):
        text = f.read_text(errors="ignore")
        meta = essen_meta(text)
        region, prov = essen_region(meta)
        if not region:
            continue
        notes, meters = parse_kern(text)
        if len(notes) < 8:
            continue
        r = {"item": f"{f.parent.name}/{f.stem}", "subset": f.parent.name, "region": region,
             "region_en": EN[region], "province": prov, "title": meta.get("title", "")}
        r.update(song_features(notes, meters))
        lat, lon = PROVINCE_LATLON.get(prov, (np.nan, np.nan))
        r["lat"], r["lon"] = lat, lon
        rows.append(r)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- stats --
def kruskal(df, col, group="region_en"):
    groups = [g[col].dropna().values for _, g in df.groupby(group) if g[col].notna().sum() >= MIN_N]
    if len(groups) < 2:
        return np.nan, np.nan
    h, pval = stats.kruskal(*groups)
    n = sum(len(g) for g in groups)
    eps2 = (h - len(groups) + 1) / (n - len(groups))
    return pval, max(0.0, eps2)


def chi2(df, col, group="region_en"):
    keep = df.groupby(group)[col].transform("count") >= MIN_N
    t = pd.crosstab(df.loc[keep, group], df.loc[keep, col])
    t = t.loc[:, t.sum() >= 5]
    if t.shape[0] < 2 or t.shape[1] < 2:
        return np.nan, np.nan, t
    c, pval, dof, _ = stats.chi2_contingency(t)
    v = math.sqrt(c / (t.values.sum() * (min(t.shape) - 1)))
    return pval, v, t


def fdr(table):
    ok = table["p"].notna()
    table.loc[ok, "q_fdr"] = multipletests(table.loc[ok, "p"], method="fdr_bh")[1]
    table["significant"] = table["q_fdr"] < ALPHA
    return table


NUMERIC = ["ambitus", "mean_abs_interval", "step_share", "leap_share", "large_leap_share", "descending_share",
           "final_below_mean", "non_pentatonic_share", "n_durations", "duration_entropy", "dotted_share",
           "short_note_share", "n_phrases", "notes_per_phrase", "phrase_repetition", "phrase_ends_on_final"]
ELEMENT = {"ambitus": "melody", "mean_abs_interval": "melody", "step_share": "melody", "leap_share": "melody",
           "large_leap_share": "melody", "descending_share": "melody", "final_below_mean": "melody",
           "non_pentatonic_share": "tonality", "mode": "tonality", "n_durations": "rhythm",
           "duration_entropy": "rhythm", "dotted_share": "rhythm", "short_note_share": "rhythm",
           "meter_class": "rhythm", "meter_changes": "rhythm", "n_phrases": "form", "notes_per_phrase": "form",
           "phrase_repetition": "form", "phrase_ends_on_final": "form"}


def essen_tests(e):
    rows = []
    for col in NUMERIC:
        pval, eff = kruskal(e, col)
        rs, rp = stats.spearmanr(e[col], e["lat"], nan_policy="omit")
        rows.append({"feature": col, "element": ELEMENT[col], "test": "Kruskal-Wallis by region", "p": pval,
                     "effect": eff, "effect_kind": "epsilon2", "spearman_lat": rs, "spearman_lat_p": rp})
    for col in ["mode", "meter_class", "meter_changes"]:
        pval, v, _ = chi2(e, col)
        rows.append({"feature": col, "element": ELEMENT[col], "test": "chi-square by region", "p": pval,
                     "effect": v, "effect_kind": "Cramer V"})
    t = fdr(pd.DataFrame(rows))
    # Same tests inside the Han subset, so the Han/minority split cannot drive the result alone.
    han = e[e["region"].map(lambda r: r in ORDER[:11])]
    t["p_han_only"] = [kruskal(han, c)[0] if c in NUMERIC else chi2(han, c)[0] for c in t["feature"]]
    # The 'shanxi' subset is one collection from one province, so it could stand
    # in for "Northwest Plateau". Re-test inside the mixed 'han' subset only.
    hs = e[e["subset"] == "han"]
    t["p_han_subset_only"] = [kruskal(hs, c)[0] if c in NUMERIC else chi2(hs, c)[0] for c in t["feature"]]
    t["effect_han_subset_only"] = [kruskal(hs, c)[1] if c in NUMERIC else chi2(hs, c)[1] for c in t["feature"]]
    return t


PERF_EN = {"原生态": "traditional (yuanshengtai)", "民族唱法": "national (conservatory) style",
           "field": "field recording", "other": "other", "instrumental": "instrumental"}


def metadata_tests(d):
    d = d[d["core"] == True].copy()  # noqa: E712
    d["performance_type"] = d["performance_type"].map(PERF_EN).fillna(d["performance_type"])
    ff = d["feature_flags"].fillna("")
    d["accompaniment"] = pd.Series(np.nan, index=d.index, dtype=object)
    d.loc[ff.str.contains(r"(?:^|;)accompanied"), "accompaniment"] = "accompanied"
    d.loc[ff.str.contains("unaccompanied"), "accompaniment"] = "unaccompanied"
    d["multiple_singers"] = ff.str.contains("multiple_singers")
    d["upload_year"] = pd.to_numeric(d["upload_date"], errors="coerce") // 10000
    rows = []
    for col, kind in [("performance_type", "c"), ("song_genre", "c"), ("song_class", "c"),
                      ("accompaniment", "c"), ("multiple_singers", "c"), ("duration_s", "n")]:
        if kind == "n":
            pval, eff = kruskal(d, col)
            rows.append({"feature": col, "test": "Kruskal-Wallis by region", "p": pval, "effect": eff,
                         "effect_kind": "epsilon2", "n": int(d[col].notna().sum())})
        else:
            sub = d[d[col].notna() & (d[col].astype(str) != "nan")]
            pval, v, _ = chi2(sub, col)
            rows.append({"feature": col, "test": "chi-square by region", "p": pval, "effect": v,
                         "effect_kind": "Cramer V", "n": int(len(sub))})
    # Over time: composition period (dated songs only) and upload year.
    dated = d[~d["composition_period"].isin(["traditional_undated", "unknown"])]
    for col in ["performance_type", "song_genre"]:
        pval, v, _ = chi2(dated, col, group="composition_period")
        rows.append({"feature": f"{col} by composition period", "test": "chi-square", "p": pval, "effect": v,
                     "effect_kind": "Cramer V", "n": int(len(dated))})
    yr = d[d["composition_year"].notna()]
    rs, rp = stats.spearmanr(yr["composition_year"], yr["duration_s"])
    rows.append({"feature": "duration vs composition year", "test": "Spearman", "p": rp, "effect": rs,
                 "effect_kind": "rho", "n": int(len(yr))})
    up = d[d["upload_year"].notna()]
    rs, rp = stats.spearmanr(up["upload_year"], (up["performance_type"] == PERF_EN["原生态"]).astype(int))
    rows.append({"feature": "share traditional style vs upload year", "test": "Spearman", "p": rp, "effect": rs,
                 "effect_kind": "rho", "n": int(len(up))})
    rs, rp = stats.spearmanr(up["upload_year"], up["duration_s"])
    rows.append({"feature": "duration vs upload year", "test": "Spearman", "p": rp, "effect": rs,
                 "effect_kind": "rho", "n": int(len(up))})
    return fdr(pd.DataFrame(rows)), d, dated


# ------------------------------------------------------------------- figures --
def region_order(df):
    return [EN[r] for r in ORDER if (df["region"] == r).sum() >= MIN_N]


def fig_numeric(e, cols, name, title):
    order = region_order(e)
    fig, axes = plt.subplots(1, len(cols), figsize=(4.2 * len(cols), 0.42 * len(order) + 1.6), sharey=True)
    for ax, col in zip(np.atleast_1d(axes), cols):
        data = [e.loc[e["region_en"] == r, col].dropna() for r in order]
        ax.boxplot(data, vert=False, showfliers=False, widths=0.6)
        ax.set_yticks(range(1, len(order) + 1), [f"{r} (n={len(x)})" for r, x in zip(order, data)])
        ax.set_title(col.replace("_", " "))
        ax.invert_yaxis()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(FIG / f"elements_{name}.png", dpi=130)
    plt.close(fig)


def fig_share(df, col, name, title, group="region_en", order=None):
    t = pd.crosstab(df[group], df[col], normalize="index")
    if order:
        t = t.reindex([o for o in order if o in t.index])
    ax = t.plot(kind="barh", stacked=True, figsize=(9, 0.4 * len(t) + 1.6), colormap="tab20", width=0.8)
    ax.invert_yaxis()
    ax.set_xlabel("share")
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / f"elements_{name}.png", dpi=130)
    plt.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    e = load_essen()
    PER_SONG.parent.mkdir(parents=True, exist_ok=True)
    e.to_csv(PER_SONG, index=False)
    et = essen_tests(e)
    et.to_csv(OUT / "essen_region_tests.csv", index=False)
    med = e.groupby("region_en")[NUMERIC].median().reindex(region_order(e))
    med.insert(0, "n", e.groupby("region_en").size())
    med.to_csv(OUT / "essen_region_medians.csv")
    pd.crosstab(e["region_en"], e["mode"], normalize="index").round(3).to_csv(OUT / "essen_mode_by_region.csv")

    rec = pd.read_csv(REC)
    mt, d, dated = metadata_tests(rec)
    mt.to_csv(OUT / "metadata_tests.csv", index=False)
    order_all = [EN[r] for r in ORDER]
    fig_numeric(e, ["ambitus", "mean_abs_interval", "leap_share"], "melody", "Melody by colour region (Essen scores)")
    fig_numeric(e, ["duration_entropy", "short_note_share", "notes_per_phrase"], "rhythm_form",
                "Rhythm and form by colour region (Essen scores)")
    fig_share(e[e.groupby("region_en")["mode"].transform("count") >= MIN_N], "mode", "mode",
              "Pentatonic mode of the final note, by region (Essen scores)", order=region_order(e))
    fig_share(d, "performance_type", "performance", "Performance type by region (recordings)", order=order_all)
    fig_share(d[d["accompaniment"].notna() & (d["accompaniment"] != "nan")], "accompaniment",
              "accompaniment", "Accompanied vs unaccompanied, by region (recordings with a flag)", order=order_all)
    fig_share(d, "song_genre", "genre", "Song genre by region (recordings)", order=order_all)
    per = ["ming", "qing", "republic", "prc_1949_1965", "prc_1977_1999", "after_2000"]
    fig_share(dated, "song_genre", "genre_by_period", "Song genre by composition period (dated songs)",
              group="composition_period", order=per)

    print(f"Essen songs mapped: {len(e)} | regions with n>={MIN_N}: {len(region_order(e))}")
    print(et[["feature", "element", "p", "q_fdr", "effect", "effect_kind", "significant", "p_han_only",
              "spearman_lat"]].round(4).to_string(index=False))
    print()
    print(mt.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
