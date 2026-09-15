#!/usr/bin/env python3
"""Download Opencpop dataset.

Opencpop: A High-Quality Open Source Chinese Popular Song Corpus for
Singing Voice Synthesis.
Paper: https://arxiv.org/abs/2201.07429
Website: https://wenet-e2e.github.io/opencpop/
GitHub: https://github.com/wenet-e2e/opencpop

ACCESS METHOD: Gated download via Google Form.
  1. Fill out the form: https://forms.gle/LnsbLqE6GcExhT5U6
     (Name, email, organization, address; agree to non-commercial terms)
  2. Check your email for a download link (usually a Google Drive link)
  3. Run this script with the link:
       python opencpop_download.py --url "<link_from_email>"

The dataset is approximately 5.2 hours of audio (~3.8 GB compressed).
Contains: 100 songs, 3,756 utterances, WAV 44,100 Hz, phonetic annotations.

License: CC BY 4.0 (non-commercial use per terms of access form).
Contact: zpcoftts@gmail.com

Requirements:
    pip install gdown  (if Google Drive link)
"""

import argparse
import os
import subprocess
import sys
import zipfile
import tarfile
from pathlib import Path


def detect_link_type(url: str) -> str:
    """Detect whether URL is Google Drive, HTTP direct, or other."""
    if "drive.google.com" in url or "docs.google.com" in url:
        return "gdrive"
    elif url.startswith("http://") or url.startswith("https://"):
        return "http"
    else:
        return "unknown"


def download_gdrive(url: str, output_path: Path) -> Path:
    """Download from Google Drive using gdown."""
    try:
        import gdown
    except ImportError:
        print("ERROR: gdown not installed. Run: pip install gdown")
        sys.exit(1)

    # gdown handles both /file/d/ and /uc?id= formats
    archive_name = "opencpop_download"
    print(f"Downloading Opencpop from Google Drive...")
    print(f"  URL: {url}")
    downloaded = gdown.download(
        url, str(output_path / archive_name), quiet=False, fuzzy=True
    )
    if downloaded is None:
        print("ERROR: gdown download failed. The link may have expired.")
        print("  Request a new link at: https://forms.gle/LnsbLqE6GcExhT5U6")
        sys.exit(1)
    return Path(downloaded)


def download_http(url: str, output_path: Path) -> Path:
    """Download via wget/curl."""
    # Guess filename from URL
    url_basename = url.split("/")[-1].split("?")[0]
    if not url_basename or len(url_basename) < 3:
        url_basename = "opencpop_download"
    dest = output_path / url_basename

    print(f"Downloading Opencpop via HTTP...")
    print(f"  URL: {url}")
    print(f"  Destination: {dest}")

    # Try wget first, then curl
    try:
        subprocess.run(
            ["wget", "-c", "-O", str(dest), url],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            subprocess.run(
                ["curl", "-L", "-C", "-", "-o", str(dest), url],
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"ERROR: Download failed: {e}")
            sys.exit(1)

    return dest


def extract_archive(archive_path: Path, output_dir: Path) -> None:
    """Extract tar.gz, zip, or other archive formats."""
    name = archive_path.name.lower()
    print(f"Extracting {archive_path.name}...")

    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        with tarfile.open(str(archive_path), "r:gz") as tar:
            tar.extractall(path=str(output_dir))
    elif name.endswith(".tar"):
        with tarfile.open(str(archive_path), "r:") as tar:
            tar.extractall(path=str(output_dir))
    elif name.endswith(".zip"):
        with zipfile.ZipFile(str(archive_path), "r") as zf:
            zf.extractall(path=str(output_dir))
    else:
        print(f"  Archive format not auto-detected for {name}.")
        print(f"  Please extract manually to {output_dir}")
        return

    print(f"  Extracted to {output_dir}")


def verify_opencpop(data_dir: Path) -> bool:
    """Verify expected Opencpop structure exists."""
    expected_dirs = ["wavs", "segments", "textgrids", "midis"]
    found = []
    missing = []

    # Check top-level or one level deep (in case archive has a wrapper dir)
    check_dirs = [data_dir]
    for child in data_dir.iterdir():
        if child.is_dir():
            check_dirs.append(child)

    for check_dir in check_dirs:
        found_here = [d for d in expected_dirs if (check_dir / d).is_dir()]
        if len(found_here) >= 3:
            print(f"  Found Opencpop structure in: {check_dir}")
            for d in expected_dirs:
                subdir = check_dir / d
                if subdir.exists():
                    count = len(list(subdir.iterdir()))
                    print(f"    {d}/: {count} items")
                    found.append(d)
                else:
                    print(f"    {d}/: MISSING")
                    missing.append(d)
            return len(missing) == 0

    print("  WARNING: Could not find expected Opencpop directory structure.")
    print(f"  Expected subdirectories: {expected_dirs}")
    print(f"  Contents of {data_dir}:")
    for item in sorted(data_dir.iterdir()):
        print(f"    {item.name}{'/' if item.is_dir() else ''}")
    return False


def download_opencpop(
    url: str, output_dir: str, keep_archive: bool = False
) -> None:
    """Download, extract, and verify the Opencpop dataset.

    Args:
        url: Download URL (Google Drive or direct HTTP).
        output_dir: Directory to extract dataset into.
        keep_archive: If True, keep the downloaded archive after extraction.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    if (output_path / "wavs").is_dir() and (output_path / "segments").is_dir():
        wav_count = len(list((output_path / "wavs").glob("*.wav")))
        seg_count = len(list((output_path / "segments" / "wavs").glob("*.wav")))
        if wav_count > 50 and seg_count > 1000:
            print(
                f"Dataset already present at {output_path}/ "
                f"({wav_count} full WAVs, {seg_count} segment WAVs)"
            )
            return

    # Download
    link_type = detect_link_type(url)
    if link_type == "gdrive":
        archive_path = download_gdrive(url, output_path)
    elif link_type == "http":
        archive_path = download_http(url, output_path)
    else:
        print(f"ERROR: Unrecognized URL format: {url}")
        print("  Expected Google Drive or HTTP URL.")
        sys.exit(1)

    file_size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"  Downloaded: {file_size_mb:.1f} MB -> {archive_path}")

    # Extract if it's an archive
    if archive_path.suffix.lower() in (".zip", ".gz", ".tar", ".tgz", ".7z"):
        extract_archive(archive_path, output_path)
    elif archive_path.name.endswith(".tar.gz"):
        extract_archive(archive_path, output_path)
    else:
        print(f"  File downloaded but may not be an archive: {archive_path.name}")
        print(f"  Check manually.")

    # Verify
    print("\n=== Verification ===")
    verify_opencpop(output_path)

    # Cleanup
    if not keep_archive and archive_path.exists() and archive_path.is_file():
        archive_path.unlink()
        print(f"  Removed archive: {archive_path}")
    elif keep_archive:
        print(f"  Kept archive: {archive_path}")

    print("\nDownload complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Download Opencpop dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
ACCESS: This dataset requires a Google Form submission first.
  1. Fill out: https://forms.gle/LnsbLqE6GcExhT5U6
  2. Receive download link by email
  3. Run: python opencpop_download.py --url "<link_from_email>"

Contact: zpcoftts@gmail.com (if no email received)
""",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Download URL received via email after form submission",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw/opencpop",
        help="Output directory (default: data/raw/opencpop)",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep the downloaded archive after extraction",
    )
    args = parser.parse_args()

    download_opencpop(args.url, args.output_dir, args.keep_archive)


if __name__ == "__main__":
    main()
