"""Per-group stage counts and fallback rates: catches pipeline bugs that look like data.
Usage: python stage_report.py ROOT_DIR [--groups-from audio] [--stage NAME=GLOB ...] [--fallback NAME]
Default stages assume ROOT/{audio,vocals,midi/<model>}/<group>/<id>.*  Example:
  python stage_report.py data/transcription --stage vocals=vocals --stage game=midi/game --stage rosvot=midi/rosvot \
      --stage fallback=midi/yourmt3 --fallback fallback
Flags groups where a stage is incomplete or the fallback rate exceeds --max-fallback (default 0.10)."""
import argparse
from pathlib import Path
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--groups-from", default="audio")
    ap.add_argument("--stage", action="append", default=[]); ap.add_argument("--fallback")
    ap.add_argument("--max-fallback", type=float, default=0.10)
    a = ap.parse_args()
    root = Path(a.root)
    stages = dict(s.split("=", 1) for s in a.stage) or {"vocals": "vocals"}
    rows = []
    for g in sorted(p.name for p in (root / a.groups_from).iterdir() if p.is_dir()):
        n = len([f for f in (root / a.groups_from / g).iterdir() if not f.name.startswith(("_", "."))])
        row = {"group": g, "inputs": n}
        for k, sub in stages.items():
            d = root / sub / g
            row[k] = len([f for f in d.iterdir() if not f.name.startswith(("_", "."))]) if d.exists() else 0
        rows.append(row)
    df = pd.DataFrame(rows)
    flags = []
    for k in stages:
        if k != a.fallback:
            bad = df[df[k] < df.inputs]
            flags += [f"{r.group}: {k} {r[k]}/{r.inputs}" for _, r in bad.iterrows()]
    if a.fallback:
        df["fallback_rate"] = (df[a.fallback] / df.inputs.clip(lower=1)).round(3)
        flags += [f"{r.group}: fallback rate {r.fallback_rate:.0%} — likely a pipeline bug" for _, r in
                  df[df.fallback_rate > a.max_fallback].iterrows()]
    print(df.to_string(index=False))
    print("\nFLAGS:" if flags else "\nno flags", *flags, sep="\n  ")


if __name__ == "__main__":
    main()
