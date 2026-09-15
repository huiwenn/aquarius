#!/usr/bin/env python3
"""
POP909 Dataset Downloader
=========================
Downloads the POP909 dataset from GitHub and extracts it.

Source: https://github.com/music-x-lab/POP909-Dataset
Paper: "POP909: A Pop-song Dataset for Music Arrangement Generation"
       (Wang et al., ISMIR 2020)

Usage:
    conda activate py312
    python src/downloaders/pop909_download.py
"""

import os
import sys
import zipfile
import urllib.request
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────
REPO_BASE = "https://raw.githubusercontent.com/music-x-lab/POP909-Dataset/master"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "pop909"

FILES_TO_DOWNLOAD = [
    # (URL, output filename, description)
    (
        f"{REPO_BASE}/POP909.zip",
        "POP909.zip",
        "Main dataset archive (909 songs with MIDI + annotations)",
    ),
    (
        f"{REPO_BASE}/POP909/index.xlsx",
        "index.xlsx",
        "Metadata index (song names, artists, time signatures)",
    ),
    (
        f"{REPO_BASE}/data_process/data_process.ipynb",
        "data_process.ipynb",
        "Data processing notebook (Magenta event token conversion)",
    ),
    (
        f"{REPO_BASE}/data_process/processor.py",
        "processor.py",
        "MIDI processor script for event token conversion",
    ),
]


def download_file(url: str, output_path: Path, description: str) -> bool:
    """Download a file from URL to output_path."""
    if output_path.exists():
        print(f"  [SKIP] {output_path.name} already exists ({output_path.stat().st_size} bytes)")
        return True

    print(f"  [DOWN] {description}")
    print(f"         {url}")
    try:
        urllib.request.urlretrieve(url, str(output_path))
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"         -> {output_path.name} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract a zip archive."""
    print(f"  [EXTRACT] {zip_path.name}")
    try:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(str(extract_to))
        # Count extracted items
        extracted = list(extract_to.rglob("*"))
        files = [f for f in extracted if f.is_file()]
        dirs = [f for f in extracted if f.is_dir()]
        print(f"            -> {len(files)} files in {len(dirs)} directories")
        return True
    except Exception as e:
        print(f"  [FAIL] Extract error: {e}")
        return False


def verify_dataset(data_dir: Path) -> dict:
    """Verify the extracted dataset structure."""
    pop909_dir = data_dir / "POP909"
    results = {
        "pop909_dir_exists": pop909_dir.exists(),
        "song_dirs": 0,
        "main_midi_files": 0,
        "annotation_files": 0,
        "version_midi_files": 0,
        "index_xlsx": (data_dir / "index.xlsx").exists(),
    }

    if pop909_dir.exists():
        song_dirs = [
            d for d in pop909_dir.iterdir()
            if d.is_dir() and d.name.isdigit()
        ]
        results["song_dirs"] = len(song_dirs)

        for sd in song_dirs:
            sid = sd.name
            if (sd / f"{sid}.mid").exists():
                results["main_midi_files"] += 1
            results["annotation_files"] += sum(
                1 for f in sd.glob("*.txt")
            )
            versions_dir = sd / "versions"
            if versions_dir.exists():
                results["version_midi_files"] += sum(
                    1 for f in versions_dir.glob("*.mid")
                )

    return results


def main():
    print("=" * 60)
    print("POP909 Dataset Downloader")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}")

    # Download files
    print("\n--- Downloading files ---")
    success = True
    for url, filename, description in FILES_TO_DOWNLOAD:
        if not download_file(url, OUTPUT_DIR / filename, description):
            success = False

    if not success:
        print("\nSome downloads failed. Check errors above.")
        sys.exit(1)

    # Extract POP909.zip
    print("\n--- Extracting dataset ---")
    zip_path = OUTPUT_DIR / "POP909.zip"
    pop909_dir = OUTPUT_DIR / "POP909"
    if pop909_dir.exists() and any(pop909_dir.iterdir()):
        print(f"  [SKIP] POP909/ already extracted")
    else:
        if not extract_zip(zip_path, OUTPUT_DIR):
            sys.exit(1)

    # Verify
    print("\n--- Verifying dataset ---")
    results = verify_dataset(OUTPUT_DIR)
    print(f"  POP909 directory: {'OK' if results['pop909_dir_exists'] else 'MISSING'}")
    print(f"  Song directories: {results['song_dirs']}")
    print(f"  Main MIDI files: {results['main_midi_files']}")
    print(f"  Version MIDI files: {results['version_midi_files']}")
    print(f"  Annotation files: {results['annotation_files']}")
    print(f"  index.xlsx: {'OK' if results['index_xlsx'] else 'MISSING'}")

    if results["song_dirs"] == 909:
        print("\n[SUCCESS] Dataset downloaded and verified (909 songs)")
    else:
        print(f"\n[WARNING] Expected 909 songs, found {results['song_dirs']}")

    # Size check
    total_size = sum(
        f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()
    )
    print(f"\nTotal size: {total_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
