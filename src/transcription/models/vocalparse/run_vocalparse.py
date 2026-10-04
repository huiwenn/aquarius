"""
Run VocalParse (Chen et al., arXiv 2605.04613; Qwen3-ASR-1.7B fine-tuned for singing
transcription) on a folder of audio -> one .mid + one lyrics .txt per input file.

VocalParse emits a token sequence, not timestamps:
    language Chinese<asr_text>感受<|file_sep|>感 <P_68> <NOTE_4> 受 <P_60> <NOTE_8> ... <BPM_89>
i.e. lyrics (CoT prefix), then per character one or more (MIDI pitch, note value) pairs,
then a single global BPM. "SP"/"AP" words (pitch 0) are rests/breaths. Absolute times are
reconstructed here as cumulative  note_value * 60 / BPM.

Timing modes (--timing):
  fit  (default) strip leading/trailing rests from the predicted sequence and linearly
       stretch it onto the voiced span of the chunk (librosa.effects.trim, top_db=40).
       Corrects global tempo/offset error; does not fix per-note quantisation drift.
  raw  first token at chunk start, durations exactly note_value*60/BPM.

Chunking: the model was trained on sentence-level segments (a few s to ~15 s).
Inputs longer than --max-seg-sec (default 20 s) are cut into voiced regions with
librosa.effects.split(top_db=35); adjacent regions are greedily merged while the
merged chunk stays <= max-seg-sec; any single region still longer is hard-split at the
lowest-RMS 50 ms frame within the last 5 s before the limit. Each chunk is transcribed
independently and its notes are offset by the chunk start time. Short inputs (<= max-seg)
are a single chunk.

Device: MPS (Apple Silicon) in bf16 by default; --device cpu uses float32. The upstream
loader (vocalparse.model.load_model) only knows cuda/cpu and picks fp16 off-CUDA; the
`load_model_any_device` below is the only patch (upstream code is untouched).

Outputs (per input stem):
  <out>/<stem>.mid   single track "vocalparse"
  <out>/<stem>.txt   predicted lyrics (all chunks, one line per chunk)
  <out>/<stem>.json  raw decoded text per chunk + chunk bounds + BPM (for re-deriving MIDI)
Use --from-json to rebuild MIDI from saved .json files without re-running the model.

Env: conda env `vocalparse` (arm64 miniforge at ~/miniforge3, python 3.11, torch 2.14,
transformers 4.57.6, qwen-asr 0.0.6). Run with PYTHONNOUSERSITE=1 (x86 ~/.local packages
otherwise shadow the env). Weights: third_party/weights/VocalParse (hf: pymaster/VocalParse);
the processor/architecture come from Qwen/Qwen3-ASR-1.7B (auto-downloaded to HF cache).

Usage:
  PYTHONNOUSERSITE=1 ~/miniforge3/envs/vocalparse/bin/python \
      src/transcription/models/vocalparse/run_vocalparse.py IN_DIR OUT_DIR \
      [--device mps|cpu] [--timing fit|raw] [--max-seg-sec 20] [--lyrics-dir DIR]
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import librosa
import numpy as np
import pretty_midi

ROOT = Path(__file__).resolve().parents[4]
VP_DIR = ROOT / "third_party" / "VocalParse"
CKPT = ROOT / "third_party" / "weights" / "VocalParse"
SR = 16000
AUDIO_EXT = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aac", ".aiff", ".aif"}
NOTE_DUR = {
    "<NOTE_32>": 0.125, "<NOTE_DOT_32>": 0.1875, "<NOTE_16>": 0.25, "<NOTE_DOT_16>": 0.375,
    "<NOTE_8>": 0.5, "<NOTE_DOT_8>": 0.75, "<NOTE_4>": 1.0, "<NOTE_DOT_4>": 1.5,
    "<NOTE_2>": 2.0, "<NOTE_DOT_2>": 3.0, "<NOTE_1>": 4.0, "<NOTE_DOT_1>": 6.0,
}
REST_WORDS = {"SP", "AP"}

sys.path.insert(0, str(VP_DIR))


# ─────────────────────────── model loading (MPS patch) ───────────────────────────

def load_model_any_device(checkpoint: Path, device: str):
    """Same as vocalparse.model.load_model but supports mps and chooses a sane dtype."""
    import torch
    from qwen_asr import Qwen3ASRModel
    from safetensors.torch import load_file
    from transformers import GenerationConfig
    from vocalparse.model import (_detect_base_model_path, _infer_checkpoint_vocab_size,
                                  patch_outer_forward, register_vocalparse_tokens)

    dtype = torch.bfloat16 if device in ("mps", "cuda") else torch.float32
    base = _detect_base_model_path(str(checkpoint))
    wrapper = Qwen3ASRModel.from_pretrained(base, dtype=dtype, device_map=None,
                                            attn_implementation="sdpa")
    model, processor = wrapper.model, wrapper.processor
    patch_outer_forward(model)
    model.generation_config = GenerationConfig.from_model_config(model.config)
    register_vocalparse_tokens(processor, model,
                               target_vocab_size=_infer_checkpoint_vocab_size(str(checkpoint)))
    sd = load_file(str(checkpoint / "model.safetensors"))
    missing, unexpected = model.load_state_dict(sd, strict=False)
    if unexpected or len(missing) > 0:
        print(f"  load_state_dict: {len(missing)} missing, {len(unexpected)} unexpected keys")
    model = model.to(device=device, dtype=dtype).eval()
    return model, processor


class VocalParse:
    def __init__(self, device: str, max_new_tokens: int = 1024):
        import torch
        from vocalparse.prompts import build_prefix_text
        self.torch = torch
        self.device = device
        self.model, self.processor = load_model_any_device(CKPT, device)
        self.build_prefix = build_prefix_text
        self.max_new_tokens = max_new_tokens

    def __call__(self, wav: np.ndarray, lyrics: str | None = None) -> str:
        prefix = self.build_prefix(self.processor, lyrics_text=lyrics)
        inputs = self.processor(text=[prefix], audio=[wav.astype(np.float32)], sampling_rate=SR,
                                return_tensors="pt", padding=False, truncation=False)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        if inputs["input_features"].is_floating_point():
            inputs["input_features"] = inputs["input_features"].to(self.model.dtype)
        n = inputs["input_ids"].shape[1]
        with self.torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=False)
        seq = out.sequences[0] if hasattr(out, "sequences") else out[0]
        text = self.processor.tokenizer.decode(seq[n:], skip_special_tokens=False)
        return (f"<asr_text>{lyrics}<|file_sep|>" if lyrics else "") + text


# ─────────────────────────── parsing / timing ───────────────────────────

def parse(text: str) -> tuple[str, list[tuple[str, int, float]], int]:
    """-> (lyrics, [(word, midi_pitch_or_0, note_value_beats)], bpm)."""
    lyrics = ""
    m = re.search(r"<asr_text>(.*?)<\|file_sep\|>", text, flags=re.S)
    if m:
        lyrics = m.group(1).strip()
    ast = text.split("<|file_sep|>")[-1]
    bpm = 120
    entries, word = [], None
    for tok in re.findall(r"<[^>]+>|[^\s<>]+", ast):
        if tok.startswith("<BPM_"):
            bpm = int(re.findall(r"\d+", tok)[0]) or 120
        elif tok.startswith("<P_"):
            if entries and entries[-1][2] is None:
                entries[-1][2] = 1.0
            entries.append([word or "·", int(re.findall(r"\d+", tok)[0]), None])
            word = None
        elif tok in NOTE_DUR:
            if entries and entries[-1][2] is None:
                entries[-1][2] = NOTE_DUR[tok]
        elif not tok.startswith("<") and tok not in ("language", "Chinese"):
            word = tok
    if entries and entries[-1][2] is None:
        entries[-1][2] = 1.0
    return lyrics, [tuple(e) for e in entries], bpm


def is_rest(e) -> bool:
    return e[0] in REST_WORDS or e[1] == 0


def to_notes(entries, bpm: int, t0: float, t1: float, timing: str) -> list[tuple[float, float, int]]:
    """Place parsed entries in absolute time within chunk [t0, t1] (voiced span for 'fit')."""
    spb = 60.0 / bpm
    if timing == "scale":
        total = sum(e[2] for e in entries) * spb
        spb *= (t1 - t0) / total if total > 0 else 1.0
    if timing == "fit":
        i, j = 0, len(entries)
        while i < j and is_rest(entries[i]):
            i += 1
        while j > i and is_rest(entries[j - 1]):
            j -= 1
        entries = entries[i:j]
        total = sum(e[2] for e in entries) * spb
        scale = (t1 - t0) / total if total > 0 else 1.0
        spb *= scale
    notes, t = [], t0
    for w, p, v in entries:
        d = v * spb
        if not is_rest((w, p, v)):
            notes.append((t, t + d, p))
        t += d
    return notes


# ─────────────────────────── chunking ───────────────────────────

def hard_split(y, sr, a, b, max_seg, search=5.0):
    cuts, start, hop = [a], a, int(0.05 * sr)
    while b - start > max_seg * sr:
        hi = start + int(max_seg * sr)
        lo = max(start + int((max_seg - search) * sr), start + hop)
        rms = librosa.feature.rms(y=y[lo:hi], frame_length=2 * hop, hop_length=hop, center=False)[0]
        cut = lo + int(np.argmin(rms)) * hop + hop if len(rms) else hi
        cuts.append(cut)
        start = cut
    cuts.append(b)
    return list(zip(cuts[:-1], cuts[1:]))


def make_chunks(y: np.ndarray, sr: int, max_seg: float, pad: float = 0.15) -> list[tuple[int, int]]:
    n = len(y)
    if n <= max_seg * sr:
        return [(0, n)]
    ivs = librosa.effects.split(y, top_db=35, frame_length=2048, hop_length=512)
    p = int(pad * sr)
    padded = []
    for a, b in ivs:  # pad each voiced region, but never into the previous one
        a = max(0, a - p, padded[-1][1] if padded else 0)
        padded.append((a, min(n, b + p)))
    ivs = padded
    pieces = []
    for a, b in ivs:
        pieces += hard_split(y, sr, a, b, max_seg) if b - a > max_seg * sr else [(a, b)]
    chunks = []
    for a, b in pieces:
        if chunks and b - chunks[-1][0] <= max_seg * sr:
            chunks[-1] = (chunks[-1][0], b)
        else:
            chunks.append((a, b))
    return chunks


def voiced_span(y: np.ndarray, sr: int) -> tuple[float, float]:
    _, (a, b) = librosa.effects.trim(y, top_db=40, frame_length=1024, hop_length=160)
    return (a / sr, b / sr) if b > a else (0.0, len(y) / sr)


# ─────────────────────────── main ───────────────────────────

def f0_track(path: str) -> tuple[np.ndarray, np.ndarray]:
    """pYIN f0 (MIDI, NaN when unvoiced) at 10 ms hop."""
    y, _ = librosa.load(path, sr=SR, mono=True)
    f0, _, _ = librosa.pyin(y, fmin=65, fmax=1300, sr=SR, frame_length=2048, hop_length=160)
    return np.arange(len(f0)) * 0.01, librosa.hz_to_midi(f0)


def write_outputs(out_dir: Path, stem: str, rec: dict, timing: str, pitch_src: str = "model") -> int:
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0, name="vocalparse")
    lyric_lines = []
    f0 = f0_track(rec["file"]) if pitch_src == "f0" else None
    for c in rec["chunks"]:
        lyrics, entries, bpm = parse(c["text"])
        lyric_lines.append(lyrics)
        if timing == "fit":
            t0, t1 = c["voiced"]
        else:
            t0, t1 = c["start"], c["end"]
        for s, e, p in to_notes(entries, bpm, t0, t1, timing):
            if f0 is not None:  # replace model pitch by median pYIN pitch inside the note
                seg = f0[1][(f0[0] >= s) & (f0[0] < e)]
                seg = seg[~np.isnan(seg)]
                if len(seg):
                    p = int(round(float(np.median(seg))))
            if e > s and 0 < p < 128:
                inst.notes.append(pretty_midi.Note(velocity=90, pitch=int(p), start=s, end=e))
    pm.instruments.append(inst)
    pm.write(str(out_dir / f"{stem}.mid"))
    (out_dir / f"{stem}.txt").write_text("\n".join(lyric_lines) + "\n", encoding="utf-8")
    return len(inst.notes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("in_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"])
    ap.add_argument("--timing", default="scale", choices=["fit", "raw", "scale"])
    ap.add_argument("--pitch", default="model", choices=["model", "f0"],
                    help="f0: replace each note pitch with the median pYIN pitch inside it (post-hoc hybrid)")
    ap.add_argument("--max-seg-sec", type=float, default=20.0)
    ap.add_argument("--max-new-tokens", type=int, default=1024)
    ap.add_argument("--lyrics-dir", type=Path, default=None,
                    help="optional dir of <stem>.txt ground-truth lyrics (audio-lyric mode; "
                         "only for inputs that are a single chunk)")
    ap.add_argument("--from-json", action="store_true",
                    help="rebuild .mid/.txt from existing <out>/<stem>.json (or --json-dir) only")
    ap.add_argument("--json-dir", type=Path, default=None)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(f for f in args.in_dir.iterdir() if f.suffix.lower() in AUDIO_EXT)

    if args.from_json:
        jd = args.json_dir or args.out_dir
        for f in files:
            rec = json.loads((jd / f"{f.stem}.json").read_text(encoding="utf-8"))
            write_outputs(args.out_dir, f.stem, rec, args.timing, args.pitch)
        print(f"rebuilt {len(files)} files ({args.timing})")
        return

    t_load = time.time()
    vp = VocalParse(args.device, args.max_new_tokens)
    print(f"model loaded in {time.time() - t_load:.1f}s on {args.device}")
    tot_audio = tot_proc = 0.0
    for k, f in enumerate(files):
        jpath = args.out_dir / f"{f.stem}.json"
        if jpath.exists() and not args.overwrite:
            write_outputs(args.out_dir, f.stem, json.loads(jpath.read_text(encoding="utf-8")), args.timing, args.pitch)
            continue
        y, _ = librosa.load(str(f), sr=SR, mono=True)
        lyr = None
        if args.lyrics_dir and (args.lyrics_dir / f"{f.stem}.txt").exists():
            lyr = (args.lyrics_dir / f"{f.stem}.txt").read_text(encoding="utf-8").strip()
        t = time.time()
        chunks = []
        for a, b in make_chunks(y, SR, args.max_seg_sec):
            seg = y[a:b]
            va, vb = voiced_span(seg, SR)
            text = vp(seg, lyrics=lyr)
            chunks.append({"start": a / SR, "end": b / SR,
                           "voiced": [a / SR + va, a / SR + vb], "text": text})
        dt = time.time() - t
        dur = len(y) / SR
        tot_audio += dur
        tot_proc += dt
        rec = {"file": str(f), "duration": dur, "proc_sec": dt, "timing_note": "see run_vocalparse.py",
               "chunks": chunks}
        jpath.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        n = write_outputs(args.out_dir, f.stem, rec, args.timing, args.pitch)
        print(f"[{k + 1}/{len(files)}] {f.stem}: {dur:.1f}s audio, {len(chunks)} chunk(s), "
              f"{n} notes, {dt:.1f}s", flush=True)
    if tot_audio:
        print(f"TOTAL audio {tot_audio:.1f}s, processing {tot_proc:.1f}s -> "
              f"{60 * tot_proc / tot_audio:.1f} s per minute of audio (RTF {tot_proc / tot_audio:.2f})")


if __name__ == "__main__":
    main()
