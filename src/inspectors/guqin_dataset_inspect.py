#!/usr/bin/env python3
"""
Inspect the Guqin Dataset.

Walks the directory tree, counts and characterizes all file types,
parses MusicXML files for musical content analysis, and extracts
metadata from reference.csv.

Usage:
    python src/inspectors/guqin_dataset_inspect.py [--data-dir DIR]
"""

import argparse
import csv
import os
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_DATA_DIR = "data/raw/guqin_dataset"


def walk_tree(data_dir: Path) -> dict:
    """Walk directory tree and count files by extension."""
    ext_counts = Counter()
    all_files = []
    for root, dirs, files in os.walk(data_dir):
        # Skip .git
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower() or "(no extension)"
            ext_counts[ext] += 1
            all_files.append(fp)
    return {"ext_counts": ext_counts, "all_files": all_files}


def analyze_metadata(csv_path: Path) -> dict:
    """Parse reference.csv and extract taxonomy information."""
    pieces = []
    tuning_counts = Counter()
    source_counts = Counter()  # 琴谱来源 (score source collection)
    origin_counts = Counter()  # 琴曲来源 (original historical source)
    performer_counts = Counter()
    arranger_counts = Counter()

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pieces.append(row)
            title = row.get("曲谱名称", "").strip()
            source = row.get("琴谱来源", "").strip()
            tuning = row.get("定弦", "").strip()
            origin = row.get("琴曲来源", "").strip()
            performer = row.get("演奏者", "").strip()
            arranger = row.get("打谱/记谱者", "").strip()

            if tuning:
                tuning_counts[tuning] += 1
            if source:
                source_counts[source] += 1
            if origin:
                origin_counts[origin] += 1
            if performer:
                performer_counts[performer] += 1
            if arranger:
                arranger_counts[arranger] += 1

    return {
        "pieces": pieces,
        "n_pieces": len(pieces),
        "tuning_counts": tuning_counts,
        "source_counts": source_counts,
        "origin_counts": origin_counts,
        "performer_counts": performer_counts,
        "arranger_counts": arranger_counts,
    }


def analyze_musicxml_files(xml_dir: Path) -> dict:
    """Parse MusicXML files for musical content statistics."""
    time_sig_counts = Counter()
    pitch_counts = Counter()
    total_notes = 0
    total_harmonics = 0
    measure_counts = []
    note_counts_per_file = []

    xml_files = sorted(xml_dir.rglob("*.xml"))

    for fp in xml_files:
        try:
            tree = ET.parse(fp)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # Measures
        measures = root.findall(".//measure")
        n_measures = len(measures)
        measure_counts.append((fp.stem, n_measures))

        # Time signatures
        for ts in root.findall(".//time"):
            beats = ts.findtext("beats", "")
            beat_type = ts.findtext("beat-type", "")
            if beats and beat_type:
                time_sig_counts[f"{beats}/{beat_type}"] += 1

        # Notes
        notes = root.findall(".//note")
        n_notes = len(notes)
        note_counts_per_file.append((fp.stem, n_notes))
        total_notes += n_notes

        for note in notes:
            pitch_el = note.find("pitch")
            if pitch_el is not None:
                step = pitch_el.findtext("step", "")
                octave = pitch_el.findtext("octave", "")
                if step and octave:
                    pitch_counts[f"{step}{octave}"] += 1

            # Harmonics marked as staccato
            if note.find(".//staccato") is not None:
                total_harmonics += 1

    return {
        "n_files": len(xml_files),
        "time_sig_counts": time_sig_counts,
        "pitch_counts": pitch_counts,
        "total_notes": total_notes,
        "total_harmonics": total_harmonics,
        "measure_counts": measure_counts,
        "note_counts_per_file": note_counts_per_file,
    }


