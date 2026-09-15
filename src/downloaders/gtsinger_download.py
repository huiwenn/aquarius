#!/usr/bin/env python3
"""
Download the Chinese portion of GTSinger from HuggingFace.

GTSinger (NeurIPS 2024 Spotlight) is a global multi-technique singing corpus
covering 9 languages. The full dataset is ~54 GB. For Aquarius we need only
the Chinese subset (~10.7 GB: raw audio + annotations + processed metadata).

HuggingFace repo: GTSinger/GTSinger
Paper: https://arxiv.org/abs/2409.13832

Dataset structure on HF:
    Chinese/
        ZH-Alto-1/       # Female alto singer
        ZH-Tenor-1/      # Male tenor singer
        (each singer)/
            Breathy/
            Glissando/
            Mixed_Voice_and_Falsetto/
            Pharyngeal/
            Vibrato/
            (each technique)/
                (song_name)/
                    Breathy_Group/ | Control_Group/ | Paired_Speech_Group/ | ...
                        XXXX.wav        # 48 kHz mono 24-bit PCM
                        XXXX.json       # phoneme + note alignment
                        XXXX.TextGrid   # Praat TextGrid
                        XXXX.musicxml   # music score
    processed/Chinese/
        metadata.json     # ~39.5 MB processed metadata for all Chinese segments
        phone_set.json    # phoneme set
        spker_set.json    # speaker set

Folders downloaded:
    Chinese/         ~10.65 GB (raw audio + annotations)
    processed/Chinese/  ~0.04 GB (metadata)

Skipped (other languages): English, French, German, Italian, Japanese,
    Korean, Russian, Spanish, processed/All

Usage:
    conda activate py312
    python src/downloaders/gtsinger_download.py
    # Dry run (just count files, don't download):
    python src/downloaders/gtsinger_download.py --dry-run
"""

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "raw" / "gtsinger"
REPO_ID = "GTSinger/GTSinger"

# Folders to download (Chinese raw + processed metadata)
INCLUDE_PREFIXES = ["Chinese/", "processed/Chinese/"]

# All other top-level folders (skipped, documented here for transparency)
SKIPPED_FOLDERS = [
    "English/",
    "French/",
    "German/",
    "Italian/",
    "Japanese/",
    "Korean/",
    "Russian/",
    "Spanish/",
    "processed/All/",
    "processed/English/",
    "processed/French/",
    "processed/German/",
    "processed/Italian/",
    "processed/Japanese/",
    "processed/Korean/",
    "processed/Russian/",
    "processed/Spanish/",
]


def get_dir_size_mb(path):
    """Return total size of directory in MB."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def download_chinese(dry_run=False):
    """Download only the Chinese portion of GTSinger."""
    from huggingface_hub import snapshot_download

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GTSinger Chinese Subset Downloader")
    print(f"HuggingFace repo: {REPO_ID}")
    print(f"Output:           {OUTPUT_DIR}")
    print("=" * 70)

    print(f"\nFolders to download: {INCLUDE_PREFIXES}")
    print(f"Estimated size:      ~10.7 GB")
    print(f"\nSkipped folders (non-Chinese):")
    for s in SKIPPED_FOLDERS:
        print(f"  - {s}")

    if dry_run:
        # Count files in Chinese folders
        from huggingface_hub import list_repo_tree
        total_size = 0
        total_files = 0
        wav_count = 0
        wav_size = 0
        for prefix in INCLUDE_PREFIXES:
            for f in list_repo_tree(REPO_ID, path_in_repo=prefix.rstrip("/"),
                                    repo_type="dataset", recursive=True):
                size = getattr(f, "size", 0)
                fname = getattr(f, "rfilename", None) or getattr(f, "path", "")
                if size:
                    total_size += size
                    total_files += 1
                    if fname.endswith(".wav"):
                        wav_count += 1
                        wav_size += size
        print(f"\n[DRY RUN] Would download:")
        print(f"  Total files: {total_files:,}")
        print(f"  Total size:  {total_size / 1e9:.2f} GB")
        print(f"  WAV files:   {wav_count:,} ({wav_size / 1e9:.2f} GB)")
        return

    # Use snapshot_download with allow_patterns to download only Chinese files
    # This downloads files matching the prefixes into local_dir
    allow_patterns = [f"{prefix}*" for prefix in INCLUDE_PREFIXES]
    # Also grab top-level doc files
    allow_patterns.extend(["README.md", "dataset_license.md"])

    print(f"\nStarting download...")
    t0 = time.time()

    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=str(OUTPUT_DIR),
        allow_patterns=allow_patterns,
    )

    elapsed = time.time() - t0
    size_mb = get_dir_size_mb(OUTPUT_DIR)
    print(f"\nDownload complete in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"Total on disk: {size_mb:.1f} MB ({size_mb/1024:.2f} GB)")

    # Quick file count summary
    wav_count = 0
    json_count = 0
    tg_count = 0
    xml_count = 0
    for dirpath, _, filenames in os.walk(OUTPUT_DIR):
        for fn in filenames:
            if fn.endswith(".wav"):
                wav_count += 1
            elif fn.endswith(".json"):
                json_count += 1
            elif fn.endswith(".TextGrid"):
                tg_count += 1
            elif fn.endswith(".musicxml"):
                xml_count += 1

    print(f"\nFile counts:")
    print(f"  .wav files:       {wav_count:,}")
    print(f"  .json files:      {json_count:,}")
    print(f"  .TextGrid files:  {tg_count:,}")
    print(f"  .musicxml files:  {xml_count:,}")


def main():
    parser = argparse.ArgumentParser(
        description="Download Chinese portion of GTSinger from HuggingFace")
    parser.add_argument("--dry-run", action="store_true",
                        help="Count files and estimate size without downloading")
    args = parser.parse_args()
    download_chinese(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
