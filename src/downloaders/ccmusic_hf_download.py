"""Download CCMusic datasets from HuggingFace."""
import subprocess
import sys
import os

DATASETS = {
    "ccmusic-database/CTIS": "data/raw/ctis",
    "ccmusic-database/GZ_IsoTech": "data/raw/gz_isotech",
    "ccmusic-database/Guzheng_Tech99": "data/raw/guzheng_tech99",
}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for ds_name, target_dir in DATASETS.items():
    target_path = os.path.join(ROOT, target_dir)
    if os.path.exists(target_path) and os.listdir(target_path):
        print(f"Skipping {ds_name} — already exists at {target_dir}")
        continue
    print(f"\nDownloading {ds_name} to {target_dir}...")
    os.makedirs(target_path, exist_ok=True)
    try:
        from datasets import load_dataset
        ds = load_dataset(ds_name, trust_remote_code=True)
        ds.save_to_disk(target_path)
        print(f"Saved {ds_name} to {target_path}")
    except Exception as e:
        print(f"Error downloading {ds_name}: {e}")
        print("Trying huggingface_hub snapshot download...")
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=ds_name,
                repo_type="dataset",
                local_dir=target_path,
            )
            print(f"Snapshot downloaded to {target_path}")
        except Exception as e2:
            print(f"Snapshot also failed: {e2}")
