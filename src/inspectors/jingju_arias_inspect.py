"""Inspect the Annotated Jingju Arias dataset."""

import os
import re
from collections import Counter

BASE = "/Users/sophiasun/Desktop/2cool4school/2026/aquarius/data/raw/jingju_arias/annotated_jingju_arias_1.0"
ANN_DIR = os.path.join(BASE, "Annotations")


def count_textgrids():
    """Count TextGrid files and categorize by role type and shengqiang."""
    files = sorted(f for f in os.listdir(ANN_DIR) if f.endswith(".TextGrid"))
    role_types = Counter()
    shengqiang_types = Counter()
    for f in files:
        name = f.replace(".TextGrid", "")
        parts = name.split("-")
        role = parts[0]
        sq = parts[1].split("_")[0] if len(parts) > 1 else "unknown"
        role_types[role] += 1
        shengqiang_types[sq] += 1
    return files, role_types, shengqiang_types


def parse_textgrid_tiers(filepath):
    """Extract tier names from a UTF-16 TextGrid."""
    with open(filepath, "rb") as f:
        content = f.read().decode("utf-16")
    tiers = re.findall(r'name = "([^"]+)"', content)
    return tiers


def parse_arias_info():
    """Parse ariasInfo.txt (UTF-16 encoded)."""
    info_path = os.path.join(ANN_DIR, "ariasInfo.txt")
    with open(info_path, "rb") as f:
        content = f.read().decode("utf-16")
    # Count arias by looking for aria entries
    entries = content.strip().split("\n\n")
    entries = [e for e in entries if e.strip()]
    return len(entries)


def parse_tone_melody_subset():
    """Parse Tone-melody_subset.csv."""
    import csv

    csv_path = os.path.join(BASE, "Tone-melody_subset.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    return {"header": rows[0], "entries": len(rows) - 1}


if __name__ == "__main__":
    files, role_types, sq_types = count_textgrids()
    print(f"=== TextGrid Files: {len(files)} ===")
    print(f"\nRole types:")
    for role, count in sorted(role_types.items()):
        print(f"  {role}: {count}")
    print(f"\nShengqiang types:")
    for sq, count in sorted(sq_types.items()):
        print(f"  {sq}: {count}")

    print(f"\n=== TextGrid Tiers ===")
    sample = os.path.join(ANN_DIR, files[0])
    tiers = parse_textgrid_tiers(sample)
    print(f"  Tiers ({len(tiers)}): {tiers}")

    print(f"\n=== ariasInfo.txt ===")
    entry_count = parse_arias_info()
    print(f"  Aria entries: {entry_count}")

    print(f"\n=== Tone-melody_subset.csv ===")
    tm = parse_tone_melody_subset()
    print(f"  Entries: {tm['entries']}")
    print(f"  Header: {tm['header']}")
