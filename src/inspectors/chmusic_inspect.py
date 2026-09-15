#!/usr/bin/env python3
"""Inspect ChMusic dataset: structure, audio properties, taxonomy.

ChMusic: A Traditional Chinese Music Dataset for Evaluation of Instrument Recognition
Paper: https://arxiv.org/abs/2108.08470

Walks the dataset directory, characterizes all files, extracts detailed
audio metadata (duration, sample rate, channels, bit depth), and maps
the instrument taxonomy.

Requirements:
    pip install soundfile librosa
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import soundfile as sf


# Instrument number to name mapping (from paper/README)
INSTRUMENT_MAP = {
    1: "Erhu",
    2: "Pipa",
    3: "Sanxian",
    4: "Dizi",
    5: "Suona",
    6: "Zhuiqin",
    7: "Zhongruan",
    8: "Liuqin",
    9: "Guzheng",
    10: "Yangqin",
    11: "Sheng",
}

# Instrument classification by family
INSTRUMENT_FAMILIES = {
    "Bowed strings (silk)": ["Erhu", "Zhuiqin"],
    "Plucked strings (silk)": ["Pipa", "Sanxian", "Zhongruan", "Liuqin", "Guzheng", "Yangqin"],
    "Wind - bamboo": ["Dizi"],
    "Wind - reed (metal/gourd)": ["Suona", "Sheng"],
}


def inspect_chmusic(data_dir: str) -> dict:
    """Run full inspection of ChMusic dataset.

    Args:
        data_dir: Path to data/raw/chmusic/ directory.

    Returns:
        Dictionary with all inspection results.
    """
    data_path = Path(data_dir)
    results = {
        "dataset": "ChMusic",
        "root_path": str(data_path),
        "directory_tree": {},
        "file_types": defaultdict(lambda: {"count": 0, "total_size_bytes": 0, "files": []}),
        "audio_files": [],
        "audio_summary": {},
        "instrument_taxonomy": {},
        "issues": [],
    }

    # ---- 1. Directory tree ----
    print("=== Directory Structure ===")
    tree = {}
    for root, dirs, files in os.walk(data_path):
        rel_root = os.path.relpath(root, data_path)
        if rel_root == ".":
            rel_root = ""
        level = rel_root.count(os.sep) if rel_root else 0
        indent = "  " * level
        dirname = os.path.basename(root) if rel_root else str(data_path.name)
        print(f"{indent}{dirname}/")
        tree[rel_root] = {"dirs": sorted(dirs), "files": sorted(files)}
        for f in sorted(files):
            print(f"{indent}  {f}")

    results["directory_tree"] = tree

    # ---- 2. File type census ----
    print("\n=== File Type Census ===")
    all_files = list(data_path.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]

    for f in all_files:
        ext = f.suffix.lower()
        if not ext:
            ext = "(no extension)"
        entry = results["file_types"][ext]
        entry["count"] += 1
        entry["total_size_bytes"] += f.stat().st_size
        entry["files"].append(str(f.relative_to(data_path)))

    for ext, info in sorted(results["file_types"].items()):
        size_mb = info["total_size_bytes"] / (1024 * 1024)
        print(f"  {ext}: {info['count']} files, {size_mb:.1f} MB")

    # ---- 3. Audio file analysis ----
    print("\n=== Audio File Analysis ===")
    musics_dir = data_path / "ChMusic" / "Musics"
    wav_files = sorted(musics_dir.glob("*.wav")) if musics_dir.exists() else []

    total_duration = 0.0
    sample_rates = set()
    channels_set = set()
    subtypes = set()
    durations = []
    file_sizes = []

    for wav_path in wav_files:
        try:
            info = sf.info(str(wav_path))
            duration = info.duration
            sr = info.samplerate
            ch = info.channels
            subtype = info.subtype
            fsize = wav_path.stat().st_size

            # Parse instrument and track number from filename
            stem = wav_path.stem  # e.g., "1.1"
            parts = stem.split(".")
            inst_num = int(parts[0])
            track_num = int(parts[1])
            inst_name = INSTRUMENT_MAP.get(inst_num, f"Unknown({inst_num})")

            audio_entry = {
                "filename": wav_path.name,
                "instrument_number": inst_num,
                "instrument_name": inst_name,
                "track_number": track_num,
                "duration_seconds": round(duration, 2),
                "sample_rate": sr,
                "channels": ch,
                "subtype": subtype,
                "file_size_bytes": fsize,
                "file_size_mb": round(fsize / (1024 * 1024), 2),
            }
            results["audio_files"].append(audio_entry)

            total_duration += duration
            sample_rates.add(sr)
            channels_set.add(ch)
            subtypes.add(subtype)
            durations.append(duration)
            file_sizes.append(fsize)

            print(f"  {wav_path.name}: {inst_name}, {duration:.1f}s, {sr}Hz, {ch}ch, {subtype}, {fsize/(1024*1024):.1f}MB")

        except Exception as e:
            msg = f"Error reading {wav_path.name}: {e}"
            print(f"  WARNING: {msg}")
            results["issues"].append(msg)

    # Audio summary
    if durations:
        results["audio_summary"] = {
            "total_files": len(wav_files),
            "total_duration_seconds": round(total_duration, 2),
            "total_duration_minutes": round(total_duration / 60, 2),
            "min_duration_seconds": round(min(durations), 2),
            "max_duration_seconds": round(max(durations), 2),
            "mean_duration_seconds": round(sum(durations) / len(durations), 2),
            "sample_rates": sorted(sample_rates),
            "channels": sorted(channels_set),
            "subtypes": sorted(subtypes),
            "total_audio_size_bytes": sum(file_sizes),
            "total_audio_size_mb": round(sum(file_sizes) / (1024 * 1024), 2),
        }

        print(f"\n  Summary:")
        print(f"    Total files: {len(wav_files)}")
        print(f"    Total duration: {total_duration/60:.1f} minutes ({total_duration:.1f} seconds)")
        print(f"    Duration range: {min(durations):.1f}s - {max(durations):.1f}s")
        print(f"    Mean duration: {sum(durations)/len(durations):.1f}s")
        print(f"    Sample rate(s): {sorted(sample_rates)}")
        print(f"    Channels: {sorted(channels_set)}")
        print(f"    Bit depth / subtype: {sorted(subtypes)}")
        print(f"    Total audio size: {sum(file_sizes)/(1024*1024):.1f} MB")

    # ---- 4. Per-instrument breakdown ----
    print("\n=== Per-Instrument Breakdown ===")
    instrument_stats = {}
    for inst_num in sorted(INSTRUMENT_MAP.keys()):
        inst_name = INSTRUMENT_MAP[inst_num]
        inst_files = [a for a in results["audio_files"] if a["instrument_number"] == inst_num]
        if inst_files:
            inst_durations = [a["duration_seconds"] for a in inst_files]
            inst_sizes = [a["file_size_mb"] for a in inst_files]
            stats = {
                "instrument_number": inst_num,
                "instrument_name": inst_name,
                "track_count": len(inst_files),
                "total_duration_seconds": round(sum(inst_durations), 2),
                "min_duration_seconds": round(min(inst_durations), 2),
                "max_duration_seconds": round(max(inst_durations), 2),
                "mean_duration_seconds": round(sum(inst_durations) / len(inst_durations), 2),
                "total_size_mb": round(sum(inst_sizes), 2),
            }
            instrument_stats[inst_name] = stats
            print(f"  {inst_num:2d}. {inst_name:10s}: {len(inst_files)} tracks, "
                  f"{sum(inst_durations):.0f}s total, "
                  f"range {min(inst_durations):.0f}-{max(inst_durations):.0f}s, "
                  f"{sum(inst_sizes):.1f} MB")

    results["instrument_taxonomy"] = {
        "instrument_count": len(INSTRUMENT_MAP),
        "tracks_per_instrument": 5,
        "instruments": instrument_stats,
        "families": INSTRUMENT_FAMILIES,
        "naming_convention": "x.y.wav where x=instrument_number(1-11), y=track_number(1-5)",
        "label_type": "single_instrument_per_track",
    }

    # ---- 5. Non-audio files ----
    print("\n=== Non-Audio Files ===")
    desc_dir = data_path / "ChMusic" / "InstrumentsDescription"
    if desc_dir.exists():
        for f in sorted(desc_dir.iterdir()):
            fsize = f.stat().st_size
            print(f"  {f.name}: {fsize/(1024):.0f} KB")

    # ---- 6. Verify completeness ----
    print("\n=== Completeness Check ===")
    expected_files = set()
    for inst in range(1, 12):
        for track in range(1, 6):
            expected_files.add(f"{inst}.{track}.wav")
    actual_files = set(f.name for f in wav_files)
    missing = expected_files - actual_files
    extra = actual_files - expected_files
    if missing:
        msg = f"Missing files: {sorted(missing)}"
        print(f"  WARNING: {msg}")
        results["issues"].append(msg)
    else:
        print(f"  All {len(expected_files)} expected WAV files present.")
    if extra:
        msg = f"Unexpected files: {sorted(extra)}"
        print(f"  Note: {msg}")
        results["issues"].append(msg)

    # Check for metadata files (CSV, JSON, etc.)
    metadata_exts = {".csv", ".json", ".txt", ".xml", ".yaml", ".yml", ".tsv"}
    metadata_files = [f for f in all_files if f.suffix.lower() in metadata_exts]
    if metadata_files:
        print(f"\n  Metadata files found:")
        for mf in metadata_files:
            print(f"    {mf.relative_to(data_path)}")
    else:
        print(f"  No structured metadata files (CSV/JSON/TXT) found.")
        print(f"  Labels are encoded in filenames only (instrument number).")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Inspect ChMusic dataset")
    parser.add_argument(
        "--data-dir",
        default="data/raw/chmusic",
        help="Path to chmusic data directory (default: data/raw/chmusic)",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional path to save full inspection results as JSON",
    )
    args = parser.parse_args()

    results = inspect_chmusic(args.data_dir)

    if args.output_json:
        # Convert defaultdict for JSON serialization
        results["file_types"] = dict(results["file_types"])
        with open(args.output_json, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nFull results saved to {args.output_json}")


if __name__ == "__main__":
    main()
