"""
Reviewer R3, step 1–2: sample Anthology scores and render them to audio ("resynthesized performances").

Question: is the score→transcription gap caused by the transcriber or by performance practice? We render clean
scores to audio, push them through the *same* GAME pipeline as the real recordings (rev_resynth_transcribe.sh),
and classify the result with score-trained models (rev_resynth_eval.py).

Sample: 120 songs per A5 region (600), seed 0, one song per title group, 20 ≤ notes ≤ 400 and ≤ 240 beats.
Per song (seeded by its index, identical across conditions): tempo ~ U(60, 100) bpm, transposition so the
median pitch lands on a random integer MIDI 62–67.

Synth (no SVS; DiffSinger/OpenUtau need phoneme-aligned lyrics and a GUI/voicebank, not quick): a source-filter
additive "voice" — harmonics up to 4.5 kHz (−6 dB/oct tilt) shaped by a 3-formant vowel envelope; each note is one
syllable with a random vowel (a o i e u; formants glide over ~40 ms), a 25 ms band-passed noise "consonant"
before its onset, 40 ms raised-cosine attack, 60 ms release, a 35% amplitude dip at legato boundaries, and faint
breath noise. 44.1 kHz mono, −20 dBFS RMS.

Conditions (data/regionclf/resynth/audio/<cond>/<sid>.wav):
  plain        score timing/pitch exactly (10 ms pitch smoothing only)
  expressive   plain + vibrato (rate U(5,6) Hz per song, ±30 cents, fading in 150–350 ms after onset),
               portamento glides U(60,100) ms between legato notes, onset jitter U(±20 ms), per-note intonation
               offset U(±15 cents), per-note dynamics U(±3 dB)
  heavy        expressive with doubled/stressed parameters, to bracket transcriber error on real voices (synthetic
               voices are easy for GAME): jitter ±40 ms, intonation ±30 cents, vibrato ±60 cents, portamento
               100–200 ms, and 40% of legato notes sung as melisma (no new syllable: no consonant, no dip,
               same vowel), so note boundaries are marked by pitch change only
  ornamented   expressive + simulated 润腔 (a *performance-practice* simulation, not a transcriber test):
               on notes ≥ 0.25 s, p=0.25 upper-neighbour grace note (倚音, +2/+3 st, 70–110 ms, own syllable-less
               onset), p=0.15 scoop from −2 st over 120 ms (上滑音), p=0.10 fall of −2/−3 st over the last 150 ms
               (下滑音)
  accompanied  expressive + ChMusic instrumental excerpt at +6 dB vocal-to-accompaniment (…/accompanied_mix/);
               rev_resynth_transcribe.sh then separates it with htdemucs, as in the dataset pipeline
Reference MIDI of what was rendered (nominal pitches, rendered onsets; ornaments excluded):
  ref/plain/<sid>.mid (plain), ref/heavy/<sid>.mid, ref/expressive/<sid>.mid (expressive / ornamented / accompanied)
Sample table: data/regionclf/resynth/sample.csv

Run (py312, ~20 min with 3 workers):
  OMP_NUM_THREADS=3 /usr/local/Caskroom/miniforge/base/envs/py312/bin/python src/regionclf/rev_resynth_render.py \
      [--per-region 120] [--workers 3] [--conds plain,expressive,heavy,ornamented,accompanied]
"""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pretty_midi
import soundfile as sf
from scipy.signal import butter, sosfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regionclf.common import A5_REGIONS, D, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = D / "resynth"
SR = 44100
CR = 1000  # control rate (Hz) for amplitude / formant tracks
LEAD = 0.5  # seconds of silence before the first note
CHMUSIC = ROOT / "data" / "raw" / "chmusic" / "ChMusic" / "Musics"
VOWELS = {"a": [(800, 80, 1.0), (1200, 90, 0.5), (2500, 120, 0.25)],
          "o": [(500, 70, 1.0), (900, 80, 0.45), (2400, 120, 0.12)],
          "i": [(300, 60, 1.0), (2300, 100, 0.35), (3000, 120, 0.25)],
          "e": [(450, 70, 1.0), (1900, 100, 0.45), (2600, 120, 0.25)],
          "u": [(350, 60, 1.0), (800, 80, 0.3), (2300, 120, 0.08)]}
VOW = list(VOWELS)
# expressive parameter sets: jitter (s), intonation (cents), vibrato depth (cents), portamento (s range),
# probability that a legato note is sung without a new syllable (melisma: no consonant, no dip)
EXPR = {"expressive": dict(jit=0.02, detune=15, vib=30, port=(0.06, 0.10), melisma=0.0),
        "heavy": dict(jit=0.04, detune=30, vib=60, port=(0.10, 0.20), melisma=0.4)}


