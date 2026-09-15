#!/usr/bin/env python3
"""
Inspection script for CCOM-HuQin dataset.
Walks directory tree, counts clips per instrument, checks audio specs,
parses annotation files.
"""

import os
import sys
import json
import csv
from pathlib import Path
from collections import Counter, defaultdict

# Try importing audio libraries
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "ccom_huqin"


def walk_directory_tree(root):
    """Walk and display the directory tree structure."""
    print("=" * 70)
    print("DIRECTORY STRUCTURE")
    print("=" * 70)

    dir_counts = {}
    file_types = Counter()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel = os.path.relpath(dirpath, root)
        depth = rel.count(os.sep) if rel != "." else 0
        indent = "  " * depth
        dirname = os.path.basename(dirpath) if rel != "." else str(root.name)
        n_files = len(filenames)
        n_dirs = len(dirnames)

        if depth <= 4:
            print(f"{indent}{dirname}/ ({n_files} files, {n_dirs} subdirs)")

        dir_counts[rel] = n_files
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            file_types[ext] += 1

    print(f"\nFile type summary:")
    for ext, count in file_types.most_common():
        print(f"  {ext or '(no ext)':12s}: {count:6d}")

    return file_types


def count_clips_per_instrument(root):
    """Count audio clips per instrument type."""
    print("\n" + "=" * 70)
    print("CLIPS PER INSTRUMENT")
    print("=" * 70)

    instrument_counts = Counter()
    instrument_durations = defaultdict(float)
    pt_counts = Counter()
    instrument_pt = defaultdict(Counter)

    # Known instrument abbreviations from the paper
    instrument_names = {
        "erhu": "Erhu (二胡)",
        "zhonghu": "Zhonghu (中胡)",
        "gaohu": "Gaohu (高胡)",
        "zhuihu": "Zhuihu (坠胡)",
        "banhu": "Banhu (板胡)",
        "sbh": "Soprano Banhu (高音板胡)",
        "abh": "Alto Banhu (中音板胡)",
        "tbh": "Tenor Banhu (次中音板胡)",
    }

    audio_files = list(root.rglob("*.wav")) + list(root.rglob("*.WAV"))
    print(f"\nTotal audio files found: {len(audio_files)}")

    for f in audio_files:
        parts = f.parts
        fname = f.stem.lower()
        fpath = str(f).lower()

        # Try to identify instrument from path or filename
        found = False
        for abbr, name in instrument_names.items():
            if abbr in fpath:
                instrument_counts[name] += 1
                found = True
                break
        if not found:
            instrument_counts["Unknown"] += 1

        # Try to identify playing technique from filename
        pt_keywords = [
            "tremolo", "chang", "diang", "dung", "duang", "tiaog",
            "paog", "jig", "dajig", "vibrato", "rvib", "pvib", "svib",
            "port", "uport", "dport", "udport", "duport", "iport",
            "trill", "dayin", "shtrill", "lotrill", "pizz",
        ]
        for pt in pt_keywords:
            if pt in fname:
                pt_counts[pt] += 1
                break

    print("\nClip counts by instrument:")
    for inst, count in sorted(instrument_counts.items(), key=lambda x: -x[1]):
        print(f"  {inst:35s}: {count:6d}")
    print(f"  {'TOTAL':35s}: {sum(instrument_counts.values()):6d}")

    if pt_counts:
        print("\nClip counts by playing technique (from filenames):")
        for pt, count in sorted(pt_counts.items(), key=lambda x: -x[1]):
            print(f"  {pt:20s}: {count:6d}")

    return instrument_counts, pt_counts


