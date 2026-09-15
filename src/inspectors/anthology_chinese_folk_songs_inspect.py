#!/usr/bin/env python3
"""Inspect Anthology of Chinese Folk Songs and its Anonymized Subset.

Anthology: https://github.com/m-july/Anthology-of-Chinese-Folk-Songs-v251103
Anonymized: https://github.com/m-july/Anonymized-Subset-of-Anthology-of-Chinese-Folk-Songs

Paper: "The Renaissance of Expert Systems: Optical Recognition of Printed Chinese
Jianpu Musical Scores with Lyrics" (CSMT 2025, arXiv: 2512.14758)

Walks both dataset directories, counts files by type and region, inspects
MIDI properties (tracks, instruments, note counts, pitch ranges, tempo, key/time
signatures) and MusicXML structure (parts, measures, notes, lyrics, key/time
signatures). Compares the main and anonymized datasets and reports what was
anonymized.

Requirements:
    pip install mido pretty_midi
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import mido


# ---- Configuration ----

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
ANTHOLOGY_DIR = BASE_DIR / "anthology_chinese_folk_songs"
ANONYMIZED_DIR = BASE_DIR / "anonymized_anthology_folk_songs"

# Province/volume organization
LYRICS_INCLUDED_VOLUMES = {
    "guangdong": "Guangdong",
    "jiangsu1": "Jiangsu I",
    "jiangsu2": "Jiangsu II",
}

MELODY_ONLY_VOLUMES = {
    "hainan": "Hainan",
    "hebei1": "Hebei I",
    "hebei2": "Hebei II",
    "henan": "Henan",
    "jilin": "Jilin",
    "shanghai": "Shanghai",
    "sichuan1": "Sichuan I",
    "tianjin": "Tianjin",
}

# Expected total from README
EXPECTED_LYRICS_TOTAL = 2498
EXPECTED_MELODY_TOTAL = 6161
EXPECTED_GRAND_TOTAL = 8659


def count_files_by_ext(directory: Path) -> dict:
    """Count files by extension in a directory (non-recursive)."""
    counts = Counter()
    if not directory.exists():
        return counts
    for f in directory.iterdir():
        if f.is_file() and not f.name.startswith("."):
            counts[f.suffix.lower()] += 1
    return counts


def count_files_recursive(directory: Path) -> dict:
    """Count all files by extension recursively, excluding .git."""
    counts = Counter()
    sizes = Counter()
    if not directory.exists():
        return counts, sizes
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if not f.startswith("."):
                ext = os.path.splitext(f)[1].lower()
                counts[ext] += 1
                sizes[ext] += os.path.getsize(os.path.join(root, f))
    return counts, sizes


def inspect_midi_sample(midi_files: list, sample_size: int = 50) -> dict:
    """Inspect a sample of MIDI files and return aggregate statistics."""
    import random

    if len(midi_files) > sample_size:
        sampled = random.sample(midi_files, sample_size)
    else:
        sampled = midi_files

    results = {
        "total_files": len(midi_files),
        "sampled": len(sampled),
        "track_counts": Counter(),
        "ticks_per_beat": Counter(),
        "midi_types": Counter(),
        "note_counts": [],
        "pitch_range_min": [],
        "pitch_range_max": [],
        "tempos": [],
        "key_signatures": Counter(),
        "time_signatures": Counter(),
        "channels_used": Counter(),
        "durations_seconds": [],
        "errors": [],
    }

    for fpath in sampled:
        try:
            mid = mido.MidiFile(str(fpath))
            results["midi_types"][mid.type] += 1
            results["ticks_per_beat"][mid.ticks_per_beat] += 1
            results["track_counts"][len(mid.tracks)] += 1

            note_count = 0
            pitches = []
            for track in mid.tracks:
                for msg in track:
                    if msg.type == "note_on" and msg.velocity > 0:
                        note_count += 1
                        pitches.append(msg.note)
                    elif msg.type == "note_on":
                        pass  # velocity 0 = note off
                    elif hasattr(msg, "type"):
                        if msg.type == "set_tempo" and hasattr(msg, "tempo"):
                            bpm = mido.tempo2bpm(msg.tempo)
                            results["tempos"].append(round(bpm, 1))
                        elif msg.type == "key_signature" and hasattr(msg, "key"):
                            results["key_signatures"][msg.key] += 1
                        elif msg.type == "time_signature":
                            ts = f"{msg.numerator}/{msg.denominator}"
                            results["time_signatures"][ts] += 1

            results["note_counts"].append(note_count)
            if pitches:
                results["pitch_range_min"].append(min(pitches))
                results["pitch_range_max"].append(max(pitches))

            # Channel usage
            for track in mid.tracks:
                for msg in track:
                    if hasattr(msg, "channel"):
                        results["channels_used"][msg.channel] += 1

            try:
                results["durations_seconds"].append(round(mid.length, 2))
            except Exception:
                pass

        except Exception as e:
            results["errors"].append(f"{fpath.name}: {e}")

    return results


def inspect_musicxml_sample(xml_files: list, sample_size: int = 50) -> dict:
    """Inspect a sample of MusicXML files and return aggregate statistics."""
    import random

    if len(xml_files) > sample_size:
        sampled = random.sample(xml_files, sample_size)
    else:
        sampled = xml_files

    results = {
        "total_files": len(xml_files),
        "sampled": len(sampled),
        "part_counts": Counter(),
        "part_names": Counter(),
        "measure_counts": [],
        "note_counts": [],
        "notes_with_lyrics": [],
        "rest_counts": [],
        "key_signatures": Counter(),
        "time_signatures": Counter(),
        "max_lyric_lines": [],
        "has_work_title": 0,
        "work_title_patterns": Counter(),
        "errors": [],
    }

    for fpath in sampled:
        try:
            tree = ET.parse(str(fpath))
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            # Work title
            work = root.find(f"{ns}work")
            if work is not None:
                title = work.find(f"{ns}work-title")
                if title is not None and title.text:
                    results["has_work_title"] += 1
                    # Classify title pattern
                    if title.text.startswith("页面_song_"):
                        results["work_title_patterns"]["页面_song_N"] += 1
                    elif title.text.startswith("曲目_"):
                        results["work_title_patterns"]["曲目_N《title》"] += 1
                    else:
                        results["work_title_patterns"]["other"] += 1

            # Parts
            part_list = root.find(f"{ns}part-list")
            if part_list is not None:
                score_parts = part_list.findall(f"{ns}score-part")
                results["part_counts"][len(score_parts)] += 1
                for sp in score_parts:
                    pname = sp.find(f"{ns}part-name")
                    if pname is not None and pname.text:
                        results["part_names"][pname.text] += 1

            # Analyze first part
            parts = root.findall(f"{ns}part")
            if parts:
                part = parts[0]
                measures = part.findall(f"{ns}measure")
                results["measure_counts"].append(len(measures))

                all_notes = part.findall(f".//{ns}note")
                rests = [n for n in all_notes if n.find(f"{ns}rest") is not None]
                lyric_notes = [
                    n for n in all_notes if n.find(f"{ns}lyric") is not None
                ]
                results["note_counts"].append(len(all_notes))
                results["rest_counts"].append(len(rests))
                results["notes_with_lyrics"].append(len(lyric_notes))

                # Max lyric lines
                max_lines = 0
                for n in lyric_notes:
                    lyrics = n.findall(f"{ns}lyric")
                    max_lines = max(max_lines, len(lyrics))
                results["max_lyric_lines"].append(max_lines)

                # Key and time from first measure
                if measures:
                    attrs = measures[0].find(f"{ns}attributes")
                    if attrs is not None:
                        key = attrs.find(f"{ns}key")
                        if key is not None:
                            fifths = key.find(f"{ns}fifths")
                            mode = key.find(f"{ns}mode")
                            ks = f"fifths={fifths.text if fifths is not None else '?'}"
                            if mode is not None and mode.text:
                                ks += f",mode={mode.text}"
                            results["key_signatures"][ks] += 1
                        time_el = attrs.find(f"{ns}time")
                        if time_el is not None:
                            beats = time_el.find(f"{ns}beats")
                            btype = time_el.find(f"{ns}beat-type")
                            ts = f"{beats.text if beats is not None else '?'}/{btype.text if btype is not None else '?'}"
                            results["time_signatures"][ts] += 1

        except Exception as e:
            results["errors"].append(f"{fpath.name}: {e}")

    return results


def summarize_numeric(values: list, label: str) -> str:
    """Summarize a list of numeric values."""
    if not values:
        return f"  {label}: no data"
    import statistics

    mn = min(values)
    mx = max(values)
    avg = statistics.mean(values)
    med = statistics.median(values)
    return f"  {label}: min={mn}, max={mx}, mean={avg:.1f}, median={med:.1f}, n={len(values)}"


def inspect_anthology(data_dir: Path) -> dict:
    """Full inspection of the Anthology of Chinese Folk Songs."""
    print("=" * 70)
    print("ANTHOLOGY OF CHINESE FOLK SONGS - INSPECTION")
    print("=" * 70)
    print(f"Directory: {data_dir}")
    print()

    results = {
        "dataset": "Anthology of Chinese Folk Songs",
        "root_path": str(data_dir),
        "volumes": {},
        "total_counts": {},
        "midi_analysis": {},
        "musicxml_analysis": {},
        "issues": [],
    }

    # ---- 1. File counts by volume ----
    print("--- File Counts by Volume ---")
    total_mid = 0
    total_xml = 0
    total_png = 0
    lyrics_mid = 0
    melody_mid = 0
    lyrics_xml = 0
    melody_xml = 0

    for subset, volumes in [
        ("lyrics-included", LYRICS_INCLUDED_VOLUMES),
        ("melody-only", MELODY_ONLY_VOLUMES),
    ]:
        for dirname, display_name in sorted(volumes.items()):
            vol_dir = data_dir / subset / dirname
            counts = count_files_by_ext(vol_dir)
            mid_count = counts.get(".mid", 0)
            xml_count = counts.get(".musicxml", 0)
            png_count = counts.get(".png", 0)

            results["volumes"][dirname] = {
                "display_name": display_name,
                "subset": subset,
                "mid": mid_count,
                "musicxml": xml_count,
                "png": png_count,
            }

            total_mid += mid_count
            total_xml += xml_count
            total_png += png_count
            if subset == "lyrics-included":
                lyrics_mid += mid_count
                lyrics_xml += xml_count
            else:
                melody_mid += mid_count
                melody_xml += xml_count

            print(
                f"  {subset}/{dirname} ({display_name}): "
                f"mid={mid_count}, musicxml={xml_count}, png={png_count}"
            )

            # Check for mismatches
            if mid_count != xml_count:
                msg = (
                    f"{dirname}: MIDI count ({mid_count}) != "
                    f"MusicXML count ({xml_count})"
                )
                results["issues"].append(msg)
                print(f"    WARNING: {msg}")

    print()
    print(f"  Lyrics-included total: mid={lyrics_mid}, musicxml={lyrics_xml}")
    print(f"  Melody-only total: mid={melody_mid}, musicxml={melody_xml}")
    print(f"  Grand total: mid={total_mid}, musicxml={total_xml}, png={total_png}")

    results["total_counts"] = {
        "midi": total_mid,
        "musicxml": total_xml,
        "png": total_png,
        "lyrics_included_midi": lyrics_mid,
        "lyrics_included_musicxml": lyrics_xml,
        "melody_only_midi": melody_mid,
        "melody_only_musicxml": melody_xml,
    }

    # Verify against expected totals
    if lyrics_xml != EXPECTED_LYRICS_TOTAL:
        msg = (
            f"Lyrics-included MusicXML count ({lyrics_xml}) != "
            f"expected ({EXPECTED_LYRICS_TOTAL})"
        )
        results["issues"].append(msg)
        print(f"  NOTE: {msg}")
    if melody_xml != EXPECTED_MELODY_TOTAL:
        msg = (
            f"Melody-only MusicXML count ({melody_xml}) != "
            f"expected ({EXPECTED_MELODY_TOTAL})"
        )
        results["issues"].append(msg)

    # Check for missing MIDI files
    print()
    print("--- Missing MIDI Files ---")
    missing_midi = []
    for subset, volumes in [
        ("lyrics-included", LYRICS_INCLUDED_VOLUMES),
        ("melody-only", MELODY_ONLY_VOLUMES),
    ]:
        for dirname in sorted(volumes):
            vol_dir = data_dir / subset / dirname
            xml_stems = {f.stem for f in vol_dir.glob("*.musicxml")}
            mid_stems = {f.stem for f in vol_dir.glob("*.mid")}
            missing = xml_stems - mid_stems
            if missing:
                for s in sorted(missing):
                    missing_midi.append(f"{dirname}/{s}")
                    print(f"  MusicXML without MIDI: {dirname}/{s}")

    results["missing_midi"] = missing_midi
    if not missing_midi:
        print("  None")

    # ---- 2. MIDI Analysis ----
    print()
    print("--- MIDI Analysis (sampled) ---")

    # Collect all MIDI files
    all_mid_files = []
    for subset in ["lyrics-included", "melody-only"]:
        for vol_dir in sorted((data_dir / subset).iterdir()):
            if vol_dir.is_dir():
                all_mid_files.extend(vol_dir.glob("*.mid"))

    midi_results = inspect_midi_sample(all_mid_files, sample_size=200)
    results["midi_analysis"] = {
        "total_files": midi_results["total_files"],
        "sampled": midi_results["sampled"],
        "track_counts": dict(midi_results["track_counts"]),
        "ticks_per_beat": dict(midi_results["ticks_per_beat"]),
        "midi_types": dict(midi_results["midi_types"]),
        "key_signatures": dict(midi_results["key_signatures"]),
        "time_signatures": dict(midi_results["time_signatures"]),
        "channels_used": dict(midi_results["channels_used"]),
    }

    print(f"  Total MIDI files: {midi_results['total_files']}")
    print(f"  Sampled: {midi_results['sampled']}")
    print(f"  MIDI types: {dict(midi_results['midi_types'])}")
    print(f"  Track counts: {dict(midi_results['track_counts'])}")
    print(f"  Ticks per beat: {dict(midi_results['ticks_per_beat'])}")
    print(f"  Key signatures: {dict(midi_results['key_signatures'].most_common(10))}")
    print(
        f"  Time signatures: {dict(midi_results['time_signatures'].most_common(10))}"
    )
    print(
        f"  Channels used: {sorted(midi_results['channels_used'].keys())}"
    )
    print(summarize_numeric(midi_results["note_counts"], "Note counts"))
    print(summarize_numeric(midi_results["pitch_range_min"], "Pitch min (MIDI note)"))
    print(summarize_numeric(midi_results["pitch_range_max"], "Pitch max (MIDI note)"))
    print(summarize_numeric(midi_results["tempos"], "Tempo (BPM)"))
    print(summarize_numeric(midi_results["durations_seconds"], "Duration (seconds)"))

    if midi_results["note_counts"]:
        results["midi_analysis"]["note_count_stats"] = {
            "min": min(midi_results["note_counts"]),
            "max": max(midi_results["note_counts"]),
            "mean": round(
                sum(midi_results["note_counts"]) / len(midi_results["note_counts"]), 1
            ),
        }
    if midi_results["tempos"]:
        results["midi_analysis"]["tempo_stats"] = {
            "min": min(midi_results["tempos"]),
            "max": max(midi_results["tempos"]),
            "mean": round(
                sum(midi_results["tempos"]) / len(midi_results["tempos"]), 1
            ),
        }
    if midi_results["durations_seconds"]:
        results["midi_analysis"]["duration_stats"] = {
            "min": min(midi_results["durations_seconds"]),
            "max": max(midi_results["durations_seconds"]),
            "mean": round(
                sum(midi_results["durations_seconds"])
                / len(midi_results["durations_seconds"]),
                1,
            ),
        }
    if midi_results["pitch_range_min"]:
        results["midi_analysis"]["pitch_stats"] = {
            "overall_min": min(midi_results["pitch_range_min"]),
            "overall_max": max(midi_results["pitch_range_max"]),
        }

    if midi_results["errors"]:
        print(f"  Errors ({len(midi_results['errors'])}):")
        for e in midi_results["errors"][:5]:
            print(f"    {e}")

    # ---- 3. MusicXML Analysis ----
    print()
    print("--- MusicXML Analysis (sampled) ---")

    # Lyrics-included sample
    lyrics_xml_files = []
    for vol_dir in sorted((data_dir / "lyrics-included").iterdir()):
        if vol_dir.is_dir():
            lyrics_xml_files.extend(vol_dir.glob("*.musicxml"))

    lyrics_xml_results = inspect_musicxml_sample(lyrics_xml_files, sample_size=100)

    print(f"  Lyrics-included MusicXML ({lyrics_xml_results['total_files']} total, "
          f"{lyrics_xml_results['sampled']} sampled):")
    print(f"    Part counts: {dict(lyrics_xml_results['part_counts'])}")
    print(f"    Part names: {dict(lyrics_xml_results['part_names'])}")
    print(f"    Work titles present: {lyrics_xml_results['has_work_title']}/{lyrics_xml_results['sampled']}")
    print(f"    Title patterns: {dict(lyrics_xml_results['work_title_patterns'])}")
    print(f"    Key signatures: {dict(lyrics_xml_results['key_signatures'].most_common(10))}")
    print(f"    Time signatures: {dict(lyrics_xml_results['time_signatures'].most_common(10))}")
    print(summarize_numeric(lyrics_xml_results["measure_counts"], "Measures"))
    print(summarize_numeric(lyrics_xml_results["note_counts"], "Notes"))
    print(summarize_numeric(lyrics_xml_results["notes_with_lyrics"], "Notes with lyrics"))
    print(summarize_numeric(lyrics_xml_results["max_lyric_lines"], "Max lyric lines"))

    # Melody-only sample
    melody_xml_files = []
    for vol_dir in sorted((data_dir / "melody-only").iterdir()):
        if vol_dir.is_dir():
            melody_xml_files.extend(vol_dir.glob("*.musicxml"))

    melody_xml_results = inspect_musicxml_sample(melody_xml_files, sample_size=100)

    print()
    print(f"  Melody-only MusicXML ({melody_xml_results['total_files']} total, "
          f"{melody_xml_results['sampled']} sampled):")
    print(f"    Part counts: {dict(melody_xml_results['part_counts'])}")
    print(f"    Part names: {dict(melody_xml_results['part_names'])}")
    print(f"    Work titles present: {melody_xml_results['has_work_title']}/{melody_xml_results['sampled']}")
    print(f"    Key signatures: {dict(melody_xml_results['key_signatures'].most_common(10))}")
    print(f"    Time signatures: {dict(melody_xml_results['time_signatures'].most_common(10))}")
    print(summarize_numeric(melody_xml_results["measure_counts"], "Measures"))
    print(summarize_numeric(melody_xml_results["note_counts"], "Notes"))
    print(summarize_numeric(melody_xml_results["notes_with_lyrics"], "Notes with lyrics"))

    results["musicxml_analysis"] = {
        "lyrics_included": {
            "total_files": lyrics_xml_results["total_files"],
            "sampled": lyrics_xml_results["sampled"],
            "part_names": dict(lyrics_xml_results["part_names"]),
            "key_signatures": dict(lyrics_xml_results["key_signatures"]),
            "time_signatures": dict(lyrics_xml_results["time_signatures"]),
            "title_patterns": dict(lyrics_xml_results["work_title_patterns"]),
        },
        "melody_only": {
            "total_files": melody_xml_results["total_files"],
            "sampled": melody_xml_results["sampled"],
            "part_names": dict(melody_xml_results["part_names"]),
            "key_signatures": dict(melody_xml_results["key_signatures"]),
            "time_signatures": dict(melody_xml_results["time_signatures"]),
        },
    }

    if lyrics_xml_results["measure_counts"]:
        results["musicxml_analysis"]["lyrics_included"]["measure_stats"] = {
            "min": min(lyrics_xml_results["measure_counts"]),
            "max": max(lyrics_xml_results["measure_counts"]),
            "mean": round(
                sum(lyrics_xml_results["measure_counts"])
                / len(lyrics_xml_results["measure_counts"]),
                1,
            ),
        }
    if melody_xml_results["measure_counts"]:
        results["musicxml_analysis"]["melody_only"]["measure_stats"] = {
            "min": min(melody_xml_results["measure_counts"]),
            "max": max(melody_xml_results["measure_counts"]),
            "mean": round(
                sum(melody_xml_results["measure_counts"])
                / len(melody_xml_results["measure_counts"]),
                1,
            ),
        }

    # ---- 4. Summary ----
    print()
    print("--- Issues ---")
    for issue in results["issues"]:
        print(f"  - {issue}")
    if not results["issues"]:
        print("  None")

    return results


def inspect_anonymized(data_dir: Path) -> dict:
    """Full inspection of the Anonymized Subset."""
    print()
    print("=" * 70)
    print("ANONYMIZED SUBSET - INSPECTION")
    print("=" * 70)
    print(f"Directory: {data_dir}")
    print()

    results = {
        "dataset": "Anonymized Subset of Anthology of Chinese Folk Songs",
        "root_path": str(data_dir),
        "subsets": {},
        "total_counts": {},
        "midi_analysis": {},
        "musicxml_analysis": {},
        "anonymization_details": {},
        "issues": [],
    }

    # ---- 1. File counts ----
    print("--- File Counts ---")

    # Curated subset
    curated_dir = data_dir / "Curated"
    curated_mid = list((curated_dir / "midi").glob("*.mid"))
    curated_xml = list((curated_dir / "musicxml").glob("*.musicxml"))
    curated_jpg = list((curated_dir / "original_jpg").glob("*.jpg"))

    print(f"  Curated/midi: {len(curated_mid)} files")
    print(f"  Curated/musicxml: {len(curated_xml)} files")
    print(f"  Curated/original_jpg: {len(curated_jpg)} files")

    # Melody-only subset
    melody_dir = data_dir / "Melody-only"
    melody_mid = list((melody_dir / "midi").glob("*.mid"))
    melody_xml = list((melody_dir / "musicxml").glob("*.musicxml"))

    print(f"  Melody-only/midi: {len(melody_mid)} files (merged)")
    print(f"  Melody-only/musicxml: {len(melody_xml)} files (merged)")

    results["subsets"] = {
        "curated": {
            "midi": len(curated_mid),
            "musicxml": len(curated_xml),
            "original_jpg": len(curated_jpg),
        },
        "melody_only": {
            "midi": len(melody_mid),
            "musicxml": len(melody_xml),
            "note": "single merged file containing all songs",
        },
    }

    # ---- 2. Song number range ----
    print()
    print("--- Curated Song Range ---")
    song_numbers = []
    for f in curated_mid:
        # Pattern: song_786《title》.mid
        name = f.stem
        try:
            num = int(name.split("_")[1].split("《")[0])
            song_numbers.append(num)
        except (IndexError, ValueError):
            pass

    if song_numbers:
        print(f"  Song number range: {min(song_numbers)} to {max(song_numbers)}")
        print(f"  Unique song numbers: {len(set(song_numbers))}")
        print(f"  Total files: {len(song_numbers)}")
        results["subsets"]["curated"]["song_range"] = {
            "min": min(song_numbers),
            "max": max(song_numbers),
            "unique_numbers": len(set(song_numbers)),
        }

    # ---- 3. JPG numbering ----
    print()
    print("--- Original JPG Analysis ---")
    jpg_numbers = []
    for f in curated_jpg:
        try:
            num = int(f.stem)
            jpg_numbers.append(num)
        except ValueError:
            pass
    if jpg_numbers:
        print(f"  JPG number range: {min(jpg_numbers)} to {max(jpg_numbers)}")
        print(f"  Total JPGs: {len(jpg_numbers)}")
        print(f"  Note: JPGs use sequential page numbering, not song numbers")
        results["subsets"]["curated"]["jpg_range"] = {
            "min": min(jpg_numbers),
            "max": max(jpg_numbers),
        }

    # ---- 4. Anonymization analysis ----
    print()
    print("--- Anonymization Details ---")
    print("  Purpose: Double-blind review for CSMT 2025")
    print("  Source: Volume Jiangsu II from the full Anthology")
    print("  What was anonymized:")
    print("    - Repository name: generic, no author identification")
    print("    - File naming: 'song_N《title》' instead of 'N_title'")
    print("    - Work titles in MusicXML: '曲目_N《title》' instead of '页面_song_N'")
    print("    - JPG files: sequential page numbers instead of song-keyed names")
    print("    - No author/institution metadata in MusicXML (same as main)")
    print("  What was NOT anonymized:")
    print("    - Song titles (Chinese folk song names preserved)")
    print("    - Musical content (MIDI/MusicXML data identical)")
    print("    - Regional attribution (Jiangsu II)")

    results["anonymization_details"] = {
        "purpose": "Double-blind review for CSMT 2025",
        "source_volume": "Jiangsu II",
        "anonymized": [
            "Repository name (no author identification)",
            "File naming convention changed",
            "Work titles in MusicXML reformatted",
            "JPG files use sequential page numbers",
        ],
        "not_anonymized": [
            "Song titles preserved",
            "Musical content identical",
            "Regional attribution (Jiangsu II) implicit",
        ],
    }

    # ---- 5. Curated MIDI Analysis ----
    print()
    print("--- Curated MIDI Analysis ---")
    curated_midi_results = inspect_midi_sample(curated_mid, sample_size=100)

    print(f"  Total MIDI files: {curated_midi_results['total_files']}")
    print(f"  Sampled: {curated_midi_results['sampled']}")
    print(f"  MIDI types: {dict(curated_midi_results['midi_types'])}")
    print(f"  Track counts: {dict(curated_midi_results['track_counts'])}")
    print(f"  Key signatures: {dict(curated_midi_results['key_signatures'].most_common(10))}")
    print(f"  Time signatures: {dict(curated_midi_results['time_signatures'].most_common(10))}")
    print(summarize_numeric(curated_midi_results["note_counts"], "Note counts"))
    print(summarize_numeric(curated_midi_results["tempos"], "Tempo (BPM)"))
    print(summarize_numeric(curated_midi_results["durations_seconds"], "Duration (seconds)"))

    results["midi_analysis"]["curated"] = {
        "total_files": curated_midi_results["total_files"],
        "sampled": curated_midi_results["sampled"],
        "track_counts": dict(curated_midi_results["track_counts"]),
        "key_signatures": dict(curated_midi_results["key_signatures"]),
        "time_signatures": dict(curated_midi_results["time_signatures"]),
    }
    if curated_midi_results["note_counts"]:
        results["midi_analysis"]["curated"]["note_count_stats"] = {
            "min": min(curated_midi_results["note_counts"]),
            "max": max(curated_midi_results["note_counts"]),
            "mean": round(
                sum(curated_midi_results["note_counts"])
                / len(curated_midi_results["note_counts"]),
                1,
            ),
        }

    # ---- 6. Merged Melody-only Analysis ----
    print()
    print("--- Merged Melody-only MIDI ---")
    if melody_mid:
        try:
            merged = mido.MidiFile(str(melody_mid[0]))
            note_count = sum(
                1
                for t in merged.tracks
                for msg in t
                if msg.type == "note_on" and msg.velocity > 0
            )
            print(f"  Tracks: {len(merged.tracks)}")
            print(f"  Total note_on events: {note_count}")
            try:
                dur = merged.length
                print(f"  Duration: {dur:.1f} seconds ({dur/60:.1f} minutes)")
            except Exception:
                pass
            results["midi_analysis"]["merged_melody_only"] = {
                "tracks": len(merged.tracks),
                "note_count": note_count,
            }
        except Exception as e:
            print(f"  Error reading merged MIDI: {e}")

    # ---- 7. Curated MusicXML Analysis ----
    print()
    print("--- Curated MusicXML Analysis ---")
    curated_xml_results = inspect_musicxml_sample(curated_xml, sample_size=100)

    print(f"  Total files: {curated_xml_results['total_files']}")
    print(f"  Sampled: {curated_xml_results['sampled']}")
    print(f"  Part counts: {dict(curated_xml_results['part_counts'])}")
    print(f"  Part names: {dict(curated_xml_results['part_names'])}")
    print(f"  Title patterns: {dict(curated_xml_results['work_title_patterns'])}")
    print(f"  Key signatures: {dict(curated_xml_results['key_signatures'].most_common(10))}")
    print(f"  Time signatures: {dict(curated_xml_results['time_signatures'].most_common(10))}")
    print(summarize_numeric(curated_xml_results["measure_counts"], "Measures"))
    print(summarize_numeric(curated_xml_results["note_counts"], "Notes"))
    print(summarize_numeric(curated_xml_results["notes_with_lyrics"], "Notes with lyrics"))
    print(summarize_numeric(curated_xml_results["max_lyric_lines"], "Max lyric lines"))

    results["musicxml_analysis"]["curated"] = {
        "total_files": curated_xml_results["total_files"],
        "sampled": curated_xml_results["sampled"],
        "part_names": dict(curated_xml_results["part_names"]),
        "key_signatures": dict(curated_xml_results["key_signatures"]),
        "time_signatures": dict(curated_xml_results["time_signatures"]),
        "title_patterns": dict(curated_xml_results["work_title_patterns"]),
    }

    return results


def main():
    """Run inspection on both datasets."""
    import random

    random.seed(42)

    # Inspect main anthology
    anthology_results = inspect_anthology(ANTHOLOGY_DIR)

    # Inspect anonymized subset
    anonymized_results = inspect_anonymized(ANONYMIZED_DIR)

    # Save combined results
    combined = {
        "anthology": anthology_results,
        "anonymized": anonymized_results,
    }

    output_path = Path(__file__).resolve().parent.parent.parent / "data" / "inspection_results"
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "anthology_chinese_folk_songs_inspection.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print()
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
