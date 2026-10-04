"""
Chromaprint fingerprints (first 120 s) of every downloaded recording, released so that users can verify that a
re-downloaded file is the same audio (fpcalc; compare with chromaprint/acoustid similarity, e.g. bit error rate).

Output: data/colour_regions/fingerprints.csv      (item_id, fp_duration_s, fingerprint) — compressed (AcoustID form)
        data/colour_regions/fingerprints_raw.csv  (item_id, fingerprint_raw) — JSON list of 32-bit ints, used by
        download_release.py for a bit-error-rate check. Both cached, resumable.
Run (py312, needs `fpcalc`, e.g. `brew install chromaprint`): python src/colour_regions/fingerprints.py
"""

import json
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "colour_regions" / "fingerprints.csv"


def main() -> None:
    paths = {}
    for man, idc in ((ROOT / "data" / "regions_audio" / "manifest.csv", "video_id"),
                     (ROOT / "data" / "regions_v2" / "manifest.csv", "id")):
        m = pd.read_csv(man)
        m = m[m.status == "ok"]
        paths.update(dict(zip(m[idc], m.audio_path)))
    done = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=["item_id"])
    rows = done.to_dict("records")
    for i, (item, p) in enumerate(sorted(paths.items()), 1):
        if item in set(done.item_id):
            continue
        r = subprocess.run(["fpcalc", "-json", "-length", "120", str(ROOT / p)], capture_output=True, text=True)
        try:
            j = json.loads(r.stdout)
            rows.append(dict(item_id=item, fp_duration_s=j["duration"], fingerprint=j["fingerprint"]))
        except (json.JSONDecodeError, KeyError):
            rows.append(dict(item_id=item, fp_duration_s=None, fingerprint=None))
        if i % 100 == 0:
            pd.DataFrame(rows).to_csv(OUT, index=False)
            print(i, flush=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print("fingerprints:", sum(r["fingerprint"] is not None for r in rows), "of", len(rows))
    raw_out = OUT.with_name("fingerprints_raw.csv")
    raw = pd.read_csv(raw_out) if raw_out.exists() else pd.DataFrame(columns=["item_id"])
    raw_rows = raw.to_dict("records")
    for item, p in sorted(paths.items()):
        if item in set(raw.item_id):
            continue
        r = subprocess.run(["fpcalc", "-raw", "-json", "-length", "120", str(ROOT / p)], capture_output=True, text=True)
        try:
            raw_rows.append(dict(item_id=item, fingerprint_raw=json.dumps(json.loads(r.stdout)["fingerprint"])))
        except (json.JSONDecodeError, KeyError):
            raw_rows.append(dict(item_id=item, fingerprint_raw=None))
    pd.DataFrame(raw_rows).to_csv(raw_out, index=False)
    print("raw fingerprints:", len(raw_rows))


if __name__ == "__main__":
    main()
