"""
Aquarius Phase 4: Gap Analysis

Reads data/unified/master_table.parquet, produces:
- data/unified/gap_report.json
- data/unified/coverage_matrix.csv
- docs/gap_analysis_report.md
- data/figures/ (heatmaps and distribution charts)
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

ROOT = Path(__file__).resolve().parent.parent
UNIFIED = ROOT / "data" / "unified"
FIGURES = ROOT / "data" / "figures"
DOCS = ROOT / "docs"


def load_master():
    return pd.read_parquet(UNIFIED / "master_table.parquet")


def modality_matrix(df: pd.DataFrame) -> pd.DataFrame:
    mods = ["has_audio", "has_midi", "has_musicxml", "has_lyrics",
            "has_score", "has_jianpu", "has_metadata_only"]
    existing = [m for m in mods if m in df.columns]
    grouped = df.groupby("dataset")[existing].sum().astype(int)
    counts = df.groupby("dataset").size().rename("total_items")
    result = grouped.join(counts)
    return result


def metadata_matrix(df: pd.DataFrame) -> pd.DataFrame:
    meta_fields = [
        "title", "artist", "composer", "arranger",
        "province", "region", "country",
        "genre", "folk_song_type", "instrument",
        "key", "mode", "tempo_bpm", "time_signature", "tuning",
        "language", "lyrics_text",
        "emotion_valence", "playing_technique", "singing_technique",
        "chord_labels", "beat_annotations",
        "role_type", "shengqiang",
    ]
    existing = [f for f in meta_fields if f in df.columns]
    result = {}
    for ds, group in df.groupby("dataset"):
        row = {"total_items": len(group)}
        for field in existing:
            non_null = group[field].notna().sum()
            non_empty = 0
            for v in group[field].dropna():
                if isinstance(v, str) and v.strip() in ("", "nan", "None"):
                    continue
                if isinstance(v, bool) and not v:
                    continue
                non_empty += 1
            row[field] = non_empty
        result[ds] = row
    return pd.DataFrame(result).T


def build_gap_report(df: pd.DataFrame) -> dict:
    datasets = sorted(df["dataset"].unique().tolist())
    total = len(df)

    modality_gaps = {}
    for mod in ["has_audio", "has_midi", "has_musicxml", "has_lyrics"]:
        if mod in df.columns:
            count = int(df[mod].sum())
            modality_gaps[mod] = {
                "present": count,
                "missing": total - count,
                "coverage_pct": round(count / total * 100, 1),
                "datasets_with": sorted(df[df[mod] == True]["dataset"].unique().tolist()),
            }

    meta_gaps = {}
    critical_fields = ["title", "artist", "genre", "instrument", "key",
                       "province", "language", "tempo_bpm"]
    for field in critical_fields:
        if field not in df.columns:
            continue
        non_null = df[field].notna()
        non_empty = non_null & ~df[field].astype(str).isin(["", "nan", "None"])
        count = int(non_empty.sum())
        meta_gaps[field] = {
            "present": count,
            "missing": total - count,
            "coverage_pct": round(count / total * 100, 1),
            "datasets_with": sorted(df[non_empty]["dataset"].unique().tolist()),
        }

    priorities = []

    if meta_gaps.get("key", {}).get("coverage_pct", 0) < 50:
        priorities.append({
            "field": "key/mode",
            "impact": "high",
            "method": "computational inference from MIDI/audio pitch content",
            "confidence": "medium",
            "coverage_now": meta_gaps.get("key", {}).get("coverage_pct", 0),
        })

    if meta_gaps.get("genre", {}).get("coverage_pct", 0) < 50:
        priorities.append({
            "field": "genre",
            "impact": "high",
            "method": "infer from dataset source + title keywords + instrument",
            "confidence": "medium-high",
            "coverage_now": meta_gaps.get("genre", {}).get("coverage_pct", 0),
        })

    if meta_gaps.get("province", {}).get("coverage_pct", 0) < 50:
        priorities.append({
            "field": "province/region",
            "impact": "medium",
            "method": "infer from dataset metadata, title analysis, instrument origin",
            "confidence": "low-medium",
            "coverage_now": meta_gaps.get("province", {}).get("coverage_pct", 0),
        })

    priorities.append({
        "field": "Chinese pentatonic mode",
        "impact": "critical",
        "method": "pitch-class analysis of MIDI/MusicXML content",
        "confidence": "medium",
        "coverage_now": 0,
        "note": "No dataset provides ground-truth mode labels",
    })

    priorities.append({
        "field": "temporal/year",
        "impact": "medium",
        "method": "artist lookup, genre-era mapping, publication dates",
        "confidence": "low",
        "coverage_now": 0,
    })

    return {
        "summary": {
            "total_items": total,
            "total_datasets": len(datasets),
            "datasets": datasets,
        },
        "modality_gaps": modality_gaps,
        "metadata_gaps": meta_gaps,
        "priority_fills": priorities,
    }


def write_gap_report_md(report: dict, mod_matrix: pd.DataFrame, meta_matrix: pd.DataFrame):
    lines = ["# Gap Analysis Report\n"]

    lines.append(f"## Summary\n")
    lines.append(f"- **Total items**: {report['summary']['total_items']:,}")
    lines.append(f"- **Total datasets**: {report['summary']['total_datasets']}")
    lines.append(f"- **Datasets**: {', '.join(report['summary']['datasets'])}\n")

    lines.append("## Modality Coverage\n")
    lines.append("| Modality | Present | Missing | Coverage |")
    lines.append("|----------|---------|---------|----------|")
    for mod, info in report["modality_gaps"].items():
        label = mod.replace("has_", "")
        lines.append(f"| {label} | {info['present']:,} | {info['missing']:,} | {info['coverage_pct']}% |")
    lines.append("")

    lines.append("## Modality × Dataset Matrix\n")
    lines.append(mod_matrix.to_markdown())
    lines.append("")

    lines.append("## Critical Metadata Gaps\n")
    lines.append("| Field | Present | Missing | Coverage | Datasets |")
    lines.append("|-------|---------|---------|----------|----------|")
    for field, info in report["metadata_gaps"].items():
        ds = ", ".join(info["datasets_with"][:5])
        if len(info["datasets_with"]) > 5:
            ds += f" (+{len(info['datasets_with'])-5})"
        lines.append(f"| {field} | {info['present']:,} | {info['missing']:,} | {info['coverage_pct']}% | {ds} |")
    lines.append("")

    lines.append("## Priority Gap-Filling Actions\n")
    for i, p in enumerate(report["priority_fills"], 1):
        lines.append(f"### {i}. {p['field']}")
        lines.append(f"- **Impact**: {p['impact']}")
        lines.append(f"- **Current coverage**: {p['coverage_now']}%")
        lines.append(f"- **Method**: {p['method']}")
        lines.append(f"- **Confidence**: {p['confidence']}")
        if "note" in p:
            lines.append(f"- **Note**: {p['note']}")
        lines.append("")

    lines.append("## Key Observations\n")
    lines.append("1. **Metadata-only dominance**: ~75% of items are metadata-only (MGD catalog), skewing coverage stats. Audio coverage among audio-bearing datasets is much higher.\n")
    lines.append("2. **Chinese mode labels**: Zero datasets provide ground-truth pentatonic mode (gong/shang/jue/zhi/yu). This is the single most important gap for a Chinese music database.\n")
    lines.append("3. **Temporal metadata absent**: No dataset provides year/era. Must be inferred from artist, genre, and publication context.\n")
    lines.append("4. **Composer attribution rare**: Only Guqin dataset has arranger/transcriber info. Most datasets track performer but not creator.\n")
    lines.append("5. **Geographic coverage biased**: Folk music well-covered (31 provinces via MGD, 10 via Anthology). Other genres lack regional labels entirely.\n")
    lines.append("6. **Emotion labels Western-only**: PMEmo has emotion annotations but on Western pop music. No Chinese-music emotion dataset exists.\n")

    with open(DOCS / "gap_analysis_report.md", "w") as f:
        f.write("\n".join(lines))


def plot_figures(df: pd.DataFrame, mod_matrix: pd.DataFrame, meta_matrix: pd.DataFrame):
    if not HAS_MPL:
        print("matplotlib not available, skipping figures")
        return

    FIGURES.mkdir(parents=True, exist_ok=True)

    # 1. Modality heatmap
    mod_cols = [c for c in mod_matrix.columns if c.startswith("has_")]
    if mod_cols:
        counts = mod_matrix[mod_cols].copy()
        totals = mod_matrix["total_items"]
        pcts = counts.div(totals, axis=0) * 100
        pcts.columns = [c.replace("has_", "") for c in pcts.columns]

        fig, ax = plt.subplots(figsize=(10, max(6, len(pcts) * 0.5)))
        im = ax.imshow(pcts.values, cmap="YlGn", aspect="auto", vmin=0, vmax=100)
        ax.set_xticks(range(len(pcts.columns)))
        ax.set_xticklabels(pcts.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(pcts.index)))
        ax.set_yticklabels(pcts.index, fontsize=8)
        for i in range(len(pcts.index)):
            for j in range(len(pcts.columns)):
                v = pcts.values[i, j]
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if v > 60 else "black")
        plt.colorbar(im, label="Coverage %")
        ax.set_title("Modality Coverage by Dataset")
        plt.tight_layout()
        plt.savefig(FIGURES / "modality_heatmap.png", dpi=150)
        plt.close()
        print(f"  Saved modality_heatmap.png")

    # 2. Metadata heatmap
    meta_cols = [c for c in meta_matrix.columns if c != "total_items"]
    if meta_cols:
        counts = meta_matrix[meta_cols].copy()
        totals = meta_matrix["total_items"]
        pcts = counts.div(totals, axis=0) * 100
        pcts = pcts.fillna(0)

        fig, ax = plt.subplots(figsize=(14, max(6, len(pcts) * 0.5)))
        im = ax.imshow(pcts.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
        ax.set_xticks(range(len(pcts.columns)))
        ax.set_xticklabels(pcts.columns, rotation=45, ha="right", fontsize=7)
        ax.set_yticks(range(len(pcts.index)))
        ax.set_yticklabels(pcts.index, fontsize=8)
        for i in range(len(pcts.index)):
            for j in range(len(pcts.columns)):
                v = pcts.values[i, j]
                if v > 0:
                    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                            color="white" if v > 60 else "black")
        plt.colorbar(im, label="Coverage %")
        ax.set_title("Metadata Coverage by Dataset")
        plt.tight_layout()
        plt.savefig(FIGURES / "metadata_heatmap.png", dpi=150)
        plt.close()
        print(f"  Saved metadata_heatmap.png")

    # 3. Dataset size distribution
    ds_counts = df["dataset"].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(ds_counts)), ds_counts.values, color="#4a90d9")
    ax.set_yticks(range(len(ds_counts)))
    ax.set_yticklabels(ds_counts.index, fontsize=8)
    ax.set_xlabel("Number of items")
    ax.set_title("Items per Dataset")
    for i, v in enumerate(ds_counts.values):
        ax.text(v + max(ds_counts) * 0.01, i, f"{v:,}", va="center", fontsize=7)
    plt.tight_layout()
    plt.savefig(FIGURES / "dataset_sizes.png", dpi=150)
    plt.close()
    print(f"  Saved dataset_sizes.png")

    # 4. Genre distribution
    if "genre" in df.columns:
        genres = df["genre"].dropna()
        genres = genres[~genres.isin(["", "nan", "None"])]
        if len(genres) > 0:
            gc = genres.value_counts().head(15)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.barh(range(len(gc)), gc.values, color="#e8734a")
            ax.set_yticks(range(len(gc)))
            ax.set_yticklabels(gc.index, fontsize=8)
            ax.set_xlabel("Count")
            ax.set_title("Genre Distribution (top 15)")
            plt.tight_layout()
            plt.savefig(FIGURES / "genre_distribution.png", dpi=150)
            plt.close()
            print(f"  Saved genre_distribution.png")


def main():
    print("Loading master table...")
    df = load_master()
    print(f"  {len(df)} items from {df['dataset'].nunique()} datasets\n")

    print("Building modality matrix...")
    mod_matrix = modality_matrix(df)
    mod_matrix.to_csv(UNIFIED / "coverage_matrix.csv")
    print(f"  Saved coverage_matrix.csv\n")

    print("Building metadata matrix...")
    meta_matrix = metadata_matrix(df)
    meta_matrix.to_csv(UNIFIED / "metadata_coverage.csv")
    print(f"  Saved metadata_coverage.csv\n")

    print("Building gap report...")
    report = build_gap_report(df)
    with open(UNIFIED / "gap_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved gap_report.json\n")

    print("Writing gap analysis report...")
    write_gap_report_md(report, mod_matrix, meta_matrix)
    print(f"  Saved docs/gap_analysis_report.md\n")

    print("Generating figures...")
    plot_figures(df, mod_matrix, meta_matrix)

    print("\nDone.")


if __name__ == "__main__":
    main()
