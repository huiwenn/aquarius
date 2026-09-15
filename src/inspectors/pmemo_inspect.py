#!/usr/bin/env python3
"""
PMEmo Dataset Inspector
=======================
Walks the PMEmo 2019 dataset directory, characterizes all files,
extracts metadata, analyzes annotations, audio, EDA, lyrics, and
comments, and reports comprehensive statistics.

Usage:
    conda activate py312
    python src/inspectors/pmemo_inspect.py
"""

import csv
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from mutagen.mp3 import MP3
except ImportError:
    print("WARNING: mutagen not installed. MP3 duration analysis skipped.")
    MP3 = None

# ── Configuration ──────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "pmemo" / "dataset"
# The dataset extracts into PMEmo/PMEmo2019/
PMEMO_DIR = DATA_DIR / "PMEmo" / "PMEmo2019"


# ── Helpers ────────────────────────────────────────────────────────

def read_csv(filepath, encoding="utf-8"):
    """Read a CSV file and return (header, rows)."""
    with open(filepath, "r", encoding=encoding) as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows


def count_files(directory, extension):
    """Count files with a given extension in a directory."""
    return len(list(Path(directory).glob(f"*.{extension}")))


# ── Inspection functions ──────────────────────────────────────────

def inspect_directory_tree():
    """Walk the directory tree and report structure."""
    print("=" * 60)
    print("DIRECTORY STRUCTURE")
    print("=" * 60)

    if not PMEMO_DIR.exists():
        print(f"ERROR: Dataset not found at {PMEMO_DIR}")
        sys.exit(1)

    for root, dirs, files in os.walk(PMEMO_DIR):
        level = len(Path(root).relative_to(PMEMO_DIR).parts)
        indent = "  " * level
        dirname = os.path.basename(root)
        print(f"{indent}{dirname}/ ({len(files)} files)")
        if level >= 2:
            dirs.clear()  # don't recurse too deep

    # Top-level files
    print("\nTop-level files:")
    for f in sorted(PMEMO_DIR.glob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"  {f.name} ({size:,} bytes)")


def inspect_metadata():
    """Analyze metadata.csv."""
    print("\n" + "=" * 60)
    print("METADATA (metadata.csv)")
    print("=" * 60)

    header, rows = read_csv(PMEMO_DIR / "metadata.csv")
    print(f"Columns ({len(header)}): {header}")
    print(f"Rows: {len(rows)}")

    # Column types and examples
    for i, col in enumerate(header):
        values = [r[i] for r in rows]
        non_empty = [v for v in values if v.strip()]
        missing = len(values) - len(non_empty)
        print(f"\n  {col}:")
        print(f"    Non-empty: {len(non_empty)}, Missing: {missing}")
        print(f"    Examples: {non_empty[:3]}")

        # Numeric stats where applicable
        try:
            nums = [float(v) for v in non_empty]
            print(f"    Range: [{min(nums):.2f}, {max(nums):.2f}]")
            print(f"    Mean: {sum(nums)/len(nums):.2f}")
        except ValueError:
            unique = len(set(non_empty))
            print(f"    Unique values: {unique}")

    # Language detection on artists
    cjk_artists = sum(
        1 for r in rows
        if re.search(r"[一-鿿぀-ゟ゠-ヿ가-힯]", r[3])
    )
    print(f"\nArtists with CJK characters: {cjk_artists}/{len(rows)}")

    return header, rows


def inspect_annotations():
    """Analyze static and dynamic annotation files."""
    print("\n" + "=" * 60)
    print("ANNOTATIONS")
    print("=" * 60)

    ann_dir = PMEMO_DIR / "annotations"

    # Static annotations
    header, rows = read_csv(ann_dir / "static_annotations.csv")
    print(f"\nstatic_annotations.csv:")
    print(f"  Columns: {header}")
    print(f"  Rows: {len(rows)} songs")

    arousal_vals = [float(r[1]) for r in rows]
    valence_vals = [float(r[2]) for r in rows]

    print(f"  Arousal(mean): [{min(arousal_vals):.4f}, {max(arousal_vals):.4f}], "
          f"mean={statistics.mean(arousal_vals):.4f}, std={statistics.stdev(arousal_vals):.4f}")
    print(f"  Valence(mean): [{min(valence_vals):.4f}, {max(valence_vals):.4f}], "
          f"mean={statistics.mean(valence_vals):.4f}, std={statistics.stdev(valence_vals):.4f}")

    q = [0.25, 0.5, 0.75]
    a_q = statistics.quantiles(arousal_vals, n=4)
    v_q = statistics.quantiles(valence_vals, n=4)
    print(f"  Arousal quartiles: Q1={a_q[0]:.4f}, Q2={a_q[1]:.4f}, Q3={a_q[2]:.4f}")
    print(f"  Valence quartiles: Q1={v_q[0]:.4f}, Q2={v_q[1]:.4f}, Q3={v_q[2]:.4f}")

    # Static annotations std
    header_std, rows_std = read_csv(ann_dir / "static_annotations_std.csv")
    arousal_std = [float(r[1]) for r in rows_std]
    valence_std = [float(r[2]) for r in rows_std]
    print(f"\nstatic_annotations_std.csv:")
    print(f"  Arousal(std): [{min(arousal_std):.4f}, {max(arousal_std):.4f}]")
    print(f"  Valence(std): [{min(valence_std):.4f}, {max(valence_std):.4f}]")

    # Dynamic annotations
    header_dyn, rows_dyn = read_csv(ann_dir / "dynamic_annotations.csv")
    print(f"\ndynamic_annotations.csv:")
    print(f"  Columns: {header_dyn}")
    print(f"  Total rows: {len(rows_dyn)}")

    # Frames per song
    song_frames = Counter(r[0] for r in rows_dyn)
    frame_counts = list(song_frames.values())
    print(f"  Songs with dynamic annotations: {len(song_frames)}")
    print(f"  Frames per song: min={min(frame_counts)}, max={max(frame_counts)}, "
          f"mean={statistics.mean(frame_counts):.1f}")

    dyn_arousal = [float(r[2]) for r in rows_dyn]
    dyn_valence = [float(r[3]) for r in rows_dyn]
    print(f"  Dynamic Arousal range: [{min(dyn_arousal):.4f}, {max(dyn_arousal):.4f}]")
    print(f"  Dynamic Valence range: [{min(dyn_valence):.4f}, {max(dyn_valence):.4f}]")

    frame_times = [float(r[1]) for r in rows_dyn]
    print(f"  Frame time range: [{min(frame_times):.1f}s, {max(frame_times):.1f}s]")
    print(f"  (First 15s removed per paper; 0.5s resolution)")

    return len(rows)


