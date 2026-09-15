#!/usr/bin/env python3
"""Inspect Opencpop dataset: structure, audio properties, annotations, taxonomy.

Opencpop: A High-Quality Open Source Chinese Popular Song Corpus for
Singing Voice Synthesis.
Paper: https://arxiv.org/abs/2201.07429

Walks the dataset directory, characterizes all files, extracts detailed
audio metadata (duration, sample rate, channels, bit depth), parses
annotation/transcription files, and maps the phoneme taxonomy.

Expected directory structure:
    opencpop/
      midis/         -- MIDI files (one per song, e.g. 2001.midi)
      textgrids/     -- Praat TextGrid annotation files (e.g. 2001.TextGrid)
      wavs/          -- Full song WAV files (e.g. 2001.wav)
      segments/
        wavs/              -- Utterance-level WAV files (e.g. 2001000001.wav)
        transcriptions.txt -- All utterance labels
        train.txt          -- Training split labels
        test.txt           -- Test split labels
      TERMS_OF_ACCESS
      readme.md

Annotation format (pipe-delimited, 7 fields):
    utterance_wav | text | phonemes | notes | note_durations | phoneme_durations | slur_flags

Requirements:
    pip install soundfile librosa mido
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import soundfile as sf


def parse_transcription_line(line: str) -> dict:
    """Parse a single line from transcriptions.txt.

    Format: wav_name|text|phonemes|notes|note_durations|phoneme_durations|slur_flags
    """
    parts = line.strip().split("|")
    if len(parts) != 7:
        return None

    return {
        "utterance_id": parts[0].strip(),
        "text": parts[1].strip(),
        "phonemes": parts[2].strip(),
        "notes": parts[3].strip(),
        "note_durations": parts[4].strip(),
        "phoneme_durations": parts[5].strip(),
        "slur_flags": parts[6].strip(),
    }


def analyze_transcriptions(transcriptions_path: Path) -> dict:
    """Parse and analyze a transcription file."""
    results = {
        "file": str(transcriptions_path.name),
        "total_lines": 0,
        "valid_entries": 0,
        "parse_errors": 0,
        "unique_songs": set(),
        "phoneme_counts": Counter(),
        "note_counts": Counter(),
        "slur_distribution": Counter(),
        "text_lengths": [],
        "phonemes_per_utterance": [],
        "notes_per_utterance": [],
        "example_entries": [],
        "all_phonemes": set(),
        "all_notes": set(),
    }

    if not transcriptions_path.exists():
        results["error"] = "File not found"
        return results

    with open(transcriptions_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    results["total_lines"] = len(lines)

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        entry = parse_transcription_line(line)
        if entry is None:
            results["parse_errors"] += 1
            continue

        results["valid_entries"] += 1

        # Extract song ID from utterance ID (first 4 digits)
        song_id = entry["utterance_id"][:4]
        results["unique_songs"].add(song_id)

        # Phoneme analysis
        phonemes = entry["phonemes"].split()
        for p in phonemes:
            results["phoneme_counts"][p] += 1
            results["all_phonemes"].add(p)
        results["phonemes_per_utterance"].append(len(phonemes))

        # Note analysis
        notes = entry["notes"].split()
        for n in notes:
            results["note_counts"][n] += 1
            results["all_notes"].add(n)
        results["notes_per_utterance"].append(len(notes))

        # Text length
        results["text_lengths"].append(len(entry["text"]))

        # Slur flags
        slur_vals = entry["slur_flags"].split()
        for s in slur_vals:
            results["slur_distribution"][s] += 1

        # Save first few as examples
        if len(results["example_entries"]) < 5:
            results["example_entries"].append(entry)

    # Convert sets for JSON serialization
    results["unique_songs"] = sorted(results["unique_songs"])
    results["all_phonemes"] = sorted(results["all_phonemes"])
    results["all_notes"] = sorted(results["all_notes"])
    results["phoneme_counts"] = dict(
        results["phoneme_counts"].most_common()
    )
    results["note_counts"] = dict(
        results["note_counts"].most_common(30)
    )
    results["slur_distribution"] = dict(results["slur_distribution"])

    return results


def analyze_audio_files(wav_dir: Path, label: str, limit: int = None) -> dict:
    """Analyze WAV files in a directory."""
    results = {
        "directory": str(wav_dir),
        "label": label,
        "total_files": 0,
        "analyzed": 0,
        "errors": [],
        "total_duration_seconds": 0.0,
        "sample_rates": Counter(),
        "channels": Counter(),
        "subtypes": Counter(),
        "durations": [],
        "file_sizes": [],
    }

    if not wav_dir.exists():
        results["error"] = f"Directory not found: {wav_dir}"
        return results

    wav_files = sorted(wav_dir.glob("*.wav"))
    results["total_files"] = len(wav_files)

    files_to_analyze = wav_files[:limit] if limit else wav_files

    for wav_path in files_to_analyze:
        try:
            info = sf.info(str(wav_path))
            results["analyzed"] += 1
            results["total_duration_seconds"] += info.duration
            results["sample_rates"][info.samplerate] += 1
            results["channels"][info.channels] += 1
            results["subtypes"][info.subtype] += 1
            results["durations"].append(info.duration)
            results["file_sizes"].append(wav_path.stat().st_size)
        except Exception as e:
            results["errors"].append(f"{wav_path.name}: {e}")

    # Summary statistics
    if results["durations"]:
        durations = results["durations"]
        results["summary"] = {
            "total_duration_seconds": round(sum(durations), 2),
            "total_duration_minutes": round(sum(durations) / 60, 2),
            "total_duration_hours": round(sum(durations) / 3600, 2),
            "min_duration_seconds": round(min(durations), 2),
            "max_duration_seconds": round(max(durations), 2),
            "mean_duration_seconds": round(
                sum(durations) / len(durations), 2
            ),
            "total_size_mb": round(sum(results["file_sizes"]) / (1024**2), 2),
            "sample_rates": dict(results["sample_rates"]),
            "channels": dict(results["channels"]),
            "subtypes": dict(results["subtypes"]),
        }

    # Convert Counters for JSON
    results["sample_rates"] = dict(results["sample_rates"])
    results["channels"] = dict(results["channels"])
    results["subtypes"] = dict(results["subtypes"])

    return results


def analyze_midi_files(midi_dir: Path) -> dict:
    """Analyze MIDI files if mido is available."""
    results = {
        "directory": str(midi_dir),
        "total_files": 0,
        "analyzed": 0,
        "errors": [],
        "details": [],
    }

    if not midi_dir.exists():
        results["error"] = f"Directory not found: {midi_dir}"
        return results

    midi_files = sorted(
        list(midi_dir.glob("*.midi")) + list(midi_dir.glob("*.mid"))
    )
    results["total_files"] = len(midi_files)

    try:
        import mido
    except ImportError:
        results["error"] = "mido not installed (pip install mido). Skipping MIDI analysis."
        return results

    for midi_path in midi_files:
        try:
            mid = mido.MidiFile(str(midi_path))
            detail = {
                "filename": midi_path.name,
                "type": mid.type,
                "tracks": len(mid.tracks),
                "ticks_per_beat": mid.ticks_per_beat,
                "length_seconds": round(mid.length, 2),
            }
            results["details"].append(detail)
            results["analyzed"] += 1
        except Exception as e:
            results["errors"].append(f"{midi_path.name}: {e}")

    return results


def analyze_textgrids(textgrid_dir: Path) -> dict:
    """Analyze TextGrid files (basic stats without requiring tgt/praatio)."""
    results = {
        "directory": str(textgrid_dir),
        "total_files": 0,
        "file_list": [],
        "file_sizes": [],
    }

    if not textgrid_dir.exists():
        results["error"] = f"Directory not found: {textgrid_dir}"
        return results

    tg_files = sorted(textgrid_dir.glob("*.TextGrid"))
    results["total_files"] = len(tg_files)

    for tg in tg_files:
        size = tg.stat().st_size
        results["file_list"].append(tg.name)
        results["file_sizes"].append(size)

    if results["file_sizes"]:
        results["total_size_mb"] = round(
            sum(results["file_sizes"]) / (1024**2), 2
        )
        results["min_size_kb"] = round(min(results["file_sizes"]) / 1024, 1)
        results["max_size_kb"] = round(max(results["file_sizes"]) / 1024, 1)

    # Try to parse one TextGrid to understand tier structure
    if tg_files:
        try:
            with open(tg_files[0], "r", encoding="utf-8") as f:
                content = f.read(2000)  # First 2KB
            results["sample_header"] = content[:500]
            # Count tiers
            tier_count = content.count('"IntervalTier"') + content.count(
                '"TextTier"'
            )
            results["tier_count_estimate"] = tier_count
        except Exception as e:
            results["header_error"] = str(e)

    return results


def inspect_opencpop(data_dir: str) -> dict:
    """Run full inspection of Opencpop dataset.

    Args:
        data_dir: Path to data/raw/opencpop/ directory.

    Returns:
        Dictionary with all inspection results.
    """
    data_path = Path(data_dir)
    results = {
        "dataset": "Opencpop",
        "root_path": str(data_path),
        "directory_tree": {},
        "file_types": defaultdict(
            lambda: {"count": 0, "total_size_bytes": 0}
        ),
        "full_song_audio": {},
        "segment_audio": {},
        "midi_files": {},
        "textgrid_files": {},
        "transcriptions": {},
        "train_test_split": {},
        "issues": [],
    }

    # ---- 1. Directory tree ----
    print("=" * 60)
    print("OPENCPOP DATASET INSPECTION")
    print("=" * 60)
    print(f"\nRoot: {data_path}")
    print("\n=== Directory Structure ===")
    tree = {}
    for root, dirs, files in os.walk(data_path):
        rel_root = os.path.relpath(root, data_path)
        if rel_root == ".":
            rel_root = ""
        level = rel_root.count(os.sep) if rel_root else 0
        indent = "  " * level
        dirname = os.path.basename(root) if rel_root else str(data_path.name)
        file_count = len(files)
        print(f"{indent}{dirname}/ ({file_count} files)")
        tree[rel_root] = {
            "dirs": sorted(dirs),
            "file_count": file_count,
            "sample_files": sorted(files)[:10],
        }

    results["directory_tree"] = tree

    # ---- 2. File type census ----
    print("\n=== File Type Census ===")
    all_files = [f for f in data_path.rglob("*") if f.is_file()]

    for f in all_files:
        ext = f.suffix.lower()
        if not ext:
            ext = "(no extension)"
        entry = results["file_types"][ext]
        entry["count"] += 1
        entry["total_size_bytes"] += f.stat().st_size

    for ext, info in sorted(results["file_types"].items()):
        size_mb = info["total_size_bytes"] / (1024 * 1024)
        print(f"  {ext}: {info['count']} files, {size_mb:.1f} MB")

    total_size = sum(v["total_size_bytes"] for v in results["file_types"].values())
    print(f"  TOTAL: {len(all_files)} files, {total_size / (1024**3):.2f} GB")

    # ---- 3. Full song WAV analysis ----
    print("\n=== Full Song Audio (wavs/) ===")
    wavs_dir = data_path / "wavs"
    results["full_song_audio"] = analyze_audio_files(wavs_dir, "full_songs")
    if "summary" in results["full_song_audio"]:
        s = results["full_song_audio"]["summary"]
        print(f"  Files: {results['full_song_audio']['total_files']}")
        print(f"  Total duration: {s['total_duration_hours']:.2f} hours")
        print(f"  Duration range: {s['min_duration_seconds']:.1f}s - {s['max_duration_seconds']:.1f}s")
        print(f"  Mean duration: {s['mean_duration_seconds']:.1f}s")
        print(f"  Sample rates: {s['sample_rates']}")
        print(f"  Channels: {s['channels']}")
        print(f"  Encoding: {s['subtypes']}")
        print(f"  Total size: {s['total_size_mb']:.1f} MB")
    elif "error" in results["full_song_audio"]:
        print(f"  {results['full_song_audio']['error']}")

    # ---- 4. Segment WAV analysis ----
    print("\n=== Segment Audio (segments/wavs/) ===")
    seg_wavs_dir = data_path / "segments" / "wavs"
    results["segment_audio"] = analyze_audio_files(seg_wavs_dir, "segments")
    if "summary" in results["segment_audio"]:
        s = results["segment_audio"]["summary"]
        print(f"  Files: {results['segment_audio']['total_files']}")
        print(f"  Total duration: {s['total_duration_hours']:.2f} hours")
        print(f"  Duration range: {s['min_duration_seconds']:.1f}s - {s['max_duration_seconds']:.1f}s")
        print(f"  Mean duration: {s['mean_duration_seconds']:.1f}s")
        print(f"  Sample rates: {s['sample_rates']}")
        print(f"  Channels: {s['channels']}")
        print(f"  Encoding: {s['subtypes']}")
        print(f"  Total size: {s['total_size_mb']:.1f} MB")
    elif "error" in results["segment_audio"]:
        print(f"  {results['segment_audio']['error']}")

    # ---- 5. Transcription analysis ----
    print("\n=== Transcriptions ===")
    transcriptions_file = data_path / "segments" / "transcriptions.txt"
    results["transcriptions"] = analyze_transcriptions(transcriptions_file)
    t = results["transcriptions"]
    if "error" not in t:
        print(f"  Total lines: {t['total_lines']}")
        print(f"  Valid entries: {t['valid_entries']}")
        print(f"  Parse errors: {t['parse_errors']}")
        print(f"  Unique songs: {len(t['unique_songs'])}")
        print(f"  Unique phonemes: {len(t['all_phonemes'])}")
        print(f"  Unique notes: {len(t['all_notes'])}")

        if t["phonemes_per_utterance"]:
            ppus = t["phonemes_per_utterance"]
            print(f"  Phonemes per utterance: min={min(ppus)}, max={max(ppus)}, "
                  f"mean={sum(ppus)/len(ppus):.1f}")

        if t["text_lengths"]:
            tls = t["text_lengths"]
            print(f"  Text length (chars): min={min(tls)}, max={max(tls)}, "
                  f"mean={sum(tls)/len(tls):.1f}")

        print(f"\n  Top 20 phonemes:")
        for p, c in list(t["phoneme_counts"].items())[:20]:
            print(f"    {p:8s}: {c}")

        print(f"\n  All phonemes ({len(t['all_phonemes'])}):")
        # Group into rows of 10
        phonemes = t["all_phonemes"]
        for i in range(0, len(phonemes), 10):
            print(f"    {', '.join(phonemes[i:i+10])}")

        print(f"\n  Sample note names (first 20):")
        notes_sample = sorted(t["all_notes"])[:20]
        print(f"    {', '.join(notes_sample)}")

        print(f"\n  Slur distribution: {t['slur_distribution']}")

        print(f"\n  Example entries:")
        for entry in t["example_entries"][:3]:
            print(f"    ID: {entry['utterance_id']}")
            print(f"    Text: {entry['text']}")
            print(f"    Phonemes: {entry['phonemes']}")
            print(f"    Notes: {entry['notes']}")
            print(f"    Note durations: {entry['note_durations']}")
            print(f"    Phoneme durations: {entry['phoneme_durations']}")
            print(f"    Slur: {entry['slur_flags']}")
            print()
    else:
        print(f"  {t.get('error', 'File not found')}")

    # ---- 6. Train/test split ----
    print("\n=== Train/Test Split ===")
    train_file = data_path / "segments" / "train.txt"
    test_file = data_path / "segments" / "test.txt"

    split_info = {}
    for label, fpath in [("train", train_file), ("test", test_file)]:
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            song_ids = set()
            for line in lines:
                entry = parse_transcription_line(line)
                if entry:
                    song_ids.add(entry["utterance_id"][:4])
            split_info[label] = {
                "file": fpath.name,
                "utterance_count": len(lines),
                "song_ids": sorted(song_ids),
                "song_count": len(song_ids),
            }
            print(f"  {label}: {len(lines)} utterances from {len(song_ids)} songs")
            print(f"    Song IDs: {sorted(song_ids)}")
        else:
            split_info[label] = {"error": "File not found"}
            print(f"  {label}: file not found ({fpath})")

    results["train_test_split"] = split_info

    # ---- 7. MIDI analysis ----
    print("\n=== MIDI Files ===")
    midi_dir = data_path / "midis"
    results["midi_files"] = analyze_midi_files(midi_dir)
    m = results["midi_files"]
    print(f"  Total files: {m['total_files']}")
    if m.get("analyzed"):
        print(f"  Analyzed: {m['analyzed']}")
        if m["details"]:
            # Summary
            lengths = [d["length_seconds"] for d in m["details"]]
            print(f"  Duration range: {min(lengths):.1f}s - {max(lengths):.1f}s")
            print(f"  Total duration: {sum(lengths)/60:.1f} minutes")
            print(f"  Ticks per beat: {set(d['ticks_per_beat'] for d in m['details'])}")
            print(f"  MIDI types: {set(d['type'] for d in m['details'])}")
    if m.get("error"):
        print(f"  {m['error']}")

    # ---- 8. TextGrid analysis ----
    print("\n=== TextGrid Files ===")
    tg_dir = data_path / "textgrids"
    results["textgrid_files"] = analyze_textgrids(tg_dir)
    tg = results["textgrid_files"]
    print(f"  Total files: {tg['total_files']}")
    if tg.get("total_size_mb"):
        print(f"  Total size: {tg['total_size_mb']:.1f} MB")
        print(f"  Size range: {tg['min_size_kb']:.1f} KB - {tg['max_size_kb']:.1f} KB")
    if tg.get("tier_count_estimate"):
        print(f"  Tiers per file (estimate): {tg['tier_count_estimate']}")
    if tg.get("error"):
        print(f"  {tg['error']}")

    # ---- 9. Completeness checks ----
    print("\n=== Completeness Checks ===")
    checks_passed = True

    # Check song count
    if "unique_songs" in results["transcriptions"]:
        n_songs = len(results["transcriptions"]["unique_songs"])
        expected_songs = 100
        status = "OK" if n_songs == expected_songs else f"MISMATCH (expected {expected_songs})"
        print(f"  Song count: {n_songs} -- {status}")
        if n_songs != expected_songs:
            checks_passed = False

    # Check utterance count
    if "valid_entries" in results["transcriptions"]:
        n_utt = results["transcriptions"]["valid_entries"]
        expected_utt = 3756
        status = "OK" if n_utt == expected_utt else f"MISMATCH (expected {expected_utt})"
        print(f"  Utterance count: {n_utt} -- {status}")

    # Cross-check: segment WAV count vs transcription entries
    if results["segment_audio"].get("total_files") and results["transcriptions"].get("valid_entries"):
        seg_count = results["segment_audio"]["total_files"]
        trans_count = results["transcriptions"]["valid_entries"]
        match = seg_count == trans_count
        status = "OK" if match else "MISMATCH"
        print(f"  Segment WAVs ({seg_count}) vs transcriptions ({trans_count}): {status}")
        if not match:
            checks_passed = False

    # Cross-check: full WAV count vs MIDI count vs TextGrid count
    full_wav_count = results["full_song_audio"].get("total_files", 0)
    midi_count = results["midi_files"].get("total_files", 0)
    tg_count = results["textgrid_files"].get("total_files", 0)
    print(f"  Full WAVs: {full_wav_count}, MIDIs: {midi_count}, TextGrids: {tg_count}")
    if full_wav_count > 0 and full_wav_count == midi_count == tg_count:
        print(f"    All match: OK")
    elif full_wav_count > 0:
        print(f"    Counts differ -- check manually")
        checks_passed = False

    if checks_passed:
        print("\n  All checks passed.")
    else:
        print("\n  Some checks failed -- see details above.")
        results["issues"].append("Completeness checks had mismatches")

    # ---- 10. Naming convention analysis ----
    print("\n=== Naming Conventions ===")
    if results["full_song_audio"].get("total_files", 0) > 0:
        wav_names = sorted(
            f.name for f in (data_path / "wavs").glob("*.wav")
        )
        print(f"  Full song WAVs: e.g. {wav_names[:3]} ... {wav_names[-3:]}")
        print(f"    Pattern: SSSS.wav (4-digit song ID)")

    if results["segment_audio"].get("total_files", 0) > 0:
        seg_names = sorted(
            f.name for f in (data_path / "segments" / "wavs").glob("*.wav")
        )
        print(f"  Segment WAVs: e.g. {seg_names[:3]} ... {seg_names[-3:]}")
        print(f"    Pattern: SSSSNNNNNN.wav (4-digit song ID + 6-digit segment number)")

    print("\n" + "=" * 60)
    print("INSPECTION COMPLETE")
    print("=" * 60)

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Inspect Opencpop dataset")
    parser.add_argument(
        "--data-dir",
        default="data/raw/opencpop",
        help="Path to opencpop data directory (default: data/raw/opencpop)",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional path to save full inspection results as JSON",
    )
    args = parser.parse_args()

    results = inspect_opencpop(args.data_dir)

    if args.output_json:
        # Convert defaultdicts and sets for JSON serialization
        results["file_types"] = dict(results["file_types"])
        # Remove raw duration/size lists from audio results (too large)
        for key in ["full_song_audio", "segment_audio"]:
            if "durations" in results[key]:
                del results[key]["durations"]
            if "file_sizes" in results[key]:
                del results[key]["file_sizes"]

        with open(args.output_json, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nFull results saved to {args.output_json}")


if __name__ == "__main__":
    main()