# ---------------------------------------------------------------- sampling
def make_sample(per_region: int, seed: int = 0) -> pd.DataFrame:
    A = load("anthology")
    rng = np.random.RandomState(seed)
    rows = []
    for i, r in enumerate(A):
        n = r["notes"]
        beats = n[-1, 0] + n[-1, 1]
        if 20 <= len(n) <= 400 and beats <= 240:
            rows.append((i, r["item_id"], r["region"], r["group"], len(n), beats))
    df = pd.DataFrame(rows, columns=["idx", "item_id", "region", "group", "n_notes", "beats"])
    df = df.sample(frac=1, random_state=rng).drop_duplicates("group")  # one song per title group
    df = pd.concat([df[df.region == reg].head(per_region) for reg in A5_REGIONS]).reset_index(drop=True)
    df["sid"] = [f"s{k:03d}" for k in range(len(df))]
    df["tempo"] = rng.uniform(60, 100, len(df)).round(1)
    df["target_median"] = rng.randint(62, 68, len(df))
    meds = np.array([np.median(A[i]["notes"][:, 2]) for i in df.idx])
    df["shift"] = (df.target_median - np.round(meds)).astype(int)
    return df


# ---------------------------------------------------------------- performance plan
def plan(notes_beats: np.ndarray, tempo: float, shift: int, rng: np.random.RandomState, expressive: bool,
         ornamented: bool, P: dict = EXPR["expressive"]):
    """Return per-note dicts (on, end, cents, gain_db, legato, orn) in seconds. Random draws happen in a fixed order
    so expressive / ornamented / accompanied share the same jitter and intonation for a song."""
    spb = 60.0 / tempo
    on = notes_beats[:, 0] * spb + LEAD
    end = (notes_beats[:, 0] + notes_beats[:, 1]) * spb + LEAD
    n = len(on)
    legato = np.r_[np.abs(on[1:] - end[:-1]) < 1e-3, False]  # note i flows into note i+1
    jit = rng.uniform(-1, 1, n) * P["jit"]
    detune = rng.uniform(-1, 1, n) * P["detune"]
    gain = rng.uniform(-3, 3, n)
    orn_u = rng.uniform(size=(n, 4))
    mel = rng.uniform(size=n) < P["melisma"]
    if expressive:
        on2 = on + jit
        on2[0] = on[0]
        end2 = end.copy()
        for i in range(n):
            end2[i] = on2[i + 1] if legato[i] else end[i] + jit[i]
        on, end = on2, np.maximum(end2, on2 + 0.05)
    cents = 100.0 * (notes_beats[:, 2] + shift)
    out = []
    for i in range(n):
        d = dict(on=on[i], end=end[i], cents=cents[i] + (detune[i] if expressive else 0.0),
                 nominal=int(notes_beats[i, 2] + shift), gain_db=gain[i] if expressive else 0.0,
                 legato=bool(legato[i]), grace=None, scoop=False, fall=None,
                 syllable=not (i > 0 and legato[i - 1] and mel[i]))
        if ornamented and end[i] - on[i] >= 0.25:
            if orn_u[i, 0] < 0.25:
                d["grace"] = (2 if orn_u[i, 1] < 0.5 else 3, 0.07 + 0.04 * orn_u[i, 2])
            elif orn_u[i, 0] < 0.40:
                d["scoop"] = True
            if orn_u[i, 3] < 0.10 and not legato[i]:
                d["fall"] = 2 if orn_u[i, 1] < 0.5 else 3
        out.append(d)
    return out


def _smooth(x: np.ndarray, win: int) -> np.ndarray:
    if win <= 1:
        return x
    k = np.hanning(win + 2)[1:-1]
    k /= k.sum()
    return np.convolve(np.pad(x, (win, win), mode="edge"), k, mode="same")[win:-win]


