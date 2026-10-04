"""Verify a downloaded file against the released duration and raw Chromaprint fingerprint.
Usage: python verify_download.py AUDIO_FILE ITEM_ID fingerprints.csv [--expected-duration S]
Prints ok / mismatch (duration | fingerprint BER)."""
import argparse, json, subprocess
import pandas as pd


def raw_fp(path):
    r = subprocess.run(["fpcalc", "-raw", "-json", "-length", "120", str(path)], capture_output=True, text=True)
    j = json.loads(r.stdout); return j["fingerprint"], j["duration"]


def ber(a, b, max_off=20):
    best = 1.0
    for off in range(-max_off, max_off + 1):
        pairs = [(a[i], b[i + off]) for i in range(len(a)) if 0 <= i + off < len(b)]
        if len(pairs) >= 50:
            best = min(best, sum(bin((x ^ y) & 0xFFFFFFFF).count("1") for x, y in pairs) / (32 * len(pairs)))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("item_id"); ap.add_argument("fingerprints")
    ap.add_argument("--expected-duration", type=float); ap.add_argument("--max-ber", type=float, default=0.25)
    a = ap.parse_args()
    ref = pd.read_csv(a.fingerprints).set_index("item_id").loc[a.item_id]
    fp, dur = raw_fp(a.audio)
    exp = a.expected_duration or ref.fp_duration_s
    if exp and abs(dur - exp) > 2 and dur < 119:
        print(f"mismatch (duration {dur:.1f} vs {exp:.1f})"); return
    e = ber(fp, json.loads(ref.fingerprint_raw))
    print("ok" if e <= a.max_ber else f"mismatch (fingerprint BER {e:.2f})")


if __name__ == "__main__":
    main()
