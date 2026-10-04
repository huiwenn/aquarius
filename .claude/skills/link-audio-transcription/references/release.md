# Releasing a link-based audio dataset

## What to release

- **Release:** links, curation metadata, derived data (F0 tracks, MIDI/MusicXML, features), quality flags, search logs and code.
- **Do not release** the audio.
- **Precedents:** AudioSet and DALI.

## Verification of re-downloads

- **At release time**, run `scripts/fingerprints.py`. It writes Chromaprint fingerprints of the first 120 s in two forms:
  - compressed (the AcoustID form);
  - raw (a JSON list of 32-bit integers).
- **When a user downloads**, `scripts/verify_download.py` checks each file:
  - duration within ±2 s of the released value;
  - bit error rate over aligned sub-fingerprints ≤ 0.25, searched over ±20 frame offsets.
- **Mismatches:** mark them in a report rather than deleting the file. Derived data may still be usable, but the user should know.

## Link decay

- Run `scripts/link_check.py` at each release, and keep the dated results; the script appends.
- Report the availability per platform in the paper or datasheet.
- The derived data stays usable when links die.

## Paths and portability

- Use relative symlinks (`os.path.relpath(target, link.parent)`), and repo-relative paths in every CSV.
- Get every number in a paper from data through a script, so that reruns update the text.

## Privacy

- **Names:** publish personal names only for people with a public role (for example, national heritage-bearer lists). Give everyone else a pseudonymous `singer_id`, assigned per normalised name.
- **Free text:** redact non-public names from curator evidence text.
  - Match only names in the script of the language (for example Chinese characters). Short Latin strings matched inside ordinary words.
  - Never redact a substring of a public name.
- **Titles:** keep source titles as published, since the link exposes them anyway, and say so.
- **Removal:** offer a removal route, and process removals at the next version.

## Licensing

- **Derived data** inherits constraints from its inputs. For example, scores derived from CC BY-NC-SA OMR data stay NC-SA.
- **Archive items** marked "In Copyright, research use only": release links and metadata only, until permission is given.
- **Platform terms:** the user obtains audio under the platform's terms. Do not bundle cookies or credentials in the release.

## Groups for evaluation

Recordings from the same channel or singer share confounds. Give a `group_id`: the connected components of "same channel" ∪ "same singer" (union-find). Recommend folds grouped by it, with songs held disjoint, and report the size of the largest group.