def synth(notes: list[dict], expressive: bool, rng: np.random.RandomState, vib_rate: float,
          P: dict = EXPR["expressive"]) -> np.ndarray:
    T = notes[-1]["end"] + 0.6
    nc = int(T * CR) + 1
    tc = np.arange(nc) / CR
    cents = np.full(nc, np.nan)
    amp = np.zeros(nc)
    vib_env = np.zeros(nc)
    vow_idx = np.zeros(nc, int)
    cons = []  # consonant onsets (s)
    for k, d in enumerate(notes):
        a, b = int(d["on"] * CR), int(d["end"] * CR)
        b = max(b, a + 20)
        seg = np.full(b - a, d["cents"])
        if d["scoop"]:
            L = min(120, len(seg))
            seg[:L] -= 200 * (1 - np.sin(np.linspace(0, np.pi / 2, L)))
        if d["fall"]:
            L = min(150, len(seg) // 2)
            seg[-L:] -= 100 * d["fall"] * np.sin(np.linspace(0, np.pi / 2, L)) ** 2
        grace_len = 0
        if d["grace"]:
            st, dur = d["grace"]
            grace_len = int(dur * CR)
            seg[:grace_len] = d["cents"] + 100 * st
        cents[a:b] = seg
        g = 10 ** (d["gain_db"] / 20)
        env = np.ones(b - a) * g
        att = min(40, (b - a) // 2)
        prev_legato = k > 0 and notes[k - 1]["legato"]
        if prev_legato and not d["syllable"]:  # melisma: pitch change only
            pass
        elif prev_legato:  # syllable boundary inside a legato line: a dip rather than a fresh attack
            env[:att] *= 0.65 + 0.35 * np.sin(np.linspace(0, np.pi / 2, att)) ** 2
        else:
            env[:att] *= np.sin(np.linspace(0, np.pi / 2, att)) ** 2
        if not d["legato"]:
            rel = min(60, (b - a) // 2)
            env[-rel:] *= np.cos(np.linspace(0, np.pi / 2, rel)) ** 2
        amp[a:b] = np.maximum(amp[a:b], env)
        v = rng.randint(len(VOW))
        if not d["syllable"]:
            v = vow_idx[max(a - 1, 0)]
        vow_idx[a:b] = v
        if d["syllable"]:
            cons.append(d["on"])
        if expressive:
            s = a + int(rng.uniform(0.15, 0.35) * CR)
            if s < b:
                ramp = np.clip(np.arange(b - s) / (0.2 * CR), 0, 1)
                vib_env[s:b] = ramp
    # fill rests with the previous pitch (voice silent there anyway), leading part with the first pitch
    idx = np.where(~np.isnan(cents), np.arange(nc), 0)
    np.maximum.accumulate(idx, out=idx)
    cents = cents[idx]
    first = np.argmax(~np.isnan(cents))
    cents[:first] = cents[first]
    if expressive:  # portamento: raised-cosine glide between legato neighbours
        for k in range(len(notes) - 1):
            if not notes[k]["legato"]:
                continue
            L = int(rng.uniform(*P["port"]) * CR)
            c = int(notes[k + 1]["on"] * CR)
            a, b = max(c - int(0.3 * L), 0), min(c + int(0.7 * L), nc)
            if b - a < 4:
                continue
            p0, p1 = cents[max(a - 1, 0)], cents[min(b, nc - 1)]
            cents[a:b] = p0 + (p1 - p0) * (1 - np.cos(np.linspace(0, np.pi, b - a))) / 2
        cents = cents + P["vib"] * vib_env * np.sin(2 * np.pi * vib_rate * tc + rng.uniform(0, 2 * np.pi))
    else:
        cents = _smooth(cents, 10)
    amp = _smooth(amp, 5)
    # formant tracks (smoothed across vowel changes)
    F = np.array([[f for f, _, _ in VOWELS[VOW[v]]] for v in range(len(VOW))])[vow_idx]  # nc x 3
    Bw = np.array([[bw for _, bw, _ in VOWELS[VOW[v]]] for v in range(len(VOW))])[vow_idx]
    G = np.array([[g for _, _, g in VOWELS[VOW[v]]] for v in range(len(VOW))])[vow_idx]
    F = np.stack([_smooth(F[:, j].astype(float), 40) for j in range(3)], 1)

    n = int(T * SR)
    t = np.arange(n) / SR
    f0 = 440.0 * 2 ** ((np.interp(t, tc, cents) - 6900) / 1200)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    f0c = 440.0 * 2 ** ((cents - 6900) / 1200)
    H = int(4500 / f0c.min())
    y = np.zeros(n)
    for h in range(1, H + 1):
        fh = h * f0c
        gain_h = sum(G[:, j] / (1 + ((fh - F[:, j]) / (Bw[:, j] / 2)) ** 2) for j in range(3)) + 0.03
        gain_h = gain_h / h * (fh < 4500)
        y += np.interp(t, tc, gain_h * amp) * np.sin(h * phase)
    # consonants: 25 ms band-passed noise ending at each syllable onset (skip notes that follow a grace-free slur)
    sos = butter(4, [2000, 6000], btype="band", fs=SR, output="sos")
    noise = sosfilt(sos, rng.randn(n))
    cmask = np.zeros(n)
    L = int(0.025 * SR)
    win = np.hanning(2 * L)[:L]
    for o in cons:
        s = int(o * SR) - L
        if s > 0:
            cmask[s:s + L] = np.maximum(cmask[s:s + L], win)
    rms_v = np.sqrt(np.mean(y[amp[np.minimum((t * CR).astype(int), nc - 1)] > 0.5] ** 2) + 1e-12)
    y += 0.25 * rms_v * cmask * noise / (noise.std() + 1e-9)
    y += 0.01 * rms_v * noise / (noise.std() + 1e-9) * np.interp(t, tc, amp)  # breath
    return y


def normalize(y: np.ndarray, rms_db: float = -20.0) -> np.ndarray:
    y = y * (10 ** (rms_db / 20) / (np.sqrt(np.mean(y ** 2)) + 1e-12))
    pk = np.abs(y).max()
    return y / pk * 0.98 if pk > 0.98 else y


def write_ref(notes: list[dict], path: Path) -> None:
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(0, name="ref")
    for d in notes:
        inst.notes.append(pretty_midi.Note(100, d["nominal"], float(d["on"]), float(d["end"])))
    pm.instruments.append(inst)
    path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(path))


def accompaniment(n: int, rng: np.random.RandomState) -> tuple[np.ndarray, str]:
    files = sorted(CHMUSIC.glob("*.wav"))
    f = files[rng.randint(len(files))]
    x, sr = sf.read(str(f), always_2d=True)
    x = x.mean(1)
    assert sr == SR
    if len(x) < n:
        x = np.tile(x, n // len(x) + 1)
    s = rng.randint(0, len(x) - n + 1)
    x = x[s:s + n].copy()
    fade = min(int(0.5 * SR), n // 4)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return x, f.name


def render_one(args):
    row, notes_beats, conds = args
    sid = row["sid"]
    out = {"sid": sid}
    k = int(sid[1:])
    for cond in conds:
        wav = OUT / "audio" / ("accompanied_mix" if cond == "accompanied" else cond) / f"{sid}.wav"
        if wav.exists():
            continue
        rng = np.random.RandomState(1000 + k)  # identical plan draws across conditions
        vib_rate = rng.uniform(5, 6)
        expressive = cond != "plain"
        P = EXPR["heavy" if cond == "heavy" else "expressive"]
        nl = plan(notes_beats, row["tempo"], row["shift"], rng, expressive, cond == "ornamented", P)
        rng_s = np.random.RandomState(2000 + k)  # identical vowels / noise across conditions
        y = normalize(synth(nl, expressive, rng_s, vib_rate, P))
        write_ref(nl, OUT / "ref" / {"plain": "plain", "heavy": "heavy"}.get(cond, "expressive") / f"{sid}.mid")
        if cond == "accompanied":
            acc, name = accompaniment(len(y), np.random.RandomState(3000 + k))
            acc *= np.sqrt(np.mean(y ** 2)) / (np.sqrt(np.mean(acc ** 2)) + 1e-12) / 10 ** (6 / 20)
            y = normalize(y + acc)
            out["accomp_file"] = name
        wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(wav), y.astype(np.float32), SR, subtype="PCM_16")
        out[f"dur_{cond}"] = len(y) / SR
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-region", type=int, default=120)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--conds", default="plain,expressive,heavy,ornamented,accompanied")
    ap.add_argument("--limit", type=int, default=0, help="render only the first N songs (smoke test)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sample_csv = OUT / "sample.csv"
    if sample_csv.exists():
        df = pd.read_csv(sample_csv)
    else:
        df = make_sample(args.per_region)
        df.to_csv(sample_csv, index=False)
    print(df.groupby("region").size().to_string(), flush=True)
    A = load("anthology")
    conds = args.conds.split(",")
    rows = df.to_dict("records")[: args.limit or None]
    jobs = [(r, A[r["idx"]]["notes"], conds) for r in rows]
    info = []
    with ProcessPoolExecutor(args.workers) as ex:
        for i, o in enumerate(ex.map(render_one, jobs, chunksize=4), 1):
            info.append(o)
            if i % 50 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    pd.DataFrame(info).to_csv(OUT / f"render_info_{'_'.join(conds)}.csv", index=False)


if __name__ == "__main__":
    main()
