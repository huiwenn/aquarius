"""
Inspection script for the FolkMusic / China Traditional Music Instrument Dataset.

Walks the extracted dataset directory, maps the structure, counts clips per
instrument, samples audio files to verify format/duration/sample rate, and
checks for metadata files.

Usage:
    conda activate py312
    python src/inspectors/folkmusic_zenodo_inspect.py
"""

import json
import os
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Optional: use mutagen for audio inspection if available
try:
    from mutagen.mp3 import MP3

    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

# Optional: use librosa for deeper audio analysis
try:
    import librosa

    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

DATASET_DIR = Path("data/raw/folkmusic_zenodo")

# Expected instruments from the dataset description
EXPECTED_INSTRUMENTS = [
    "Ba",
    "Flute",  # Dizi
    "Dongxiao",
    "Erhu",
    "Guqin",
    "Guzheng",
    "Hulusi",
    "Liuqin",
    "Pipa",
    "Sanxian",
    "Sheng",
    "Suona",
    "Yangqin",
    "Zhongruan",
    "Falling Qin",
]


def walk_directory_tree(root: Path) -> dict:
    """Walk directory tree and return structure info."""
    structure = {
        "total_files": 0,
        "total_dirs": 0,
        "file_extensions": Counter(),
        "top_level_dirs": [],
        "files_by_dir": defaultdict(int),
        "metadata_files": [],
        "tree": [],
    }

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        depth = len(rel_dir.parts)
        structure["total_dirs"] += 1

        if depth == 0:
            structure["top_level_dirs"] = sorted(dirnames)

        for fn in filenames:
            structure["total_files"] += 1
            ext = Path(fn).suffix.lower()
            structure["file_extensions"][ext] += 1
            structure["files_by_dir"][str(rel_dir)] += 1

            # Check for metadata files
            if ext in (".csv", ".json", ".txt", ".xlsx", ".tsv", ".yaml", ".yml", ".xml"):
                structure["metadata_files"].append(str(rel_dir / fn))

        # Build tree (limited depth)
        if depth <= 2:
            indent = "  " * depth
            structure["tree"].append(f"{indent}{rel_dir.name or root.name}/")
            if depth <= 1:
                for fn in sorted(filenames)[:5]:
                    structure["tree"].append(f"{indent}  {fn}")
                if len(filenames) > 5:
                    structure["tree"].append(
                        f"{indent}  ... ({len(filenames) - 5} more files)"
                    )

    return structure


def count_clips_per_instrument(root: Path) -> dict:
    """Count audio clips per instrument (assumed to be top-level subdirectories)."""
    instrument_counts = {}

    for entry in sorted(root.iterdir()):
        if entry.is_dir() and entry.name != "__MACOSX":
            # Count all files recursively in each instrument directory
            mp3_count = sum(1 for f in entry.rglob("*.mp3"))
            wav_count = sum(1 for f in entry.rglob("*.wav"))
            total_audio = mp3_count + wav_count
            all_files = sum(1 for f in entry.rglob("*") if f.is_file())

            # Check for subdirectories (train/test splits, etc.)
            subdirs = [d.name for d in entry.iterdir() if d.is_dir()]

            instrument_counts[entry.name] = {
                "mp3": mp3_count,
                "wav": wav_count,
                "total_audio": total_audio,
                "all_files": all_files,
                "subdirs": subdirs,
            }

    return instrument_counts


