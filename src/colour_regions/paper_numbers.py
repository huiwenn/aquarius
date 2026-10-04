"""
Write every corpus number and data table used in the paper, so the text never holds a hand-copied number.

Inputs : data/colour_regions/recordings.csv, scores.csv (build_release.py), data/transcription/benchmark_results.csv
Outputs: ../colour_regions_paper/generated/numbers.tex          \\newcommand macros (\\NRecTotal, ...)
         ../colour_regions_paper/generated/table_regions.tex    Table: regions, counts, channels, tiers
         ../colour_regions_paper/generated/table_benchmark.tex  Table: transcription benchmark
Run (py312): python src/colour_regions/paper_numbers.py
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from colour_regions.regions import REGIONS  # noqa: E402

D = ROOT / "data" / "colour_regions"
GEN = ROOT.parent / "colour_regions_paper" / "generated"


def fmt(x) -> str:
    return f"{x:,}".replace(",", "{,}") if isinstance(x, int) else str(x)


STRONG = ["A1", "A2", "A", "B"]
PENDING = ["LinkDate", "NLinkAlive", "NLinkChecked", "PctLinkAlive", "PctLinkAliveYT", "PctLinkAliveBili"]  # tiers with an attested singer or place


def traced_round1(r1: pd.DataFrame) -> int:
    """Round-1 identifiers that occur in a logged search result (data/regions_curated/search_log.jsonl)."""
    import json
    ids = set()
    for line in open(ROOT / "data" / "regions_curated" / "search_log.jsonl"):
        try:
            hits = json.loads(line).get("hits") or []
        except json.JSONDecodeError:
            continue
        ids |= {h.get("video_id") for h in hits if isinstance(h, dict)}
    return int(r1.item_id.isin(ids).sum())


def numbers(rec: pd.DataFrame, sc: pd.DataFrame) -> dict:
    sm = pd.read_csv(D / "score_matches.csv")
    per = rec.groupby("region").size()
    r1, r2 = rec[rec["round"] == 1], rec[rec["round"] == 2]
    tier = rec.provenance_tier
    n = {
        "NRecTotal": len(rec), "NRecVone": len(r1), "NRecVtwo": len(r2),
        "NRecPerRegionMin": int(per.min()), "NRecPerRegionMax": int(per.max()),
        "NHoursTotal": f"{rec.duration_s.sum() / 3600:.1f}",
        "NHoursVone": f"{r1.duration_s.sum() / 3600:.1f}", "NHoursVtwo": f"{r2.duration_s.sum() / 3600:.1f}",
        "NChannels": rec.channel_key.nunique(),
        "NRecVtwoBili": int((r2.platform == "bilibili").sum()), "NRecVtwoYT": int((r2.platform == "youtube").sum()),
        "NRecVtwoEur": int((r2.platform == "europeana").sum()),
        "NRecVtwoGan": int((r2.region == "赣").sum()),
        "NTierA": int(tier.isin(["A1", "A2", "A"]).sum()), "NTierAOne": int((tier == "A1").sum()),
        "NTierATwo": int((tier == "A2").sum()), "NTierB": int((tier == "B").sum()), "NTierC": int((tier == "C").sum()),
        "NUpgradedAOne": int(((tier == "A1") & (rec.provenance_tier_curator != "A")).sum()),
        "NTierUnknown": int(tier.isna().sum()),
        "PctTierAB": f"{100 * tier.isin(STRONG).mean():.0f}",
        "NSongs": rec.song_key.nunique(),
        "NAnthology": int((sc.source == "anthology").sum()), "NEssen": int((sc.source == "essen").sum()),
        "NScores": len(sc),
        "NAnthologyRegions": sc[sc.source == "anthology"].region.nunique(),
        "NCore": int(rec.core.sum()), "NNotCore": int((~rec.core).sum()),
        "NExclLabel": int(rec.core_exclusion.fillna("").str.contains("label").sum()),
        "NExclArrangement": int(rec.core_exclusion.fillna("").str.contains("arrangement").sum()),
        "NExclComposed": int(rec.core_exclusion.fillna("").str.contains("composed").sum()),
        "NExclSpeech": int(rec.core_exclusion.fillna("").str.contains("speech").sum()),
        "NSpeechHigh": int((rec.speech_share >= 0.3).sum()),
        "NSpeechHighDoc": int(((rec.speech_share >= 0.3) & rec.speech_doc_meta).sum()),
        "PctSpeechHighVone": f"{100 * (r1.speech_share >= 0.3).mean():.0f}",
        "PctSpeechHighVtwo": f"{100 * (r2.speech_share >= 0.3).mean():.0f}",
        "NLabelConcern": int(rec.label_status.notna().sum()),
        "NLabelExclude": int((rec.label_status == "exclude").sum()),
        # curator tiers (before the national-list check) for the comparison of the two rounds
        "NTierAVone": int((r1.provenance_tier_curator == "A").sum()),
        "NTierBVone": int((r1.provenance_tier_curator == "B").sum()),
        "NTierAVtwo": int((r2.provenance_tier_curator == "A").sum()),
        "NTierBVtwo": int((r2.provenance_tier_curator == "B").sum()),
        "PctTierABVone": f"{100 * r1.provenance_tier_curator.isin(['A', 'B']).mean():.0f}",
        "PctTierABVtwo": f"{100 * r2.provenance_tier_curator.isin(['A', 'B']).mean():.0f}",
        "NComposedVone": int((r1.dating_flag == "composed").sum()),
        "NCheckVone": int((r1.dating_flag == "check").sum()),
        "NEthnic": int(rec.ethnic_group.dropna().str.split("/").explode().nunique()),
        "NRecVoneTraced": traced_round1(r1),
        "NScoreMatchRec": int(sm.recording_id.nunique()),
        "NScoreMatchRegion": int(sm[sm.same_region].recording_id.nunique()),
        "NScoreMatchProv": int(sm[sm.same_province].recording_id.nunique()),
        "NSingerIds": int(rec.singer_id.nunique()), "NSingerNamed": int(rec.singer_id.notna().sum()),
        "NSingerNamesReleased": int(rec.singer.notna().sum()),
        "NGroups": int(rec.group_id.nunique()), "NLargestGroup": int(rec.group_id.value_counts().iloc[0]),
        "NGeoCounty": int((rec.geo_level == "county").sum()), "NGeoPref": int((rec.geo_level == "prefecture").sum()),
        "NGeoProv": int((rec.geo_level == "province").sum()), "NGeoNone": int((rec.geo_level == "none").sum()),
        "NHan": int((rec.region_type == "Han").sum()), "NMinority": int((rec.region_type == "minority").sum()),
        "NEssenRegions": sc[sc.source == "essen"].region.nunique(),
    }
    ls = D / "link_status.csv"
    if ls.exists():
        l = pd.read_csv(ls)
        l = l[l.checked_on == l.checked_on.max()]
        n.update({"LinkDate": l.checked_on.iloc[0], "NLinkAlive": int(l.available.sum()), "NLinkChecked": len(l),
                  "PctLinkAlive": f"{100 * l.available.mean():.1f}",
                  "PctLinkAliveYT": f"{100 * l[l.platform == 'youtube'].available.mean():.1f}",
                  "PctLinkAliveBili": f"{100 * l[l.platform == 'bilibili'].available.mean():.1f}"})
    b = pd.read_csv(ROOT / "data" / "transcription" / "benchmark_results.csv").set_index(["model", "subset"])
    g = lambda m, sub, col="COnP": f"{b.loc[(m, sub), col]:.3f}"
    n.update({
        "BmHumanVoc": g("human_A2", "vocadito"), "BmGameVoc": g("game_seg0.1", "vocadito"),
        "BmSomeVoc": g("some", "vocadito"), "BmRosvotVoc": g("rosvot", "vocadito"),
        "BmRosvotMfour": g("rosvot", "m4singer"), "BmRosvotGts": g("rosvot", "gtsinger"),
        "BmSepHtdemucs": g("game_seg0.1@sep_htdemucs", "vocadito"), "BmSepRoformer": g("game_seg0.1@sep", "vocadito"),
        "BmPPVoc": g("game_pp@sep_htdemucs", "vocadito"), "BmEnsVoc": g("game_ens3_pp@sep_htdemucs", "vocadito"),
        "BmPPVocOff": g("game_pp@sep_htdemucs", "vocadito", "COnPOff"),
        "BmEnsVocOff": g("game_ens3_pp@sep_htdemucs", "vocadito", "COnPOff"),
        "BmSepVocOff": g("game_seg0.1@sep_htdemucs", "vocadito", "COnPOff"),
    })
    return n


def table_regions(rec: pd.DataFrame, sc: pd.DataFrame) -> str:
    lines = [r"\begin{table*}[t]", r"\centering", r"\footnotesize", r"\setlength{\tabcolsep}{3.5pt}",
             r"\begin{tabular}{llp{3.4cm}rrrrrrl}", r"\hline",
             r"\colhead{Region} & \colhead{Chinese} & \colhead{Main provinces / areas} & \colhead{Rec.} & "
             r"\colhead{Core} & \colhead{Hours} & \colhead{Chan.} & \colhead{A/B} & \colhead{Field} & "
             r"\colhead{Scores}\\",
             r"\hline"]
    field = ["原生态", "field"]
    for i, (code, zh, en, typ, areas) in enumerate(REGIONS):
        if i == 11:
            lines.append(r"\hline")
        r = rec[rec.region == zh]
        s = sc[sc.region == zh]
        na, ne = int((s.source == "anthology").sum()), int((s.source == "essen").sum())
        scores = (f"{fmt(na)} A + {fmt(ne)} E" if na and ne else f"{fmt(na)} A" if na else f"{fmt(ne)} E" if ne else "--")
        lines.append(f"{en.replace('–', '--')} & \\zh{{{zh}}} & {areas.replace('–', '--')} & {len(r)} & "
                     f"{int(r.core.sum())} & {r.duration_s.sum() / 3600:.1f} & {r.channel_key.nunique()} & "
                     f"{100 * r.provenance_tier.isin(STRONG).mean():.0f}\\% & "
                     f"{100 * r.performance_type.isin(field).mean():.0f}\\% & {scores}\\\\")
    lines += [r"\hline",
              f"Total & & & {fmt(len(rec))} & {fmt(int(rec.core.sum()))} & {rec.duration_s.sum() / 3600:.1f} & "
              f"{rec.channel_key.nunique()} & {100 * rec.provenance_tier.isin(STRONG).mean():.0f}\\% & "
              f"{100 * rec.performance_type.isin(field).mean():.0f}\\% & {fmt(len(sc))}\\\\",
              r"\hline", r"\end{tabular}",
              r"\caption{The 15 colour regions: 11 Han regions (top) and 4 minority regions (bottom). "
              r"Rec.: recordings (both rounds); Core: recordings in the core subset (Section~\ref{sec:harmonise}); "
              r"Chan.: distinct channels; A/B: share with an attested singer or place (Section~\ref{sec:tiers}); "
              r"Field: share of tradition-bearer or field performances; Scores: Anthology (A) and Essen (E). "
              r"The Anthology's Jiang--Han scores are from Henan only.}",
              r"\label{tab:regions}", r"\end{table*}"]
    return "\n".join(lines) + "\n"


def table_benchmark() -> str:
    b = pd.read_csv(ROOT / "data" / "transcription" / "benchmark_results.csv").set_index(["model", "subset"])
    rows = [("Human annotator A2 (ceiling)", "human_A2"), ("GAME (medium)", "game_seg0.1"), ("SOME", "some"),
            ("Basic Pitch", "basic_pitch"), ("YourMT3+ (MoE)", "yourmt3_ps"), ("ROSVOT", "rosvot"),
            ("VocalParse", "vocalparse"),
            (r"\textit{Mix} $\rightarrow$ htdemucs $\rightarrow$ GAME", "game_seg0.1@sep_htdemucs"),
            (r"\quad + offset trim", "game_pp@sep_htdemucs"),
            (r"\quad + 3-run ensemble (ours)", "game_ens3_pp@sep_htdemucs")]
    lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\begin{tabular}{lrrrr}", r"\hline",
             r" & \multicolumn{2}{c}{\colhead{vocadito}} & \colhead{M4S.} & \colhead{GTS.}\\",
             r"\colhead{Model} & \colhead{COnP} & \colhead{COnPOff} & \colhead{COnP} & \colhead{COnP}\\", r"\hline"]
    for i, (name, key) in enumerate(rows):
        if i == 7:
            lines.append(r"\hline")
        v = b.loc[(key, "vocadito")]
        g = lambda s: f"{b.loc[(key, s), 'COnP']:.2f}" if (key, s) in b.index and key != "human_A2" else "--"
        lines.append(f"{name} & {v.COnP:.3f} & {v.COnPOff:.3f} & {g('m4singer')} & {g('gtsinger')}\\\\")
    lines += [r"\hline", r"\end{tabular}",
              r"\caption{Note transcription benchmark (note F1, \texttt{mir\_eval}). COnP: onset $\pm$50\,ms and "
              r"pitch $\pm$50 cents; COnPOff: also offset. vocadito is not in the published training data of any tested model. "
              r"Upper part: clean voice input. Lower part: our pipeline on voice mixed with instrumental "
              r"accompaniment at +3\,dB. All values are on all clips; the offset trim was chosen by two-fold "
              r"cross-validation, with held-out COnPOff 0.357.}",
              r"\label{tab:benchmark}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    rec = pd.read_csv(D / "recordings.csv")
    sc = pd.read_csv(D / "scores.csv")
    n = numbers(rec, sc)
    for k in PENDING:  # results that are still being computed show as a red "??" in the paper
        n.setdefault(k, r"\textcolor{red}{??}")
    (GEN / "numbers.tex").write_text("% generated by aquarius/src/colour_regions/paper_numbers.py — do not edit\n"
                                     + "".join(f"\\newcommand{{\\{k}}}{{{fmt(v)}}}\n" for k, v in n.items()))
    (GEN / "table_regions.tex").write_text(table_regions(rec, sc))
    (GEN / "table_benchmark.tex").write_text(table_benchmark())
    supplementary_tables()
    for k, v in n.items():
        print(f"{k:22s} {v}")



def supplementary_tables() -> None:
    """Tables for ../colour_regions_paper/supplementary.tex: score-to-region mapping and label-review decisions."""
    sc = pd.read_csv(D / "scores.csv")
    m = sc.groupby(["source", "volume", "province", "region_en"]).size().reset_index(name="n")
    m = m[(m.source == "anthology") | (m.n >= 10)]
    lines = [r"\begin{longtable}{llllr}", r"\toprule Source & Volume / subset & Province or group & Region & Scores\\",
             r"\midrule"]
    lines += [f"{r.source} & {r.volume} & {r.province if isinstance(r.province, str) else '(ethnic group)'} & "
              f"{r.region_en.replace('–', '--')} & {r.n}\\\\" for r in m.itertuples()]
    lines += [r"\bottomrule", r"\caption{Mapping of score volumes (Anthology) and Essen province or ethnic-group "
              r"keywords to colour regions (Essen rows with fewer than 10 songs omitted).}\label{tab:s-mapping}",
              r"\end{longtable}"]
    (GEN / "supp_mapping.tex").write_text("\n".join(lines) + "\n")
    cur = ROOT / "data" / "regions_curated"
    lab = pd.read_csv(cur / "v1_label_review.csv")
    con = pd.read_csv(cur / "v1_content_review.csv")
    rows = [(r.video_id, r.label_status, r.review_reason if r.label_status == "exclude" else r.label_concern)
            for r in lab.itertuples()] + [(r.video_id, "exclude (arrangement)", r.review_reason)
                                          for r in con.itertuples()]
    esc = lambda t: str(t).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    lines = [r"\begin{longtable}{llp{9cm}}", r"\toprule Item & Decision & Reason\\", r"\midrule"]
    lines += [f"\\texttt{{{esc(v)}}} & {esc(d)} & {esc(w)}\\\\" for v, d, w in rows]
    lines += [r"\bottomrule", r"\caption{Review decisions for flagged Round~1 recordings.}\label{tab:s-review}",
              r"\end{longtable}"]
    (GEN / "supp_review.tex").write_text("\n".join(lines) + "\n")



if __name__ == "__main__":
    main()