def analyze_phrase_split(xml_dir: Path) -> dict:
    """Analyze the phrase-split XML directory structure."""
    xml_files = sorted(xml_dir.rglob("*.xml"))
    pieces = defaultdict(list)

    for fp in xml_files:
        name = fp.stem
        parts = name.rsplit("_", 1)
        if len(parts) == 2:
            try:
                phrase_num = int(parts[1])
                pieces[parts[0]].append(phrase_num)
            except ValueError:
                pieces[name].append(0)
        else:
            pieces[name].append(0)

    return {
        "n_files": len(xml_files),
        "n_pieces": len(pieces),
        "phrases_per_piece": {
            k: sorted(v) for k, v in sorted(pieces.items())
        },
    }


def print_report(tree_info, meta, full_xml, phrase_xml):
    """Print a comprehensive inspection report."""
    print("=" * 60)
    print("GUQIN DATASET INSPECTION REPORT")
    print("=" * 60)

    print("\n--- FILE TYPE SUMMARY ---")
    for ext, count in tree_info["ext_counts"].most_common():
        print(f"  {ext}: {count}")

    print(f"\n--- METADATA (reference.csv) ---")
    print(f"  Total pieces: {meta['n_pieces']}")

    print(f"\n  Tunings (定弦):")
    for tuning, count in meta["tuning_counts"].most_common():
        print(f"    {tuning}: {count}")

    print(f"\n  Score source collections (琴谱来源):")
    for source, count in meta["source_counts"].most_common():
        print(f"    {source}: {count}")

    print(f"\n  Original historical sources (琴曲来源), top 10:")
    for origin, count in meta["origin_counts"].most_common(10):
        print(f"    {origin}: {count}")

    print(f"\n  Performers (演奏者), top 10:")
    for performer, count in meta["performer_counts"].most_common(10):
        print(f"    {performer}: {count}")

    print(f"\n  Arrangers/transcribers (打谱/记谱者), top 10:")
    for arranger, count in meta["arranger_counts"].most_common(10):
        print(f"    {arranger}: {count}")

    print(f"\n--- FULL-PIECE MUSICXML ANALYSIS (xml_no_split) ---")
    print(f"  Files: {full_xml['n_files']}")
    print(f"  Total notes: {full_xml['total_notes']}")
    print(f"  Harmonic notes (staccato): {full_xml['total_harmonics']}")

    print(f"\n  Time signatures:")
    for ts, count in full_xml["time_sig_counts"].most_common(10):
        print(f"    {ts}: {count}")

    print(f"\n  Pitch distribution (top 15):")
    for pitch, count in full_xml["pitch_counts"].most_common(15):
        print(f"    {pitch}: {count}")

    if full_xml["measure_counts"]:
        measures = [m[1] for m in full_xml["measure_counts"]]
        print(f"\n  Measures per piece: min={min(measures)}, "
              f"max={max(measures)}, mean={sum(measures)/len(measures):.1f}, "
              f"total={sum(measures)}")

    print(f"\n--- PHRASE-SPLIT ANALYSIS (xml) ---")
    print(f"  Total phrase files: {phrase_xml['n_files']}")
    print(f"  Unique pieces: {phrase_xml['n_pieces']}")
    phrases = phrase_xml["phrases_per_piece"]
    phrase_lens = [len(v) for v in phrases.values()]
    if phrase_lens:
        print(f"  Phrases per piece: min={min(phrase_lens)}, "
              f"max={max(phrase_lens)}, "
              f"mean={sum(phrase_lens)/len(phrase_lens):.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the Guqin Dataset."
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"Data directory (default: {DEFAULT_DATA_DIR})",
    )
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        print(f"Error: {data_dir} does not exist.")
        return

    v1_dir = data_dir / "Guqin_Dataset_v1"

    tree_info = walk_tree(data_dir)
    meta = analyze_metadata(v1_dir / "reference.csv")
    full_xml = analyze_musicxml_files(v1_dir / "xml_no_split")
    phrase_xml = analyze_phrase_split(v1_dir / "xml")

    print_report(tree_info, meta, full_xml, phrase_xml)


if __name__ == "__main__":
    main()