def check_audio_specs(root, sample_size=20):
    """Check audio format, duration, sample rate for a sample of files."""
    print("\n" + "=" * 70)
    print("AUDIO SPECIFICATIONS")
    print("=" * 70)

    audio_files = sorted(root.rglob("*.wav"))
    if not audio_files:
        audio_files = sorted(root.rglob("*.WAV"))

    if not audio_files:
        print("No WAV files found!")
        return {}

    print(f"Total WAV files: {len(audio_files)}")
    print(f"Sampling {min(sample_size, len(audio_files))} files for specs...")

    sample = audio_files[:sample_size]
    specs = {
        "sample_rates": Counter(),
        "channels": Counter(),
        "bit_depths": Counter(),
        "durations": [],
        "formats": Counter(),
    }

    if HAS_SOUNDFILE:
        for f in sample:
            try:
                info = sf.info(str(f))
                specs["sample_rates"][info.samplerate] += 1
                specs["channels"][info.channels] += 1
                specs["formats"][info.subtype] += 1
                specs["durations"].append(info.duration)
            except Exception as e:
                print(f"  Error reading {f.name}: {e}")
    elif HAS_LIBROSA:
        for f in sample:
            try:
                y, sr = librosa.load(str(f), sr=None, mono=False)
                dur = len(y) / sr if y.ndim == 1 else y.shape[1] / sr
                specs["sample_rates"][sr] += 1
                specs["channels"][1 if y.ndim == 1 else y.shape[0]] += 1
                specs["durations"].append(dur)
            except Exception as e:
                print(f"  Error reading {f.name}: {e}")
    else:
        print("  WARNING: Neither soundfile nor librosa available. Install with:")
        print("    pip install soundfile")
        # Try to get basic info from file headers
        for f in sample:
            try:
                import wave
                with wave.open(str(f), 'r') as wf:
                    sr = wf.getframerate()
                    ch = wf.getnchannels()
                    sw = wf.getsampwidth()
                    frames = wf.getnframes()
                    dur = frames / sr
                    specs["sample_rates"][sr] += 1
                    specs["channels"][ch] += 1
                    specs["bit_depths"][sw * 8] += 1
                    specs["durations"].append(dur)
            except Exception as e:
                print(f"  Error reading {f.name}: {e}")

    print("\nSample rates:")
    for sr, count in specs["sample_rates"].most_common():
        print(f"  {sr} Hz: {count} files")

    print("\nChannels:")
    for ch, count in specs["channels"].most_common():
        print(f"  {ch} channel(s): {count} files")

    if specs["formats"]:
        print("\nAudio subtypes:")
        for fmt, count in specs["formats"].most_common():
            print(f"  {fmt}: {count} files")

    if specs["bit_depths"]:
        print("\nBit depths:")
        for bd, count in specs["bit_depths"].most_common():
            print(f"  {bd}-bit: {count} files")

    if specs["durations"]:
        durs = specs["durations"]
        print(f"\nDuration stats (sample of {len(durs)}):")
        print(f"  Min: {min(durs):.2f}s")
        print(f"  Max: {max(durs):.2f}s")
        print(f"  Mean: {sum(durs)/len(durs):.2f}s")

    # Get total duration across all files if soundfile available
    if HAS_SOUNDFILE and len(audio_files) > sample_size:
        print(f"\nComputing total duration across all {len(audio_files)} files...")
        total_dur = 0
        for f in audio_files:
            try:
                info = sf.info(str(f))
                total_dur += info.duration
            except:
                pass
        hours = total_dur / 3600
        mins = (total_dur % 3600) / 60
        print(f"  Total duration: {hours:.1f}h ({int(hours)}h {int(mins)}m)")

    return specs


def inspect_annotations(root):
    """Find and inspect annotation files (CSV, XML, MusicXML, JSON, etc.)."""
    print("\n" + "=" * 70)
    print("ANNOTATION FILES")
    print("=" * 70)

    ann_extensions = {".csv", ".json", ".xml", ".musicxml", ".mxl", ".txt", ".lab", ".TextGrid", ".textgrid"}
    ann_files = []
    for ext in ann_extensions:
        ann_files.extend(root.rglob(f"*{ext}"))
        ann_files.extend(root.rglob(f"*{ext.upper()}"))

    # Also check for PDF scores
    pdf_files = list(root.rglob("*.pdf"))

    print(f"Annotation files found: {len(ann_files)}")
    print(f"PDF files (scores): {len(pdf_files)}")

    # Group by extension
    by_ext = defaultdict(list)
    for f in ann_files:
        by_ext[f.suffix.lower()].append(f)

    for ext, files in sorted(by_ext.items()):
        print(f"\n--- {ext} files: {len(files)} ---")
        # Show a sample
        sample = sorted(files)[:3]
        for f in sample:
            print(f"\n  File: {os.path.relpath(f, root)}")
            print(f"  Size: {f.stat().st_size:,} bytes")
            try:
                if ext == ".csv":
                    inspect_csv(f)
                elif ext == ".json":
                    inspect_json(f)
                elif ext in (".xml", ".musicxml", ".mxl"):
                    inspect_xml(f)
                elif ext in (".txt", ".lab"):
                    inspect_text(f)
            except Exception as e:
                print(f"  Error inspecting: {e}")

    if pdf_files:
        print(f"\n--- PDF files: {len(pdf_files)} ---")
        for f in sorted(pdf_files)[:5]:
            print(f"  {os.path.relpath(f, root)} ({f.stat().st_size:,} bytes)")

    return ann_files


