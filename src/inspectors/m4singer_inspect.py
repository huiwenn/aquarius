#!/usr/bin/env python3
"""Inspect the M4Singer dataset.

Walks the extracted M4Singer directory tree, maps structure,
counts audio files per singer, checks durations and sample rates,
extracts annotation fields, and identifies voice type labels.

Usage:
    python src/inspectors/m4singer_inspect.py [--data-dir data/raw/m4singer/m4singer]
"""

import argparse
import json
import os
import sys
import wave
from collections import Counter, defaultdict
from pathlib import Path


def parse_textgrid(path: str) -> dict:
    """Parse a Praat TextGrid file and extract tier information.

    Returns dict with tier names, interval counts, and sample intervals.
    """
    result = {"tiers": [], "xmin": 0.0, "xmax": 0.0}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        current_tier = None
        current_interval = {}

        for line in lines:
            line = line.strip()
            if line.startswith("xmin =") and current_tier is None and result["xmin"] == 0.0:
                result["xmin"] = float(line.split("=")[1].strip())
            elif line.startswith("xmax =") and current_tier is None and result["xmax"] == 0.0:
                result["xmax"] = float(line.split("=")[1].strip())
            elif line.startswith('class = "IntervalTier"'):
                current_tier = {"name": "", "intervals": []}
            elif line.startswith('name = "') and current_tier is not None:
                current_tier["name"] = line.split('"')[1]
            elif line.startswith('text = "') and current_tier is not None:
                text = line.split('"')[1]
                current_interval["text"] = text
                if current_interval:
                    current_tier["intervals"].append(current_interval.copy())
                current_interval = {}
            elif "item [" in line and current_tier is not None and current_tier["intervals"]:
                result["tiers"].append(current_tier)
                current_tier = {"name": "", "intervals": []}

        if current_tier is not None and current_tier.get("intervals"):
            result["tiers"].append(current_tier)

    except Exception as e:
        result["error"] = str(e)

    return result


def inspect_wav(path: str) -> dict:
    """Get WAV file properties."""
    try:
        with wave.open(path, "r") as w:
            return {
                "sample_rate": w.getframerate(),
                "channels": w.getnchannels(),
                "sample_width": w.getsampwidth(),
                "n_frames": w.getnframes(),
                "duration": w.getnframes() / w.getframerate(),
            }
    except Exception as e:
        return {"error": str(e)}


