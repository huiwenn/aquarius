#!/usr/bin/env python3
"""
PMEmo Dataset Downloader
========================
Downloads the PMEmo dataset (2019 updated version) from Google Drive
and extracts it into data/raw/pmemo/dataset/.

Source: https://github.com/HuiZhangDB/PMEmo
Paper: "The PMEmo Dataset for Music Emotion Recognition"
       (Zhang et al., ACM ICMR 2018)

Requires: pip install gdown

Usage:
    conda activate py312
    python src/downloaders/pmemo_download.py
"""

import os
import sys
import zipfile
from pathlib import Path

try:
    import gdown
except ImportError:
    print("ERROR: gdown not installed. Run: pip install gdown")
    sys.exit(1)

# ── Configuration ──────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "pmemo" / "dataset"

# Google Drive folder URLs
UPDATED_URL = "https://drive.google.com/drive/folders/1qDk6hZDGVlVXgckjLq9LvXLZ9EgK9gw0?usp=sharing"
ORIGINAL_URL = "https://drive.google.com/drive/folders/1NhN4KaLQPFg9nRNOwne-Lnkxi3nlJHR3?usp=sharing"


def download_from_gdrive(url, output_dir):
    """Download a Google Drive folder using gdown."""
    print(f"Downloading from: {url}")
    print(f"Output directory: {output_dir}")
    gdown.download_folder(url, output=str(output_dir), quiet=False)


def extract_zip(zip_path, extract_to):
    """Extract a zip file."""
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    print(f"Extracted to {extract_to}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Try updated version first (2019)
    print("=" * 60)
    print("Downloading PMEmo dataset (2019 updated version)...")
    print("=" * 60)

    try:
        download_from_gdrive(UPDATED_URL, OUTPUT_DIR)
    except Exception as e:
        print(f"Updated version failed: {e}")
        print("Trying original version (2018)...")
        try:
            download_from_gdrive(ORIGINAL_URL, OUTPUT_DIR)
        except Exception as e2:
            print(f"Original version also failed: {e2}")
            print("BLOCKED: Cannot download PMEmo from Google Drive.")
            print("Manual download required from:")
            print(f"  Updated: {UPDATED_URL}")
            print(f"  Original: {ORIGINAL_URL}")
            sys.exit(1)

    # Find and extract zip file
    zip_candidates = list(OUTPUT_DIR.rglob("*.zip"))
    for zip_path in zip_candidates:
        print(f"\nFound zip: {zip_path}")
        extract_to = zip_path.parent
        extract_zip(zip_path, extract_to)

    # Verify extraction
    pmemo_dir = None
    for candidate in OUTPUT_DIR.rglob("metadata.csv"):
        pmemo_dir = candidate.parent
        break

    if pmemo_dir:
        print(f"\nDataset extracted successfully at: {pmemo_dir}")
        # Count files
        mp3_count = len(list(pmemo_dir.rglob("*.mp3")))
        csv_count = len(list(pmemo_dir.rglob("*.csv")))
        lrc_count = len(list(pmemo_dir.rglob("*.lrc")))
        print(f"  MP3 files: {mp3_count}")
        print(f"  CSV files: {csv_count}")
        print(f"  LRC files: {lrc_count}")
    else:
        print("WARNING: Could not find metadata.csv after extraction.")


if __name__ == "__main__":
    main()