def inspect_csv(filepath):
    """Inspect a CSV annotation file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("    (empty)")
        return

    print(f"    Rows: {len(rows)} (including header)")
    print(f"    Columns: {len(rows[0])}")
    print(f"    Header: {rows[0]}")
    if len(rows) > 1:
        print(f"    First row: {rows[1]}")
    if len(rows) > 2:
        print(f"    Second row: {rows[2]}")


def inspect_json(filepath):
    """Inspect a JSON annotation file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        print(f"    Type: dict with {len(data)} keys")
        print(f"    Keys: {list(data.keys())[:10]}")
        for k in list(data.keys())[:3]:
            v = data[k]
            if isinstance(v, (str, int, float)):
                print(f"    {k}: {v}")
            elif isinstance(v, list):
                print(f"    {k}: list of {len(v)} items")
                if v and isinstance(v[0], dict):
                    print(f"      First item keys: {list(v[0].keys())}")
            elif isinstance(v, dict):
                print(f"    {k}: dict with {len(v)} keys")
    elif isinstance(data, list):
        print(f"    Type: list of {len(data)} items")
        if data and isinstance(data[0], dict):
            print(f"    First item keys: {list(data[0].keys())}")
            print(f"    First item: {data[0]}")


def inspect_xml(filepath):
    """Inspect an XML/MusicXML file."""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(filepath)
        root_elem = tree.getroot()
        print(f"    Root tag: {root_elem.tag}")
        children = [c.tag for c in root_elem]
        print(f"    Top-level children: {children[:10]}")
        print(f"    Total elements: {sum(1 for _ in root_elem.iter())}")
    except Exception as e:
        # Fallback: read first few lines
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[:5]
        for line in lines:
            print(f"    {line.rstrip()}")


def inspect_text(filepath):
    """Inspect a text/lab annotation file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    print(f"    Lines: {len(lines)}")
    for line in lines[:5]:
        print(f"    {line.rstrip()}")


def summarize_subset_structure(root):
    """Identify and summarize the two subsets: SinglePT and Excerpts."""
    print("\n" + "=" * 70)
    print("SUBSET ANALYSIS")
    print("=" * 70)

    # Look for SinglePT and Excerpts directories/patterns
    singlept_files = []
    excerpt_files = []

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        fpath = str(f).lower()
        if "singlept" in fpath or "single_pt" in fpath or "single-pt" in fpath:
            singlept_files.append(f)
        elif "excerpt" in fpath:
            excerpt_files.append(f)

    if singlept_files or excerpt_files:
        print(f"\nSinglePT subset files: {len(singlept_files)}")
        print(f"Excerpts subset files: {len(excerpt_files)}")

        # Count audio in each
        spt_audio = [f for f in singlept_files if f.suffix.lower() == ".wav"]
        exc_audio = [f for f in excerpt_files if f.suffix.lower() == ".wav"]
        print(f"\nSinglePT audio clips: {len(spt_audio)}")
        print(f"Excerpts audio clips: {len(exc_audio)}")
    else:
        # Try to find subsets by directory names
        print("Searching for subset indicators in directory structure...")
        for d in sorted(root.rglob("*")):
            if d.is_dir():
                name = d.name.lower()
                if any(x in name for x in ["single", "excerpt", "pt", "piece"]):
                    n_files = sum(1 for _ in d.rglob("*") if _.is_file())
                    print(f"  {os.path.relpath(d, root)}: {n_files} files")


def main():
    if not DATA_DIR.exists():
        print(f"ERROR: Data directory not found: {DATA_DIR}")
        sys.exit(1)

    print(f"Inspecting CCOM-HuQin dataset at: {DATA_DIR}")
    print(f"Total size: ", end="")
    total = sum(f.stat().st_size for f in DATA_DIR.rglob("*") if f.is_file())
    print(f"{total / (1024**3):.2f} GB")

    # 1. Walk directory tree
    file_types = walk_directory_tree(DATA_DIR)

    # 2. Count clips per instrument
    inst_counts, pt_counts = count_clips_per_instrument(DATA_DIR)

    # 3. Check audio specs
    specs = check_audio_specs(DATA_DIR, sample_size=50)

    # 4. Inspect annotations
    ann_files = inspect_annotations(DATA_DIR)

    # 5. Subset analysis
    summarize_subset_structure(DATA_DIR)

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
