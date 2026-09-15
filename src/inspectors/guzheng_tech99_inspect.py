#!/usr/bin/env python3
"""Inspect Guzheng_Tech99 (Guzheng Techniques 99 songs) dataset.

HuggingFace Arrow format, downloaded via save_to_disk().
Two configs:
  - default: audio + mel + frame-level labels (99 compositions)
  - eval: pre-computed spectrograms + frame-level labels (windowed segments)

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


DATA_ROOT = Path("data/raw/guzheng_tech99")

TECHNIQUE_NAMES = [
    "chanyin (Vibrato)",
    "boxian (Plucks)",
    "shanghua (Upward Portamento)",
    "xiahua (Downward Portamento)",
    "huazhi/guazou/lianmo/liantuo (Glissando)",
    "yaozhi (Tremolo)",
    "dianyin (Point Note)",
]


def get_audio_stats_from_arrow(ds, n_samples=50):
    """Get audio duration stats by reading raw bytes from Arrow table."""
    table = ds.data
    if "audio" not in table.column_names:
        return None

    audio_col = table.column("audio")
    n = min(n_samples, len(audio_col))
    indices = np.linspace(0, len(audio_col) - 1, n, dtype=int)

    durations = []
    sample_rates = set()
    for idx in indices:
        item = audio_col[int(idx)].as_py()
        audio_bytes = item["bytes"]
        buf = io.BytesIO(audio_bytes)
        data, sr = sf.read(buf)
        duration = len(data) / sr if data.ndim == 1 else data.shape[0] / sr
        durations.append(duration)
        sample_rates.add(sr)

    return {
        "sample_rates": sorted(sample_rates),
        "n_sampled": len(durations),
        "duration_min_s": round(min(durations), 2),
        "duration_max_s": round(max(durations), 2),
        "duration_mean_s": round(np.mean(durations), 2),
        "duration_median_s": round(float(np.median(durations)), 2),
        "duration_std_s": round(np.std(durations), 2),
        "total_estimated_minutes": round(np.mean(durations) * len(ds) / 60, 2),
    }


def inspect_default_split(ds, split_name, n_audio_samples=50):
    """Inspect a split from the default config (has audio + sequence labels)."""
    info = {
        "split": split_name,
        "num_examples": len(ds),
        "features": {k: str(v) for k, v in ds.features.items()},
        "column_names": ds.column_names,
    }

    # Label analysis — use select_columns to avoid loading audio
    if "label" in ds.column_names:
        label_feature = ds.features["label"]
        info["label_structure"] = str(label_feature)

        # Read label column only
        label_ds = ds.select_columns(["label"])

        total_annotations = 0
        technique_counter = Counter()
        note_values = []
        onset_offsets = []
        annotations_per_item = []

        for i in range(len(label_ds)):
            item = label_ds[i]
            labels = item["label"]

            if isinstance(labels, dict):
                n_annot = len(labels["onset_time"])
                annotations_per_item.append(n_annot)
                total_annotations += n_annot
                for ipt_val in labels["IPT"]:
                    technique_counter[ipt_val] += 1
                note_values.extend(labels["note"])
                for j in range(n_annot):
                    onset_offsets.append(
                        (labels["onset_time"][j], labels["offset_time"][j])
                    )
            elif isinstance(labels, list):
                n_annot = len(labels)
                annotations_per_item.append(n_annot)
                total_annotations += n_annot
                for ann in labels:
                    technique_counter[ann["IPT"]] += 1
                    note_values.append(ann["note"])
                    onset_offsets.append((ann["onset_time"], ann["offset_time"]))

        info["annotation_stats"] = {
            "total_annotations": total_annotations,
            "mean_annotations_per_item": round(total_annotations / len(ds), 1),
            "min_annotations_per_item": min(annotations_per_item) if annotations_per_item else 0,
            "max_annotations_per_item": max(annotations_per_item) if annotations_per_item else 0,
            "technique_distribution": [
                {
                    "id": tid,
                    "name": TECHNIQUE_NAMES[tid] if tid < len(TECHNIQUE_NAMES) else f"unknown_{tid}",
                    "count": cnt,
                    "percent": round(cnt / total_annotations * 100, 2),
                }
                for tid, cnt in sorted(technique_counter.items())
            ],
        }

        # Note (pitch) stats
        if note_values:
            note_arr = np.array(note_values, dtype=int)
            info["note_stats"] = {
                "min_midi": int(note_arr.min()),
                "max_midi": int(note_arr.max()),
                "mean_midi": round(float(note_arr.mean()), 1),
                "unique_pitches": len(set(note_values)),
            }

        # Duration of individual annotations
        if onset_offsets:
            annot_durs = [off - on for on, off in onset_offsets]
            info["annotation_duration_stats"] = {
                "min_s": round(min(annot_durs), 3),
                "max_s": round(max(annot_durs), 3),
                "mean_s": round(np.mean(annot_durs), 3),
                "median_s": round(float(np.median(annot_durs)), 3),
            }

    # Audio properties
    if "audio" in ds.column_names:
        print(f"  Sampling audio for stats...")
        audio_stats = get_audio_stats_from_arrow(ds, n_audio_samples)
        if audio_stats:
            info["audio_stats"] = audio_stats
            print(f"    Duration: {audio_stats['duration_min_s']:.2f}s - {audio_stats['duration_max_s']:.2f}s "
                  f"(mean {audio_stats['duration_mean_s']:.2f}s)")
            print(f"    Sample rates: {audio_stats['sample_rates']}")
            print(f"    Est. total: {audio_stats['total_estimated_minutes']:.1f} min")

    return info


def inspect_eval_split(ds, split_name):
    """Inspect a split from the eval config (pre-computed features)."""
    info = {
        "split": split_name,
        "num_examples": len(ds),
        "features": {k: str(v) for k, v in ds.features.items()},
        "column_names": ds.column_names,
    }

    # Check shapes from first item
    if len(ds) > 0:
        item = ds[0]
        shapes = {}
        for col in ds.column_names:
            val = item[col]
            if isinstance(val, np.ndarray):
                shapes[col] = list(val.shape)
            elif hasattr(val, "shape"):
                shapes[col] = list(val.shape)
        info["feature_shapes"] = shapes

    # Label distribution for eval (frame-level: label is Array2D [7, 258])
    if "label" in ds.column_names:
        n_check = min(50, len(ds))
        technique_frame_counts = np.zeros(7)
        total_frames = 0
        for i in range(n_check):
            label_arr = np.array(ds[i]["label"])
            active = (label_arr > 0.5).sum(axis=1)
            technique_frame_counts += active
            total_frames += label_arr.shape[1]

        info["eval_label_stats"] = {
            "label_shape": list(np.array(ds[0]["label"]).shape),
            "n_sampled": n_check,
            "total_frames_sampled": int(total_frames),
            "technique_frame_proportions": [
                {
                    "id": i,
                    "name": TECHNIQUE_NAMES[i] if i < len(TECHNIQUE_NAMES) else f"unknown_{i}",
                    "active_frames": int(technique_frame_counts[i]),
                    "percent_of_frames": round(
                        technique_frame_counts[i] / total_frames * 100, 2
                    ),
                }
                for i in range(7)
            ],
        }

    return info


def main():
    results = {"dataset": "Guzheng_Tech99", "configs": {}}

    # --- Default config ---
    print("=== Guzheng_Tech99 default config ===")
    default_path = DATA_ROOT / "default"
    ds_default = load_from_disk(str(default_path))
    print(f"  Loaded: {ds_default}")

    config_info = {"splits": {}}
    if hasattr(ds_default, "keys"):
        for split_name in ds_default:
            print(f"\n  --- Split: {split_name} ({len(ds_default[split_name])} examples) ---")
            split_info = inspect_default_split(ds_default[split_name], split_name)
            config_info["splits"][split_name] = split_info
    else:
        split_info = inspect_default_split(ds_default, "train")
        config_info["splits"]["train"] = split_info

    results["configs"]["default"] = config_info

    # --- Eval config ---
    print("\n=== Guzheng_Tech99 eval config ===")
    eval_path = DATA_ROOT / "eval"
    ds_eval = load_from_disk(str(eval_path))
    print(f"  Loaded: {ds_eval}")

    config_info = {"splits": {}}
    if hasattr(ds_eval, "keys"):
        for split_name in ds_eval:
            print(f"\n  --- Split: {split_name} ({len(ds_eval[split_name])} examples) ---")
            split_info = inspect_eval_split(ds_eval[split_name], split_name)
            config_info["splits"][split_name] = split_info
    else:
        split_info = inspect_eval_split(ds_eval, "train")
        config_info["splits"]["train"] = split_info

    results["configs"]["eval"] = config_info

    # --- Summary ---
    print("\n" + "=" * 60)
    print("GUZHENG_TECH99 INSPECTION SUMMARY")
    print("=" * 60)
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

    return results


if __name__ == "__main__":
    main()
