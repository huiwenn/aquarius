#!/usr/bin/env python3
"""
Download script for CCOM-HuQin dataset from Zenodo.
Record: https://zenodo.org/records/11387046

The full dataset is ~142 GB (mostly video from 3 camera angles).
Under the 50 GB cap, we download:
  - CCOM-HuQin-v2.0.1-audios.zip (~2.5 GB) — all audio + annotations
We skip:
  - 6 video zip files (~139.5 GB total) — 3 camera angles x 2 subsets
    Videos are MP4 1080p 29.97fps from front/left/right cameras.
"""

import json
import subprocess
import sys
from pathlib import Path

ZENODO_RECORD = 11387046
API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD}"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "ccom_huqin"

# Files to download (only audio — videos exceed 50 GB cap)
INCLUDE_KEYS = {
    "CCOM-HuQin-v2.0.1-audios.zip",
}

# Files skipped (documented)
SKIPPED_FILES = [
    ("CCOM-HuQin-v2.0-videos-front-SinglePT.zip", "35.85 GB", "Front camera, single PT clips"),
    ("CCOM-HuQin-v2.0-videos-right-SinglePT.zip", "35.42 GB", "Right camera, single PT clips"),
    ("CCOM-HuQin-v2.0-videos-left-SinglePT.zip", "35.12 GB", "Left camera, single PT clips"),
    ("CCOM-HuQin-v2.0-videos-front-Excerpts.zip", "11.02 GB", "Front camera, musical excerpts"),
    ("CCOM-HuQin-v2.0-videos-right-Excerpts.zip", "11.02 GB", "Right camera, musical excerpts"),
    ("CCOM-HuQin-v2.0-videos-left-Excerpts.zip", "11.03 GB", "Left camera, musical excerpts"),
]


def get_file_list():
    """Fetch file metadata from Zenodo API."""
    result = subprocess.run(
        ["curl", "-s", API_URL],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    return data.get("files", [])


def download_file(url, dest, expected_size=None):
    """Download a file with wget, supporting resume."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "wget", "-c",  # continue partial downloads
        "--progress=dot:giga",
        "-O", str(dest),
        url
    ]
    print(f"Downloading: {dest.name} ({expected_size / (1024**3):.2f} GB)")
    subprocess.run(cmd, check=True)
    print(f"  Saved to: {dest}")


def extract_zip(zip_path, dest_dir):
    """Extract a zip file."""
    print(f"Extracting: {zip_path.name}")
    subprocess.run(
        ["unzip", "-o", "-q", str(zip_path), "-d", str(dest_dir)],
        check=True
    )
    print(f"  Extracted to: {dest_dir}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CCOM-HuQin Dataset Downloader")
    print(f"Zenodo record: {ZENODO_RECORD}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)

    # Fetch file list
    files = get_file_list()
    if not files:
        print("ERROR: No files found in Zenodo record.")
        sys.exit(1)

    print(f"\nFound {len(files)} files on Zenodo:")
    for f in files:
        size_gb = f["size"] / (1024**3)
        status = "DOWNLOAD" if f["key"] in INCLUDE_KEYS else "SKIP (video)"
        print(f"  [{status:14s}] {f['key']:55s} {size_gb:.2f} GB")

    print(f"\nSkipped files (50 GB cap):")
    for name, size, desc in SKIPPED_FILES:
        print(f"  - {name} ({size}): {desc}")

    # Download included files
    for f in files:
        if f["key"] not in INCLUDE_KEYS:
            continue
        url = f["links"]["self"] + "/content"
        dest = OUTPUT_DIR / f["key"]
        if dest.exists() and dest.stat().st_size == f["size"]:
            print(f"\nAlready downloaded: {f['key']}")
            continue
        download_file(url, dest, f["size"])

    # Extract zips
    for f in files:
        if f["key"] not in INCLUDE_KEYS:
            continue
        zip_path = OUTPUT_DIR / f["key"]
        if zip_path.exists():
            extract_zip(zip_path, OUTPUT_DIR)

    print("\nDownload complete.")
    print(f"Total downloaded: ~2.5 GB (audio + annotations)")
    print(f"Skipped: ~139.5 GB (video files, 6 zips)")


if __name__ == "__main__":
    main()