def inspect_chorus_audio():
    """Analyze MP3 chorus clips."""
    print("\n" + "=" * 60)
    print("CHORUS AUDIO (MP3)")
    print("=" * 60)

    chorus_dir = PMEMO_DIR / "chorus"
    mp3_files = sorted(chorus_dir.glob("*.mp3"))
    print(f"MP3 files: {len(mp3_files)}")

    if MP3 is None:
        print("  (mutagen not installed; skipping duration analysis)")
        return

    durations = []
    for f in mp3_files:
        try:
            audio = MP3(str(f))
            durations.append(audio.info.length)
        except Exception:
            durations.append(0)

    valid = [d for d in durations if d > 0]
    print(f"  Duration range: {min(valid):.1f}s - {max(valid):.1f}s")
    print(f"  Mean: {statistics.mean(valid):.1f}s, Median: {statistics.median(valid):.1f}s")
    print(f"  Std: {statistics.stdev(valid):.1f}s")
    print(f"  Total: {sum(valid)/3600:.1f} hours")

    # Duration buckets
    buckets = {"<20s": 0, "20-30s": 0, "30-45s": 0, "45-60s": 0, "60-90s": 0, ">90s": 0}
    for d in valid:
        if d < 20: buckets["<20s"] += 1
        elif d < 30: buckets["20-30s"] += 1
        elif d < 45: buckets["30-45s"] += 1
        elif d < 60: buckets["45-60s"] += 1
        elif d < 90: buckets["60-90s"] += 1
        else: buckets[">90s"] += 1
    print(f"  Distribution: {buckets}")

    # File sizes
    sizes = [f.stat().st_size for f in mp3_files]
    print(f"  File size: {min(sizes)/1024:.0f} KB - {max(sizes)/1024:.0f} KB")
    print(f"  Total size: {sum(sizes)/1024/1024:.0f} MB")


def inspect_eda():
    """Analyze EDA physiological signal files."""
    print("\n" + "=" * 60)
    print("EDA SIGNALS")
    print("=" * 60)

    eda_dir = PMEMO_DIR / "EDA"
    eda_files = sorted(eda_dir.glob("*_EDA.csv"))
    print(f"EDA files: {len(eda_files)}")

    all_subjects = set()
    annotator_counts = []

    for f in eda_files:
        header, rows = read_csv(f)
        subjects = header[1:]  # first column is time
        annotator_counts.append(len(subjects))
        all_subjects.update(subjects)

    print(f"Total unique annotator IDs: {len(all_subjects)}")
    print(f"Annotators per song: min={min(annotator_counts)}, max={max(annotator_counts)}, "
          f"mean={statistics.mean(annotator_counts):.1f}")

    # Sample one file for details
    header, rows = read_csv(eda_files[0])
    times = [float(r[0]) for r in rows]
    sampling_rate = 1 / (times[1] - times[0]) if len(times) > 1 else 0
    print(f"\nSample file ({eda_files[0].name}):")
    print(f"  Time samples: {len(rows)}")
    print(f"  Time range: {min(times):.2f}s - {max(times):.2f}s")
    print(f"  Sampling rate: ~{sampling_rate:.0f} Hz")
    print(f"  Annotators: {len(header)-1}")


