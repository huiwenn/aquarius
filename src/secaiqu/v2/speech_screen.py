"""
Speech screen for collected recordings: how much of each recording is talk (narration, interviews,
news voice-over) rather than singing or instrumental music.

Why not pitch: a pitch-plateau / voiced-run heuristic on the separated vocals flags speech-like *singing*
too (narrative singing 太和清音, 木鱼歌, recited 童谣, 打鼓歌) — dropping those would bias the test set
against recitative genres. An AudioSet classifier separates "Speech / Narration" from "Singing / Music"
directly, and runs on the full mix (no separation needed).

Model: MIT/ast-finetuned-audioset-10-10-0.4593 (Audio Spectrogram Transformer, AudioSet 527 classes).
Per 10 s window (hop 10 s) we keep sigmoid scores for the classes in KEEP.

Output: <out>/windows/<region>/<id>.npz  (probs [n_win, len(KEEP)], classes, win_s)
        <out>/speech_screen.csv          per-item summary (see summarize())
Run (regionclf env, arm64, MPS; pip install librosa):
  ~/miniforge3/envs/regionclf/bin/python src/secaiqu/v2/speech_screen.py \
      --manifest data/regions_v2/manifest.csv --out data/regions_v2/speech_screen
"""

import argparse
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
MODEL = "MIT/ast-finetuned-audioset-10-10-0.4593"
SR, WIN_S = 16000, 10.0
KEEP = ["Speech", "Male speech, man speaking", "Female speech, woman speaking", "Child speech, kid speaking",
        "Conversation", "Narration, monologue", "Speech synthesizer",
        "Singing", "Male singing", "Female singing", "Child singing", "Choir", "Chant", "Yodeling",
        "Music", "Musical instrument", "Silence"]
SPEECH = KEEP[:7]
SINGING = ["Singing", "Male singing", "Female singing", "Child singing", "Choir", "Chant", "Yodeling"]


def load(path: Path) -> np.ndarray:
    """Decode any container yt-dlp produces (m4a/webm/opus/mp3) to 16 kHz mono via ffmpeg.
    (librosa/audioread fails on some Bilibili m4a files.)"""
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def classify(paths: list[tuple[Path, Path]], batch: int = 16) -> None:
    import torch
    from transformers import ASTFeatureExtractor, ASTForAudioClassification

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    fe = ASTFeatureExtractor.from_pretrained(MODEL)
    model = ASTForAudioClassification.from_pretrained(MODEL).to(dev).eval()
    idx = [model.config.label2id[c] for c in KEEP]
    for i, (audio, out) in enumerate(paths, 1):
        try:
            y = load(audio)
        except subprocess.CalledProcessError as e:
            print(f"[{i}/{len(paths)}] FAILED {audio}: {e.stderr.decode()[:200]}", flush=True)
            continue
        n = int(SR * WIN_S)
        wins = [y[s: s + n] for s in range(0, max(len(y) - n // 2, 1), n)]  # drop a trailing stub < 5 s
        probs = []
        for b in range(0, len(wins), batch):
            x = fe(wins[b: b + batch], sampling_rate=SR, return_tensors="pt")["input_values"].to(dev)
            with torch.no_grad():
                probs.append(torch.sigmoid(model(x).logits)[:, idx].float().cpu().numpy())
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(out, probs=np.concatenate(probs), classes=np.array(KEEP), win_s=WIN_S)
        print(f"[{i}/{len(paths)}] {audio.name} {len(wins)} windows", flush=True)


def window_labels(p: np.ndarray) -> np.ndarray:
    """Per window: 'speech' if talk dominates, 'sung' if singing, 'music' if instrumental, 'silence', else 'other'.
    Thresholds are provisional; calibrated against v1 (curated singing) and TTS speech, see docs/collection_v2.md."""
    c = {k: j for j, k in enumerate(KEEP)}
    sp = p[:, [c[k] for k in SPEECH]].max(1)
    sg = p[:, [c[k] for k in SINGING]].max(1)
    mu = p[:, c["Music"]]
    lab = np.full(len(p), "other", dtype=object)
    lab[mu >= 0.3] = "music"
    lab[sg >= 0.2] = "sung"
    lab[(sp >= 0.5) & (sp > 2 * sg) & (mu < 0.5)] = "speech"
    lab[p[:, c["Silence"]] >= 0.5] = "silence"
    return lab


def summarize(win_dir: Path, ids: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in ids.itertuples():
        f = win_dir / r.region / f"{r.id}.npz"
        if not f.exists():
            continue
        p = np.load(f)["probs"]
        lab = window_labels(p)
        c = {k: j for j, k in enumerate(KEEP)}
        rows.append(dict(region=r.region, id=r.id, n_win=len(p),
                         speech_share=(lab == "speech").mean(), sung_share=(lab == "sung").mean(),
                         music_share=(lab == "music").mean(),
                         speech_mean=p[:, [c[k] for k in SPEECH]].max(1).mean(),
                         singing_mean=p[:, [c[k] for k in SINGING]].max(1).mean()))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--id-col", default="id", help="v1 manifest uses video_id")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()
    out = ROOT / args.out
    df = pd.read_csv(ROOT / args.manifest)
    df = df[df.status == "ok"].rename(columns={args.id_col: "id"})
    if not args.summary_only:
        todo = [(ROOT / r.audio_path, out / "windows" / r.region / f"{r.id}.npz") for r in df.itertuples()]
        classify([t for t in todo if not t[1].exists()])
    s = summarize(out / "windows", df)
    s.to_csv(out / "speech_screen.csv", index=False)
    print(s.describe().round(3).to_string())


if __name__ == "__main__":
    main()
