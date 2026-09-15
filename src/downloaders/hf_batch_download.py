"""Batch download HuggingFace datasets for Aquarius project.

Downloads:
  1. ErhuPT (Erhu Playing Technique) from ccmusic-database
  2. CNPM (Chinese National Pentatonic Mode) from ccmusic-database
  3. XFID (Xinjiang Folk Instrument Detection) from ccmusic-database
  4. ACE-OpenCpop from espnet

Each dataset is downloaded via load_dataset() + save_to_disk().
Run one at a time to avoid memory issues.

Usage:
    conda activate py312
    python src/downloaders/hf_batch_download.py
    # Or download a single dataset:
    python src/downloaders/hf_batch_download.py erhu
    python src/downloaders/hf_batch_download.py cnpm
    python src/downloaders/hf_batch_download.py xfid
    python src/downloaders/hf_batch_download.py ace
"""
import os
import sys
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASETS = {
    "erhu": {
        "hf_name": "ccmusic-database/erhu_playing_tech",
        "target_dir": "data/raw/erhu_playing_technique",
        "description": "Erhu Playing Technique (ErhuPT)",
    },
    "cnpm": {
        "hf_name": "ccmusic-database/CNPM",
        "target_dir": "data/raw/chinese_national_pentatonic_mode",
        "description": "Chinese National Pentatonic Mode (CNPM)",
    },
    "xfid": {
        # NOTE: XFID is listed on CSMTD website as "available soon" (as of Sep 2026).
        # Not yet on HuggingFace. This entry kept for future use.
        "hf_name": "ccmusic-database/XFID",
        "target_dir": "data/raw/xfid",
        "description": "Xinjiang Folk Instrument Detection (XFID)",
    },
    "ace": {
        "hf_name": "espnet/ace-opencpop-segments",
        "target_dir": "data/raw/ace_opencpop",
        "description": "ACE-OpenCpop (espnet)",
    },
}


def get_dir_size_mb(path):
    """Return total size of directory in MB."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def download_dataset(key, info):
    """Download a single dataset from HuggingFace."""
    target_path = os.path.join(ROOT, info["target_dir"])

    if os.path.exists(target_path) and os.listdir(target_path):
        size_mb = get_dir_size_mb(target_path)
        print(f"  Skipping {info['description']} -- already exists at {info['target_dir']} ({size_mb:.1f} MB)")
        return True

    print(f"\n{'='*60}")
    print(f"  Downloading: {info['description']}")
    print(f"  HF repo:     {info['hf_name']}")
    print(f"  Target:       {info['target_dir']}")
    print(f"{'='*60}")

    os.makedirs(target_path, exist_ok=True)

    # Try load_dataset first (preferred -- gets structured data)
    try:
        from datasets import load_dataset
        print(f"  Loading via datasets.load_dataset('{info['hf_name']}')...")
        # Try without trust_remote_code first (newer datasets library versions
        # don't support it). Fall back to with it for older versions / repos
        # that need a loading script.
        try:
            ds = load_dataset(info["hf_name"])
        except Exception:
            ds = load_dataset(info["hf_name"], trust_remote_code=True)
        print(f"  Dataset loaded. Splits: {list(ds.keys()) if hasattr(ds, 'keys') else 'single'}")
        if hasattr(ds, 'keys'):
            for split_name, split_ds in ds.items():
                print(f"    {split_name}: {len(split_ds)} rows, columns: {split_ds.column_names}")
        ds.save_to_disk(target_path)
        size_mb = get_dir_size_mb(target_path)
        print(f"  Saved to {target_path} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  load_dataset failed: {e}")
        print(f"  Trying huggingface_hub snapshot_download as fallback...")

    # Fallback: snapshot_download
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=info["hf_name"],
            repo_type="dataset",
            local_dir=target_path,
        )
        size_mb = get_dir_size_mb(target_path)
        print(f"  Snapshot downloaded to {target_path} ({size_mb:.1f} MB)")
        return True
    except Exception as e2:
        print(f"  Snapshot download also failed: {e2}")
        # Clean up empty directory
        if os.path.exists(target_path) and not os.listdir(target_path):
            os.rmdir(target_path)
        return False


def main():
    # Determine which datasets to download
    if len(sys.argv) > 1:
        keys = [k for k in sys.argv[1:] if k in DATASETS]
        if not keys:
            print(f"Unknown dataset key(s): {sys.argv[1:]}")
            print(f"Available: {list(DATASETS.keys())}")
            sys.exit(1)
    else:
        keys = list(DATASETS.keys())

    print(f"Aquarius HF Batch Downloader")
    print(f"Datasets to download: {keys}")
    print()

    results = {}
    for key in keys:
        info = DATASETS[key]
        success = download_dataset(key, info)
        results[key] = "OK" if success else "FAILED"

    print(f"\n{'='*60}")
    print("Summary:")
    for key, status in results.items():
        print(f"  {DATASETS[key]['description']}: {status}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
