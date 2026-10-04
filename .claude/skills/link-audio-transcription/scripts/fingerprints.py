"""Chromaprint fingerprints (first 120 s) of downloaded files, for verifying users' re-downloads.
Writes compressed (AcoustID form) and raw (JSON list of 32-bit ints) fingerprints. Resumable. Needs `fpcalc`.
Usage: python fingerprints.py manifest.csv fingerprints.csv     (manifest columns: item_id, audio_path)"""
import json, subprocess, sys
from pathlib import Path
import pandas as pd


def fp(path, raw):
    r = subprocess.run(["fpcalc", "-json", "-length", "120"] + (["-raw"] if raw else []) + [str(path)],
                       capture_output=True, text=True)
    try:
        j = json.loads(r.stdout); return j["duration"], j["fingerprint"]
    except (json.JSONDecodeError, KeyError):
        return None, None


def main():
    man, out = pd.read_csv(sys.argv[1]), Path(sys.argv[2])
    done = pd.read_csv(out) if out.exists() else pd.DataFrame(columns=["item_id"])
    rows = done.to_dict("records")
    for r in man.itertuples():
        if r.item_id in set(done.item_id) or not isinstance(r.audio_path, str):
            continue
        d, comp = fp(r.audio_path, False); _, raw = fp(r.audio_path, True)
        rows.append(dict(item_id=r.item_id, fp_duration_s=d, fingerprint=comp, fingerprint_raw=json.dumps(raw) if raw else None))
        if len(rows) % 100 == 0:
            pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(len(rows), "fingerprints")


if __name__ == "__main__":
    main()
