"""
Download script for the FolkMusic / China Traditional Music Instrument Dataset.

Source: https://zenodo.org/records/8012071
License: CC Attribution 4.0 International
Size: ~5.6 GB (FolkMusic.zip)

This dataset contains 3-second MP3 clips of 15 traditional Chinese instruments
recorded in dual-channel at 44,100 Hz. Designed for instrument recognition tasks.

Usage:
    conda activate py312
    python src/downloaders/folkmusic_zenodo_download.py
"""

import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ZENODO_RECORD = "8012071"
DOWNLOAD_URL = f"https://zenodo.org/records/{ZENODO_RECORD}/files/FolkMusic.zip"
OUTPUT_DIR = Path("data/raw/folkmusic_zenodo")
ZIP_FILENAME = "FolkMusic.zip"


def download_file(url: str, dest: Path) -> None:
    """Download a file using wget with resume support."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "wget",
        "-c",  # resume partial downloads
        "--progress=dot:giga",
        url,
        "-O",
        str(dest),
    ]
    print(f"Downloading {url}")
    print(f"  -> {dest}")
    subprocess.run(cmd, check=True)


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a zip file, preserving original structure."""
    print(f"Extracting {zip_path} -> {extract_to}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    print("Extraction complete.")


def compute_md5(filepath: Path, chunk_size: int = 8192) -> str:
    """Compute MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()


def main():
    project_root = Path(__file__).resolve().parents[2]
    output_dir = project_root / OUTPUT_DIR
    zip_path = output_dir / ZIP_FILENAME

    # Step 1: Download
    if zip_path.exists():
        size_gb = zip_path.stat().st_size / (1024**3)
        print(f"ZIP already exists: {zip_path} ({size_gb:.2f} GB)")
        print("Skipping download (delete file to re-download).")
    else:
        download_file(DOWNLOAD_URL, zip_path)

    # Step 2: Compute checksum
    print("Computing MD5 checksum...")
    md5 = compute_md5(zip_path)
    print(f"MD5: {md5}")

    # Step 3: Extract
    # Check if already extracted by looking for subdirectories
    extracted_dirs = [
        d for d in output_dir.iterdir() if d.is_dir() and d.name != "__MACOSX"
    ]
    if extracted_dirs:
        print(f"Already extracted ({len(extracted_dirs)} directories found).")
        print("Skipping extraction (delete directories to re-extract).")
    else:
        extract_zip(zip_path, output_dir)

    print("\nDone! Dataset is at:", output_dir)


if __name__ == "__main__":
    main()
