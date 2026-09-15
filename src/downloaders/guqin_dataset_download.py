#!/usr/bin/env python3
"""
Download the Guqin Dataset from GitHub.

Source: https://github.com/lukewys/Guqin-Dataset
Method: git clone

The Guqin Dataset is a symbolic music dataset containing MusicXML
transcriptions of Guqin (ancient Chinese plucked zither) music, collected
from published Guqin scores with numbered notation (jianpu).

Usage:
    python src/downloaders/guqin_dataset_download.py [--output-dir DIR]
"""

import argparse
import subprocess
import sys
from pathlib import Path


REPO_URL = "https://github.com/lukewys/Guqin-Dataset"
DEFAULT_OUTPUT_DIR = "data/raw/guqin_dataset"


def download_guqin_dataset(output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
    """Clone the Guqin Dataset repository."""
    output_path = Path(output_dir)

    if output_path.exists() and any(output_path.iterdir()):
        print(f"Directory {output_path} already exists and is not empty.")
        print("To re-download, remove the directory first.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Cloning {REPO_URL} into {output_path}...")
    result = subprocess.run(
        ["git", "clone", REPO_URL, str(output_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error cloning repository: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully cloned Guqin Dataset to {output_path}")

    # Verify expected structure
    expected = [
        output_path / "Guqin_Dataset_v1" / "reference.csv",
        output_path / "Guqin_Dataset_v1" / "xml",
        output_path / "Guqin_Dataset_v1" / "xml_no_split",
    ]
    missing = [p for p in expected if not p.exists()]
    if missing:
        print("WARNING: Some expected paths are missing:", file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
    else:
        print("Verified: all expected directories and files present.")


def main():
    parser = argparse.ArgumentParser(
        description="Download the Guqin Dataset from GitHub."
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()
    download_guqin_dataset(args.output_dir)


if __name__ == "__main__":
    main()
