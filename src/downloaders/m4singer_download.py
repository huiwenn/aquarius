#!/usr/bin/env python3
"""Download M4Singer dataset from Google Drive.

M4Singer: A Multi-Style, Multi-Singer and Musical Score Provided
Mandarin Singing Corpus (NeurIPS 2022)
Paper: https://openreview.net/pdf?id=qiDmAaG6mP
GitHub: https://github.com/M4Singer/M4Singer
Project page: https://m4singer.github.io/

Downloads the dataset archive from Google Drive and extracts it
into data/raw/m4singer/. The dataset contains 700 Chinese pop songs
recorded by 20 professional singers covering all four SATB voice types.

Requirements:
    pip install gdown
"""

import argparse
import os
import sys
import zipfile
from pathlib import Path


def download_m4singer(output_dir: str, keep_archive: bool = False) -> None:
    """Download and extract the M4Singer dataset.

    Args:
        output_dir: Directory to extract dataset into.
        keep_archive: If True, keep the downloaded archive after extraction.
    """
    try:
        import gdown
    except ImportError:
        print("ERROR: gdown not installed. Run: pip install gdown")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Google Drive file ID from https://github.com/M4Singer/M4Singer
    gdrive_file_id = "1xC37E59EWRRFFLdG3aJkVqwtLDgtFNqW"
    gdrive_url = f"https://drive.google.com/uc?id={gdrive_file_id}"
    archive_path = output_path / "m4singer_download.zip"

    # Check if already downloaded by looking for singer directories
    # M4Singer uses singer IDs like Alto-1, Tenor-2, Soprano-1, Bass-3, etc.
    existing_dirs = [
        d for d in output_path.iterdir()
        if d.is_dir() and any(
            d.name.startswith(prefix)
            for prefix in ("Alto", "Tenor", "Soprano", "Bass")
        )
    ]
    if len(existing_dirs) >= 20:
        print(f"Dataset appears already extracted at {output_path} "
              f"({len(existing_dirs)} singer directories found)")
        return

    # Download
    print(f"Downloading M4Singer from Google Drive...")
    print(f"  URL: https://drive.google.com/file/d/{gdrive_file_id}/view")
    print(f"  Expected: ~3-4 GB archive with 700 songs by 20 singers")

    gdown.download(gdrive_url, str(archive_path), quiet=False)

    if not archive_path.exists():
        print("ERROR: Download failed.")
        print("  The Google Drive link may have download quota limits.")
        print("  Try downloading manually from:")
        print(f"    https://drive.google.com/file/d/{gdrive_file_id}/view")
        sys.exit(1)

    file_size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"  Downloaded: {file_size_mb:.1f} MB")

    # Check 50 GB cap
    if file_size_mb > 50 * 1024:
        print(f"ERROR: Archive is {file_size_mb:.0f} MB, exceeding the 50 GB cap.")
        print("  Keeping archive for manual inspection.")
        return

    # Extract - try zip first, then tar
    print(f"Extracting archive...")
    try:
        if zipfile.is_zipfile(str(archive_path)):
            with zipfile.ZipFile(str(archive_path), 'r') as zf:
                zf.extractall(path=str(output_path))
        else:
            # Try tarfile
            import tarfile
            with tarfile.open(str(archive_path)) as tf:
                tf.extractall(path=str(output_path))
    except Exception as e:
        print(f"ERROR: Extraction failed: {e}")
        print(f"  Archive kept at: {archive_path}")
        sys.exit(1)

    # Verify extraction
    extracted_dirs = [
        d for d in output_path.iterdir()
        if d.is_dir() and any(
            d.name.startswith(prefix)
            for prefix in ("Alto", "Tenor", "Soprano", "Bass")
        )
    ]
    if extracted_dirs:
        print(f"  Extracted {len(extracted_dirs)} singer directories")
        for d in sorted(extracted_dirs):
            wav_count = len(list(d.rglob("*.wav")))
            print(f"    {d.name}: {wav_count} WAV files")
    else:
        # Check if extracted into a subdirectory
        for subdir in output_path.iterdir():
            if subdir.is_dir():
                nested = [
                    d for d in subdir.iterdir()
                    if d.is_dir() and any(
                        d.name.startswith(prefix)
                        for prefix in ("Alto", "Tenor", "Soprano", "Bass")
                    )
                ]
                if nested:
                    print(f"  Found {len(nested)} singer directories under {subdir.name}/")
                    break
        else:
            print("WARNING: Expected singer directories not found after extraction")
            print(f"  Contents of {output_path}:")
            for item in sorted(output_path.iterdir()):
                print(f"    {item.name}")

    # Cleanup
    if not keep_archive and archive_path.exists():
        archive_path.unlink()
        print(f"  Removed archive: {archive_path}")
    elif keep_archive:
        print(f"  Kept archive: {archive_path}")

    print("Download complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Download M4Singer dataset from Google Drive"
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw/m4singer",
        help="Output directory (default: data/raw/m4singer)",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep the downloaded archive after extraction",
    )
    args = parser.parse_args()
    download_m4singer(args.output_dir, args.keep_archive)


if __name__ == "__main__":
    main()