def inspect_features():
    """Analyze pre-computed feature CSVs."""
    print("\n" + "=" * 60)
    print("PRE-COMPUTED FEATURES")
    print("=" * 60)

    feat_dir = PMEMO_DIR / "features"

    # Static features
    header, rows = read_csv(feat_dir / "static_features.csv")
    print(f"static_features.csv:")
    print(f"  Columns: {len(header)} (musicId + {len(header)-1} features)")
    print(f"  Rows: {len(rows)} songs")
    print(f"  Feature examples: {header[1:6]}...")
    print(f"  Extracted with OpenSMILE (6373 overall acoustic features)")

    # Dynamic features
    header_dyn, rows_dyn = read_csv(feat_dir / "dynamic_features.csv")
    song_ids = set(r[0] for r in rows_dyn)
    print(f"\ndynamic_features.csv:")
    print(f"  Columns: {len(header_dyn)} (musicId + frameTime + {len(header_dyn)-2} features)")
    print(f"  Rows: {len(rows_dyn)}")
    print(f"  Unique songs: {len(song_ids)}")
    print(f"  Feature examples: {header_dyn[2:7]}...")
    print(f"  260 low-level descriptors per 0.5s frame")


def inspect_lyrics():
    """Analyze LRC lyrics files."""
    print("\n" + "=" * 60)
    print("LYRICS (LRC)")
    print("=" * 60)

    lyrics_dir = PMEMO_DIR / "lyrics"
    lrc_files = sorted(lyrics_dir.glob("*.lrc"))
    print(f"LRC files: {len(lrc_files)}")

    chinese_only = 0
    english_only = 0
    mixed = 0
    other = 0
    encodings = Counter()

    for f in lrc_files:
        try:
            text = f.read_text(encoding="utf-8")
            encodings["utf-8"] += 1
        except UnicodeDecodeError:
            try:
                text = f.read_text(encoding="gbk")
                encodings["gbk"] += 1
            except Exception:
                other += 1
                continue

        # Remove timestamps and metadata
        clean = re.sub(r"\[\d+:\d+\.\d+\]", "", text)
        clean = re.sub(r"\[.*?\]", "", clean).strip()

        has_chinese = bool(re.search(r"[一-鿿]", clean))
        has_english = bool(re.search(r"[a-zA-Z]{3,}", clean))

        if has_chinese and has_english:
            mixed += 1
        elif has_chinese:
            chinese_only += 1
        elif has_english:
            english_only += 1
        else:
            other += 1

    print(f"  Language distribution:")
    print(f"    English only: {english_only}")
    print(f"    Mixed Chinese+English: {mixed}")
    print(f"    Chinese only: {chinese_only}")
    print(f"    Other/empty: {other}")
    print(f"  Encoding: {dict(encodings)}")
    print(f"  Format: LRC (timestamped lyrics, [mm:ss.xx] per line)")


def inspect_comments():
    """Analyze comment files from Netease and SoundCloud."""
    print("\n" + "=" * 60)
    print("COMMENTS")
    print("=" * 60)

    for source in ["netease", "soundcloud"]:
        comment_dir = PMEMO_DIR / "comments" / source
        txt_files = sorted(comment_dir.glob("*.txt"))
        print(f"\n{source}:")
        print(f"  Files: {len(txt_files)}")

        line_counts = []
        for f in txt_files:
            try:
                lines = f.read_text(encoding="utf-8").strip().split("\n")
                line_counts.append(len(lines))
            except Exception:
                pass

        if line_counts:
            print(f"  Comments per file: min={min(line_counts)}, max={max(line_counts)}, "
                  f"mean={statistics.mean(line_counts):.0f}")
            print(f"  Total comment lines: {sum(line_counts):,}")

    # netease_soundcloud.csv
    ns_path = PMEMO_DIR / "netease_soundcloud.csv"
    if ns_path.exists():
        header, rows = read_csv(ns_path)
        # First data row is actually the real header
        real_header = rows[0] if rows else header
        data_rows = rows[1:] if rows else []
        print(f"\nnetease_soundcloud.csv:")
        print(f"  Header row 1: {header}")
        print(f"  Header row 2 (actual column names): {real_header}")
        print(f"  Data rows: {len(data_rows)}")


def inspect_disk_usage():
    """Report disk usage by directory."""
    print("\n" + "=" * 60)
    print("DISK USAGE")
    print("=" * 60)

    def dir_size(path):
        total = 0
        for f in Path(path).rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total

    dirs = ["chorus", "annotations", "EDA", "features", "comments", "lyrics"]
    total = 0
    for d in dirs:
        p = PMEMO_DIR / d
        if p.exists():
            size = dir_size(p)
            total += size
            print(f"  {d}: {size/1024/1024:.0f} MB")

    # Top-level CSVs
    for f in PMEMO_DIR.glob("*.csv"):
        total += f.stat().st_size

    print(f"  Total (unzipped): {total/1024/1024:.0f} MB")


# ── Main ──────────────────────────────────────────────────────────

def main():
    print("PMEmo 2019 Dataset Inspection")
    print("=" * 60)
    print(f"Dataset path: {PMEMO_DIR}")

    inspect_directory_tree()
    inspect_metadata()
    inspect_annotations()
    inspect_chorus_audio()
    inspect_eda()
    inspect_features()
    inspect_lyrics()
    inspect_comments()
    inspect_disk_usage()

    print("\n" + "=" * 60)
    print("INSPECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
