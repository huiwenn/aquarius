"""Inspect the Jingju Pitch Contour Segmentation dataset (SMC2016)."""

import os
from collections import Counter

BASE = "/Users/sophiasun/Desktop/2cool4school/2026/aquarius/data/raw/jingju_pitch_contour/SMC2016-master"
GT_DIR = os.path.join(BASE, "dataset", "groundtruth")
SCORES_DIR = os.path.join(BASE, "dataset", "scores")


def count_recordings():
    """Count unique recordings by looking at pitchtrack files."""
    pitchtrack_files = [
        f for f in os.listdir(GT_DIR) if f.endswith("_pitchtrack.csv")
    ]
    recordings = sorted(f.replace("_pitchtrack.csv", "") for f in pitchtrack_files)
    return recordings


def count_annotation_types():
    """Count annotation types available."""
    all_csv = [f for f in os.listdir(GT_DIR) if f.endswith(".csv")]
    # Extract annotation type (last part after final underscore before .csv)
    types = Counter()
    for f in all_csv:
        # Handle files like name_monoNoteOut_midi.csv
        if "_monoNoteOut_midi.csv" in f:
            types["monoNoteOut_midi"] += 1
        elif "_monoNoteOut.csv" in f:
            types["monoNoteOut"] += 1
        elif "_pitchtrack.csv" in f:
            types["pitchtrack"] += 1
        elif "_melodicTrans.csv" in f:
            types["melodicTrans"] += 1
        elif "_coarseSeg.csv" in f:
            types["coarseSeg"] += 1
        elif "_refinedSeg.csv" in f:
            types["refinedSeg"] += 1
    return types


def count_scores():
    """Count MusicXML score files."""
    xml_files = [f for f in os.listdir(SCORES_DIR) if f.endswith(".xml")]
    return len(xml_files)


def categorize_recordings(recordings):
    """Categorize recordings by source/type."""
    categories = Counter()
    for r in recordings:
        if r.startswith("bcnRecording"):
            categories["bcnRecording"] += 1
        elif r.startswith("londonRecording_Dan"):
            categories["londonRecording_Dan"] += 1
        elif r.startswith("londonRecording_Laosheng"):
            categories["londonRecording_Laosheng"] += 1
        elif r.startswith("fem_"):
            categories["fem (female)"] += 1
        elif r.startswith("male_"):
            categories["male"] += 1
    return categories


if __name__ == "__main__":
    recordings = count_recordings()
    print(f"=== Recordings: {len(recordings)} ===")

    categories = categorize_recordings(recordings)
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print(f"\n=== Annotation Types ===")
    ann_types = count_annotation_types()
    for t, count in sorted(ann_types.items()):
        print(f"  {t}: {count} files")

    print(f"\n=== MusicXML Scores: {count_scores()} ===")

    print(f"\n=== Total size ===")
    total = sum(
        os.path.getsize(os.path.join(GT_DIR, f))
        for f in os.listdir(GT_DIR)
        if f.endswith(".csv")
    )
    print(f"  Groundtruth CSVs: {total / 1024 / 1024:.1f} MB")
