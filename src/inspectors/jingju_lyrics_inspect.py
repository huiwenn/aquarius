"""Inspect the Jingju Lyrics dataset."""

import os
from collections import Counter

BASE = "/Users/sophiasun/Desktop/2cool4school/2026/aquarius/data/raw/jingju_lyrics/jingju_lyrics_1.0"


def count_files_per_dir():
    """Count files in each subdirectory."""
    results = {}
    for subdir in ["plbs", "plsqbs", "bs4_all_docs", "sqbs7_all_docs"]:
        full_dir = os.path.join(BASE, subdir)
        files = [
            f
            for f in os.listdir(full_dir)
            if os.path.isfile(os.path.join(full_dir, f)) and f != ".DS_Store"
        ]
        results[subdir] = len(files)
    return results


def analyze_plbs():
    """Analyze banshi (metrical pattern) distribution in plbs directory."""
    plbs_dir = os.path.join(BASE, "plbs")
    files = [f for f in os.listdir(plbs_dir) if f.endswith(".txt")]
    banshi = Counter()
    for f in files:
        parts = f.split("_")
        if len(parts) >= 2:
            banshi[parts[0]] += 1
    return banshi


def analyze_plsqbs():
    """Analyze shengqiang-banshi distribution in plsqbs directory."""
    plsqbs_dir = os.path.join(BASE, "plsqbs")
    files = [f for f in os.listdir(plsqbs_dir) if f.endswith(".txt")]
    sqbs = Counter()
    for f in files:
        parts = f.split("_")
        if len(parts) >= 2:
            sqbs[parts[0]] += 1
    return sqbs


def analyze_sqbs7():
    """Analyze sqbs7_all_docs: aggregated lyrics by shengqiang-banshi type."""
    sqbs_dir = os.path.join(BASE, "sqbs7_all_docs")
    results = {}
    for f in sorted(os.listdir(sqbs_dir)):
        if f.endswith(".txt"):
            path = os.path.join(sqbs_dir, f)
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            results[f.replace(".txt", "")] = len(lines)
    return results


if __name__ == "__main__":
    print("=== File Counts ===")
    counts = count_files_per_dir()
    for subdir, count in counts.items():
        print(f"  {subdir}: {count} files")

    print(f"\n=== plbs: Banshi Distribution ===")
    banshi = analyze_plbs()
    for b, count in banshi.most_common():
        print(f"  {b}: {count}")

    print(f"\n=== plsqbs: Shengqiang-Banshi Distribution ===")
    sqbs = analyze_plsqbs()
    for sq, count in sqbs.most_common():
        print(f"  {sq}: {count}")

    print(f"\n=== sqbs7_all_docs: Lines per Type ===")
    sqbs7 = analyze_sqbs7()
    for sq, lines in sqbs7.items():
        print(f"  {sq}: {lines} lines")
