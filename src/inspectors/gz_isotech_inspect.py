#!/usr/bin/env python3
"""Inspect GZ_IsoTech (Guzheng Isolated Techniques) dataset.

HuggingFace Arrow format, downloaded via save_to_disk().
Two configs: default (audio + mel + labels) and eval (spectrograms + labels).

Requirements:
    pip install datasets numpy soundfile
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf
from datasets import load_from_disk


DATA_ROOT = Path("data/raw/gz_isotech")


def get_audio_stats_from_arrow(ds, n_samples=200):
    """Get audio duration stats by reading raw bytes from Arrow table."""
    table = ds.data
    if "audio" not in table.column_names:
        return None

    audio_col = table.column("audio")
    n = min(n_samples, len(audio_col))
    indices = np.linspace(0, len(audio_col) - 1, n, dtype=int)

    durations = []
    sample_rates = set()
    channels_set = set()
    for idx in indices:
        item = audio_col[int(idx)].as_py()
        audio_bytes = item["bytes"]
        buf = io.BytesIO(audio_bytes)
        data, sr = sf.read(buf)
        duration = len(data) / sr if data.ndim == 1 else data.shape[0] / sr
        durations.append(duration)
        sample_rates.add(sr)
        channels_set.add(1 if data.ndim == 1 else data.shape[1])

    return {
        "sample_rates": sorted(sample_rates),
        "channels": sorted(channels_set),
        "n_sampled": len(durations),
        "duration_min_s": round(min(durations), 3),
        "duration_max_s": round(max(durations), 3),
        "duration_mean_s": round(np.mean(durations), 3),
        "duration_median_s": round(float(np.median(durations)), 3),
        "duration_std_s": round(np.std(durations), 3),
        "total_estimated_minutes": round(np.mean(durations) * len(ds) / 60, 2),
    }


def inspect_split(ds, split_name, sample_audio=True, n_audio_samples=200):
    """Inspect a single split of the dataset."""
    info = {
        "split": split_name,
        "num_examples": len(ds),
        "features": {k: str(v) for k, v in ds.features.items()},
        "column_names": ds.column_names,
    }

    # Label distribution (use select_columns to avoid audio decoding)
    if "label" in ds.column_names:
        label_feature = ds.features["label"]
        if hasattr(label_feature, "names"):
            labels_ds = ds.select_columns(["label"])
            labels = labels_ds["label"]
            counter = Counter(labels)
            info["num_classes"] = len(label_feature.names)
            info["label_names"] = label_feature.names
            info["label_distribution"] = [
                {"label_id": lid, "name": label_feature.names[lid], "count": cnt,
                 "percent": round(cnt / len(ds) * 100, 1)}
                for lid, cnt in sorted(counter.items())
            ]
            counts = list(counter.values())
            info["label_stats"] = {
                "min_count": min(counts),
                "max_count": max(counts),
                "mean_count": round(np.mean(counts), 1),
                "std_count": round(np.std(counts), 1),
                "imbalance_ratio": round(max(counts) / min(counts), 2),
            }

    # Text fields
    for col in ["name", "cname", "pinyin"]:
        if col in ds.column_names:
            text_ds = ds.select_columns([col])
            vals = text_ds[col]
            unique_vals = sorted(set(vals))
            info[f"{col}_unique_count"] = len(unique_vals)
            info[f"{col}_samples"] = unique_vals[:15]

    # Audio properties
    if sample_audio and "audio" in ds.column_names:
        print(f"  Sampling audio for stats...")
        audio_stats = get_audio_stats_from_arrow(ds, n_audio_samples)
        if audio_stats:
            info["audio_stats"] = audio_stats
            print(f"    Duration: {audio_stats['duration_min_s']:.3f}s - {audio_stats['duration_max_s']:.3f}s "
                  f"(mean {audio_stats['duration_mean_s']:.3f}s)")
            print(f"    Sample rates: {audio_stats['sample_rates']}")
            print(f"    Est. total: {audio_stats['total_estimated_minutes']:.1f} min")

    return info


def main():
    results = {"dataset": "GZ_IsoTech", "configs": {}}

    # --- Default config ---
    print("=== GZ_IsoTech default config ===")
    default_path = DATA_ROOT / "default"
    ds_default = load_from_disk(str(default_path))
    print(f"  Loaded: {ds_default}")

    config_info = {"splits": {}}
    if hasattr(ds_default, "keys"):
        for split_name in ds_default:
            print(f"\n  --- Split: {split_name} ({len(ds_default[split_name])} examples) ---")
            split_info = inspect_split(ds_default[split_name], split_name, sample_audio=True)
            config_info["splits"][split_name] = split_info
    else:
        split_info = inspect_split(ds_default, "train", sample_audio=True)
        config_info["splits"]["train"] = split_info

    results["configs"]["default"] = config_info

    # --- Eval config ---
    print("\n=== GZ_IsoTech eval config ===")
    eval_path = DATA_ROOT / "eval"
    ds_eval = load_from_disk(str(eval_path))
    print(f"  Loaded: {ds_eval}")

    config_info = {"splits": {}}
    if hasattr(ds_eval, "keys"):
        for split_name in ds_eval:
            print(f"\n  --- Split: {split_name} ({len(ds_eval[split_name])} examples) ---")
            split_info = inspect_split(ds_eval[split_name], split_name, sample_audio=False)
            config_info["splits"][split_name] = split_info
    else:
        split_info = inspect_split(ds_eval, "train", sample_audio=False)
        config_info["splits"]["train"] = split_info

    results["configs"]["eval"] = config_info

    # --- Summary ---
    print("\n" + "=" * 60)
    print("GZ_ISOTECH INSPECTION SUMMARY")
    print("=" * 60)
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

    return results


if __name__ == "__main__":
    main()
