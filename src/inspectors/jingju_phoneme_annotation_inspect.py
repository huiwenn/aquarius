"""Inspect the Jingju Phoneme Annotation dataset."""

import csv
import os

BASE = "/Users/sophiasun/Desktop/2cool4school/2026/aquarius/data/raw/jingju_phoneme_annotation"


def count_textgrids():
    """Count TextGrid files per role type."""
    results = {}
    for role_dir in ["dan", "laosheng"]:
        full_dir = os.path.join(BASE, role_dir)
        files = sorted(f for f in os.listdir(full_dir) if f.endswith(".TextGrid"))
        results[role_dir] = {"count": len(files), "files": files}
    return results


def inspect_catalogues():
    """Parse catalogue CSVs."""
    results = {}
    for cat_file in ["catalogue - dan.csv", "catalogue - laosheng.csv"]:
        path = os.path.join(BASE, cat_file)
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        annotated = sum(
            1 for r in rows if r.get("Phonetically annotated", "").strip() == "*"
        )
        results[cat_file] = {
            "total": len(rows),
            "phonetically_annotated": annotated,
            "columns": list(rows[0].keys()) if rows else [],
        }
    return results


def inspect_textgrid_tiers(filepath):
    """Parse a UTF-16 TextGrid to extract tier names."""
    with open(filepath, "rb") as f:
        content = f.read().decode("utf-16")
    import re

    tiers = re.findall(r'name = "([^"]+)"', content)
    return tiers


if __name__ == "__main__":
    print("=== TextGrid Files ===")
    tg_results = count_textgrids()
    for role, info in tg_results.items():
        print(f"  {role}: {info['count']} TextGrids")

    print("\n=== Catalogues ===")
    cat_results = inspect_catalogues()
    for cat, info in cat_results.items():
        print(
            f"  {cat}: {info['total']} entries, "
            f"{info['phonetically_annotated']} phonetically annotated"
        )
        print(f"    columns: {info['columns']}")

    print("\n=== Sample TextGrid Tiers ===")
    sample = os.path.join(BASE, "dan", tg_results["dan"]["files"][0])
    tiers = inspect_textgrid_tiers(sample)
    print(f"  Tiers ({len(tiers)}): {tiers}")
