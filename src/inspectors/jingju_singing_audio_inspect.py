"""Inspect the Jingju A Cappella Singing Audio dataset."""

import wave
import csv
import os
from collections import Counter

BASE = "/Users/sophiasun/Desktop/2cool4school/2026/aquarius/data/raw/jingju_singing_audio"
WAV_DIR = os.path.join(BASE, "wav_left")
TG_DIR = os.path.join(BASE, "textgrid")


def inspect_wavs():
    """Count WAV files and extract audio properties."""
    results = {}
    for role_dir in ["danAll", "laosheng"]:
        full_dir = os.path.join(WAV_DIR, role_dir)
        files = sorted(f for f in os.listdir(full_dir) if f.endswith(".wav"))
        durations = []
        sample_rates = set()
        channels = set()
        for f in files:
            with wave.open(os.path.join(full_dir, f), "r") as w:
                sr = w.getframerate()
                ch = w.getnchannels()
                dur = w.getnframes() / sr
                sample_rates.add(sr)
                channels.add(ch)
                durations.append(dur)
        results[role_dir] = {
            "count": len(files),
            "total_duration_s": sum(durations),
            "avg_duration_s": sum(durations) / len(durations) if durations else 0,
            "sample_rates": sample_rates,
            "channels": channels,
        }
    return results


def inspect_textgrids():
    """Count TextGrid files per role type."""
    results = {}
    for role_dir in ["danAll", "laosheng"]:
        full_dir = os.path.join(TG_DIR, role_dir)
        files = [f for f in os.listdir(full_dir) if f.endswith(".TextGrid")]
        results[role_dir] = len(files)
    return results


def inspect_catalogues():
    """Parse catalogue CSVs."""
    results = {}
    for cat_file in ["catalogue_dan.csv", "catalogue_laosheng.csv"]:
        path = os.path.join(BASE, cat_file)
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        annotated = sum(1 for r in rows if r.get("Phonetically annotated", "").strip() == "*")
        results[cat_file] = {
            "total": len(rows),
            "phonetically_annotated": annotated,
            "columns": list(rows[0].keys()) if rows else [],
        }
    return results


if __name__ == "__main__":
    print("=== WAV Files ===")
    wav_results = inspect_wavs()
    total_files = 0
    total_dur = 0
    for role, info in wav_results.items():
        print(f"  {role}: {info['count']} files, "
              f"total {info['total_duration_s']:.1f}s, "
              f"avg {info['avg_duration_s']:.1f}s, "
              f"SR: {info['sample_rates']}, "
              f"channels: {info['channels']}")
        total_files += info["count"]
        total_dur += info["total_duration_s"]
    print(f"  TOTAL: {total_files} files, {total_dur:.1f}s ({total_dur/3600:.2f} hours)")

    print("\n=== TextGrid Files ===")
    tg_results = inspect_textgrids()
    for role, count in tg_results.items():
        print(f"  {role}: {count} TextGrids")

    print("\n=== Catalogues ===")
    cat_results = inspect_catalogues()
    for cat, info in cat_results.items():
        print(f"  {cat}: {info['total']} entries, "
              f"{info['phonetically_annotated']} phonetically annotated")
        print(f"    columns: {info['columns']}")
