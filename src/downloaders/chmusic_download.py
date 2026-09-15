#!/usr/bin/env python3
"""Download ChMusic dataset from Google Drive.

ChMusic: A Traditional Chinese Music Dataset for Evaluation of Instrument Recognition
Paper: https://arxiv.org/abs/2108.08470
GitHub: https://github.com/HaoranWeiUTD/ChMusic

Downloads the dataset archive from Google Drive and extracts it
into data/raw/chmusic/. The archive is a 7z file (~555 MB)
containing 55 WAV files and instrument description images.

Requirements:
    pip install gdown py7zr
"""

import argparse
import os
import sys
from pathlib import Path


def download_chmusic(output_dir: str, keep_archive: bool = False) -> None:
    """Download and extract the ChMusic dataset.

    Args:
        output_dir: Directory to extract dataset into.
        keep_archive: If True, keep the downloaded archive after extraction.
    """
    try:
        import gdown
    except ImportError:
        print("ERROR: gdown not installed. Run: pip install gdown")
        sys.exit(1)

    try:
        import py7zr
    except ImportError:
        print("ERROR: py7zr not installed. Run: pip install py7zr")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Google Drive file ID
    gdrive_file_id = "1rfbXpkYEUGw5h_CZJtC7eayYemeFMzij"
    gdrive_url = f"https://drive.google.com/uc?id={gdrive_file_id}"
    archive_path = output_path / "chmusic_download.7z"

    # Check if already extracted
    musics_dir = output_path / "ChMusic" / "Musics"
    if musics_dir.exists():
        wav_count = len(list(musics_dir.glob("*.wav")))
        if wav_count == 55:
            print(f"Dataset already extracted at {output_path}/ChMusic/ ({wav_count} WAV files)")
            return

    # Download
    print(f"Downloading ChMusic from Google Drive...")
    print(f"  URL: https://drive.google.com/file/d/{gdrive_file_id}/view")
    gdown.download(gdrive_url, str(archive_path), quiet=False)

    if not archive_path.exists():
        print("ERROR: Download failed. Try alternative source:")
        print("  Baidu Wangpan: pan.baidu.com/s/13e-6GnVJmC3tcwJtxed3-g (password: xk23)")
        sys.exit(1)

    file_size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"  Downloaded: {file_size_mb:.1f} MB")

    # Extract
    print(f"Extracting archive...")
    with py7zr.SevenZipFile(str(archive_path), mode='r') as z:
        z.extractall(path=str(output_path))

    # Verify
    if musics_dir.exists():
        wav_count = len(list(musics_dir.glob("*.wav")))
        print(f"  Extracted {wav_count} WAV files to {musics_dir}")
    else:
        print("WARNING: Expected ChMusic/Musics/ directory not found after extraction")

    # Cleanup
    if not keep_archive and archive_path.exists():
        archive_path.unlink()
        print(f"  Removed archive: {archive_path}")
    elif keep_archive:
        print(f"  Kept archive: {archive_path}")

    print("Download complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Download ChMusic dataset from Google Drive"
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw/chmusic",
        help="Output directory (default: data/raw/chmusic)",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep the downloaded archive after extraction",
    )
    args = parser.parse_args()
    download_chmusic(args.output_dir, args.keep_archive)


if __name__ == "__main__":
    main()