def inspect_m4singer(data_dir: str) -> dict:
    """Run full inspection of the M4Singer dataset.

    Returns a dict with all inspection results.
    """
    data_path = Path(data_dir)
    results = {
        "dataset": "M4Singer",
        "data_dir": str(data_path),
        "exists": data_path.exists(),
    }

    if not data_path.exists():
        print(f"ERROR: Data directory not found: {data_path}")
        return results

    # --- Directory structure ---
    print("=" * 60)
    print("M4Singer Dataset Inspection")
    print("=" * 60)

    # Find all song directories (Singer#SongName pattern)
    song_dirs = sorted([
        d for d in data_path.iterdir()
        if d.is_dir() and "#" in d.name
    ])

    # Parse singer and song info
    singers = defaultdict(list)
    voice_types = defaultdict(list)
    all_songs = []

    for song_dir in song_dirs:
        parts = song_dir.name.split("#", 1)
        singer_id = parts[0]
        song_name = parts[1] if len(parts) > 1 else "unknown"
        singers[singer_id].append(song_name)

        # Extract voice type
        voice_type = singer_id.rsplit("-", 1)[0]
        voice_types[voice_type].append(singer_id)
        all_songs.append({
            "dir": song_dir,
            "singer_id": singer_id,
            "song_name": song_name,
            "voice_type": voice_type,
        })

    results["n_singers"] = len(singers)
    results["n_songs"] = len(song_dirs)

    print(f"\n--- Singer & Song Summary ---")
    print(f"Total singers: {len(singers)}")
    print(f"Total song directories: {len(song_dirs)}")
    print(f"\nVoice types (SATB):")
    for vt in ["Soprano", "Alto", "Tenor", "Bass"]:
        vt_singers = sorted(set(s for s in singers if s.startswith(vt)))
        total_songs = sum(len(singers[s]) for s in vt_singers)
        print(f"  {vt}: {len(vt_singers)} singers, {total_songs} songs")
        for s in vt_singers:
            print(f"    {s}: {len(singers[s])} songs")

    results["singers"] = {s: len(songs) for s, songs in sorted(singers.items())}
    results["voice_types"] = {
        vt: {
            "n_singers": len(set(s for s in singers if s.startswith(vt))),
            "n_songs": sum(len(singers[s]) for s in singers if s.startswith(vt)),
        }
        for vt in ["Soprano", "Alto", "Tenor", "Bass"]
    }

    # --- File counts per type ---
    print(f"\n--- File Type Analysis ---")
    file_ext_counts = Counter()
    total_files = 0
    for song_dir in song_dirs:
        for f in song_dir.iterdir():
            if f.is_file():
                file_ext_counts[f.suffix.lower()] += 1
                total_files += 1

    # Check for meta.json
    meta_path = data_path / "meta.json"
    if meta_path.exists():
        file_ext_counts[".json (meta)"] = 1
        total_files += 1

    print(f"Total files: {total_files}")
    for ext, count in sorted(file_ext_counts.items()):
        print(f"  {ext}: {count}")

    results["file_counts"] = dict(file_ext_counts)

    # --- WAV analysis (sample from each singer) ---
    print(f"\n--- Audio Analysis ---")
    sample_rates = Counter()
    channels_counter = Counter()
    sample_widths = Counter()
    singer_durations = defaultdict(float)
    singer_segment_counts = defaultdict(int)
    total_duration = 0.0
    min_duration = float("inf")
    max_duration = 0.0
    all_durations = []

    for song in all_songs:
        wav_files = sorted(song["dir"].glob("*.wav"))
        for wav_file in wav_files:
            info = inspect_wav(str(wav_file))
            if "error" in info:
                continue
            sample_rates[info["sample_rate"]] += 1
            channels_counter[info["channels"]] += 1
            sample_widths[info["sample_width"]] += 1
            dur = info["duration"]
            total_duration += dur
            singer_durations[song["singer_id"]] += dur
            singer_segment_counts[song["singer_id"]] += 1
            all_durations.append(dur)
            min_duration = min(min_duration, dur)
            max_duration = max(max_duration, dur)

    n_wav = len(all_durations)
    avg_duration = total_duration / n_wav if n_wav > 0 else 0

    print(f"Total WAV segments: {n_wav}")
    print(f"Total duration: {total_duration:.1f}s ({total_duration / 3600:.2f} hours)")
    print(f"Duration range: {min_duration:.2f}s - {max_duration:.2f}s")
    print(f"Average segment duration: {avg_duration:.2f}s")
    print(f"Sample rates: {dict(sample_rates)}")
    print(f"Channels: {dict(channels_counter)}")
    print(f"Sample widths: {dict(sample_widths)} bytes")

    print(f"\nDuration per singer:")
    for singer in sorted(singer_durations.keys()):
        dur = singer_durations[singer]
        n_seg = singer_segment_counts[singer]
        print(f"  {singer}: {dur:.1f}s ({dur / 60:.1f}min), {n_seg} segments")

    results["audio"] = {
        "n_wav_segments": n_wav,
        "total_duration_s": round(total_duration, 1),
        "total_duration_hours": round(total_duration / 3600, 2),
        "min_duration_s": round(min_duration, 2),
        "max_duration_s": round(max_duration, 2),
        "avg_duration_s": round(avg_duration, 2),
        "sample_rates": dict(sample_rates),
        "channels": dict(channels_counter),
        "sample_widths_bytes": dict(sample_widths),
        "per_singer": {
            s: {
                "duration_s": round(singer_durations[s], 1),
                "n_segments": singer_segment_counts[s],
            }
            for s in sorted(singer_durations.keys())
        },
    }

    # --- Metadata analysis (meta.json) ---
    print(f"\n--- Metadata Analysis (meta.json) ---")
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        print(f"Total metadata entries: {len(meta)}")
        print(f"Entry format: list of dicts")

        # Analyze fields
        all_fields = set()
        for entry in meta:
            all_fields.update(entry.keys())
        print(f"Fields per entry: {sorted(all_fields)}")

        # Analyze field types and value ranges
        sample = meta[0]
        print(f"\nField details (from first entry):")
        for field in sorted(sample.keys()):
            val = sample[field]
            if isinstance(val, str):
                print(f"  {field}: str, example: '{val}'")
            elif isinstance(val, list):
                print(f"  {field}: list of {len(val)} items, "
                      f"type: {type(val[0]).__name__ if val else 'empty'}, "
                      f"example: {val[:5]}")
            elif isinstance(val, (int, float)):
                print(f"  {field}: {type(val).__name__}, value: {val}")

        # Collect unique phonemes
        all_phonemes = set()
        all_notes = set()
        special_tokens = set()
        for entry in meta:
            for ph in entry.get("phs", []):
                all_phonemes.add(ph)
                if ph.startswith("<"):
                    special_tokens.add(ph)
            for note in entry.get("notes", []):
                all_notes.add(note)

        print(f"\nUnique phonemes: {len(all_phonemes)}")
        print(f"Special tokens: {sorted(special_tokens)}")
        print(f"Regular phonemes: {sorted(all_phonemes - special_tokens)}")
        print(f"MIDI note range: {min(all_notes)} - {max(all_notes)} "
              f"(0 = rest, others are MIDI pitch)")
        non_zero_notes = [n for n in all_notes if n > 0]
        if non_zero_notes:
            print(f"Pitch range (excl. rests): MIDI {min(non_zero_notes)} - {max(non_zero_notes)}")

        # Check is_slur distribution
        slur_counts = Counter()
        for entry in meta:
            for s in entry.get("is_slur", []):
                slur_counts[s] += 1
        print(f"\nis_slur distribution: {dict(slur_counts)}")

        results["metadata"] = {
            "n_entries": len(meta),
            "fields": sorted(all_fields),
            "n_unique_phonemes": len(all_phonemes),
            "special_tokens": sorted(special_tokens),
            "phonemes": sorted(all_phonemes - special_tokens),
            "midi_note_range": [min(all_notes), max(all_notes)],
            "pitch_range": [min(non_zero_notes), max(non_zero_notes)] if non_zero_notes else None,
            "slur_distribution": dict(slur_counts),
        }
    else:
        print("meta.json not found")
        results["metadata"] = None

    # --- TextGrid analysis ---
    print(f"\n--- TextGrid Analysis ---")
    # Sample a few TextGrid files
    sample_tg_files = []
    for song in all_songs[:5]:
        tgs = sorted(song["dir"].glob("*.TextGrid"))
        if tgs:
            sample_tg_files.append(tgs[0])

    if sample_tg_files:
        tg = parse_textgrid(str(sample_tg_files[0]))
        print(f"Sample TextGrid: {sample_tg_files[0].name}")
        print(f"  Duration: {tg['xmax']}s")
        print(f"  Number of tiers: {len(tg['tiers'])}")
        for i, tier in enumerate(tg["tiers"]):
            print(f"  Tier {i + 1}: name='{tier['name']}', "
                  f"{len(tier['intervals'])} intervals")
            # Show first few intervals
            for interval in tier["intervals"][:3]:
                print(f"    text: '{interval.get('text', '')}'")

        results["textgrid"] = {
            "n_tiers": len(tg["tiers"]),
            "tier_names": [t["name"] for t in tg["tiers"]],
            "description": "Tier 1: word-level alignment (Chinese characters + special tokens), "
                           "Tier 2: phoneme-level alignment (pinyin initials/finals + special tokens)",
        }
    else:
        results["textgrid"] = None

    # --- MIDI analysis ---
    print(f"\n--- MIDI File Analysis ---")
    midi_count = sum(1 for s in all_songs for _ in s["dir"].glob("*.mid"))
    print(f"Total MIDI files: {midi_count}")

    # Check MIDI file sizes
    midi_sizes = []
    for song in all_songs[:10]:
        for mid_file in song["dir"].glob("*.mid"):
            midi_sizes.append(mid_file.stat().st_size)

    if midi_sizes:
        print(f"MIDI file size range: {min(midi_sizes)} - {max(midi_sizes)} bytes "
              f"(avg: {sum(midi_sizes) / len(midi_sizes):.0f})")

    results["midi"] = {
        "n_files": midi_count,
        "size_range_bytes": [min(midi_sizes), max(midi_sizes)] if midi_sizes else None,
    }

    # --- Disk usage ---
    print(f"\n--- Disk Usage ---")
    total_size = 0
    for root, dirs, files in os.walk(data_path):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))

    print(f"Total dataset size: {total_size / (1024**3):.2f} GB")
    results["total_size_gb"] = round(total_size / (1024 ** 3), 2)

    # --- Song name analysis ---
    print(f"\n--- Song Name Analysis ---")
    song_names = [s["song_name"] for s in all_songs]
    unique_songs = set(song_names)
    print(f"Total song directories: {len(song_names)}")
    print(f"Unique song titles: {len(unique_songs)}")

    # Songs covered by multiple singers
    song_singer_map = defaultdict(list)
    for s in all_songs:
        song_singer_map[s["song_name"]].append(s["singer_id"])
    multi_singer_songs = {
        name: singers_list
        for name, singers_list in song_singer_map.items()
        if len(singers_list) > 1
    }
    print(f"Songs performed by multiple singers: {len(multi_singer_songs)}")
    for name, singers_list in sorted(multi_singer_songs.items())[:5]:
        print(f"  '{name}': {singers_list}")
    if len(multi_singer_songs) > 5:
        print(f"  ... and {len(multi_singer_songs) - 5} more")

    results["songs"] = {
        "n_total": len(song_names),
        "n_unique_titles": len(unique_songs),
        "n_multi_singer": len(multi_singer_songs),
    }

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Dataset: M4Singer")
    print(f"Singers: {len(singers)} (SATB: "
          f"S={results['voice_types']['Soprano']['n_singers']}, "
          f"A={results['voice_types']['Alto']['n_singers']}, "
          f"T={results['voice_types']['Tenor']['n_singers']}, "
          f"B={results['voice_types']['Bass']['n_singers']})")
    print(f"Songs: {len(song_dirs)} directories, {len(unique_songs)} unique titles")
    print(f"Audio segments: {n_wav}")
    print(f"Total duration: {total_duration / 3600:.2f} hours")
    print(f"Sample rate: {list(sample_rates.keys())}")
    print(f"Format: mono {list(sample_widths.keys())}*8-bit WAV")
    print(f"Annotations: TextGrid (word + phoneme alignment), "
          f"MIDI (musical score), meta.json (phonemes, notes, durations, slur)")
    print(f"Dataset size: {total_size / (1024**3):.2f} GB")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the M4Singer dataset"
    )
    parser.add_argument(
        "--data-dir",
        default="data/raw/m4singer/m4singer",
        help="Path to extracted M4Singer directory",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional path to save results as JSON",
    )
    args = parser.parse_args()

    results = inspect_m4singer(args.data_dir)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {args.output_json}")


if __name__ == "__main__":
    main()