def sample_audio_files(root: Path, n_samples: int = 3) -> list:
    """Sample audio files and verify format, duration, sample rate."""
    samples = []
    mp3_files = list(root.rglob("*.mp3"))

    if not mp3_files:
        print("No MP3 files found; checking for WAV files...")
        mp3_files = list(root.rglob("*.wav"))

    if not mp3_files:
        print("No audio files found!")
        return samples

    # Sample evenly from the list
    step = max(1, len(mp3_files) // n_samples)
    selected = mp3_files[::step][:n_samples]

    for audio_path in selected:
        info = {
            "path": str(audio_path.relative_to(root)),
            "size_bytes": audio_path.stat().st_size,
            "size_kb": round(audio_path.stat().st_size / 1024, 1),
        }

        if HAS_MUTAGEN and audio_path.suffix.lower() == ".mp3":
            try:
                mp3 = MP3(audio_path)
                info["duration_s"] = round(mp3.info.length, 2)
                info["sample_rate"] = mp3.info.sample_rate
                info["channels"] = mp3.info.channels
                info["bitrate"] = mp3.info.bitrate
                info["mode"] = mp3.info.mode
            except Exception as e:
                info["mutagen_error"] = str(e)

        if HAS_LIBROSA:
            try:
                y, sr = librosa.load(audio_path, sr=None, mono=False)
                info["librosa_sr"] = sr
                info["librosa_duration_s"] = round(len(y[0] if y.ndim > 1 else y) / sr, 2)
                info["librosa_channels"] = y.shape[0] if y.ndim > 1 else 1
                info["librosa_samples"] = y.shape[-1]
            except Exception as e:
                info["librosa_error"] = str(e)

        samples.append(info)

    return samples


def print_report(structure: dict, instrument_counts: dict, samples: list) -> str:
    """Generate and print inspection report, return as string."""
    lines = []

    def out(s=""):
        lines.append(s)
        print(s)

    out("=" * 70)
    out("FolkMusic Dataset Inspection Report")
    out("=" * 70)

    out("\n## Directory Structure")
    out(f"Total files: {structure['total_files']}")
    out(f"Total directories: {structure['total_dirs']}")
    out(f"Top-level directories: {structure['top_level_dirs']}")
    out(f"\nFile extensions:")
    for ext, count in structure["file_extensions"].most_common():
        out(f"  {ext or '(no ext)'}: {count}")

    out("\n## Directory Tree (depth <= 2)")
    for line in structure["tree"]:
        out(line)

    out("\n## Metadata Files")
    if structure["metadata_files"]:
        for mf in structure["metadata_files"]:
            out(f"  {mf}")
    else:
        out("  (none found)")

    out("\n## Clips per Instrument")
    out(f"{'Instrument':<20} {'MP3':>6} {'WAV':>6} {'Total Audio':>12} {'All Files':>10} {'Subdirs'}")
    out("-" * 80)
    total_audio = 0
    for name, counts in sorted(instrument_counts.items()):
        subdirs_str = ", ".join(counts["subdirs"]) if counts["subdirs"] else "-"
        out(
            f"{name:<20} {counts['mp3']:>6} {counts['wav']:>6} "
            f"{counts['total_audio']:>12} {counts['all_files']:>10} {subdirs_str}"
        )
        total_audio += counts["total_audio"]
    out("-" * 80)
    out(f"{'TOTAL':<20} {'':>6} {'':>6} {total_audio:>12}")

    out(f"\nNumber of instrument categories: {len(instrument_counts)}")

    out("\n## Audio Sample Verification")
    for i, sample in enumerate(samples):
        out(f"\nSample {i + 1}: {sample['path']}")
        out(f"  Size: {sample['size_kb']} KB")
        if "duration_s" in sample:
            out(f"  Duration: {sample['duration_s']} s")
            out(f"  Sample rate: {sample['sample_rate']} Hz")
            out(f"  Channels: {sample['channels']}")
            out(f"  Bitrate: {sample['bitrate']} bps")
        if "librosa_sr" in sample:
            out(f"  Librosa SR: {sample['librosa_sr']} Hz")
            out(f"  Librosa duration: {sample['librosa_duration_s']} s")
            out(f"  Librosa channels: {sample['librosa_channels']}")
        if "mutagen_error" in sample:
            out(f"  Mutagen error: {sample['mutagen_error']}")
        if "librosa_error" in sample:
            out(f"  Librosa error: {sample['librosa_error']}")

    out("\n" + "=" * 70)

    return "\n".join(lines)


def main():
    project_root = Path(__file__).resolve().parents[2]
    dataset_dir = project_root / DATASET_DIR

    if not dataset_dir.exists():
        print(f"Dataset directory not found: {dataset_dir}")
        print("Run the download script first.")
        sys.exit(1)

    print(f"Inspecting: {dataset_dir}")
    print(f"Mutagen available: {HAS_MUTAGEN}")
    print(f"Librosa available: {HAS_LIBROSA}")
    print()

    # Find the actual data root (may be nested inside a subdirectory)
    # Check if there's a single top-level directory containing the instrument folders
    top_entries = [e for e in dataset_dir.iterdir() if e.is_dir() and e.name != "__MACOSX"]

    # If there's a single directory that looks like a container, use it as root
    data_root = dataset_dir
    if len(top_entries) == 1:
        inner_dirs = [e for e in top_entries[0].iterdir() if e.is_dir()]
        if len(inner_dirs) > 5:  # Likely the instrument folders
            data_root = top_entries[0]
            print(f"Using nested data root: {data_root.name}/")

    # Step 1: Walk directory tree
    print("Walking directory tree...")
    structure = walk_directory_tree(dataset_dir)

    # Step 2: Count clips per instrument
    print("Counting clips per instrument...")
    instrument_counts = count_clips_per_instrument(data_root)

    # Step 3: Sample audio files
    print("Sampling audio files...")
    samples = sample_audio_files(data_root, n_samples=5)

    # Step 4: Print report
    print()
    report = print_report(structure, instrument_counts, samples)

    # Save report
    report_path = project_root / "data" / "raw" / "folkmusic_zenodo" / "inspection_report.txt"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
