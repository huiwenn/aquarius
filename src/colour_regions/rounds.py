"""
The collection rounds of the corpus, in one place. Every script that reads audio, manifests or transcriptions per
round takes its paths from here, so a new round needs no code changes:

  Round 1   data/regions_audio/ (audio, manifest.csv, id column video_id), data/regions_transcription/ (transcription),
            F0 in data/transcription/critic/
  Round N≥2 data/regions_v<N>/ with  audio/<region>/<id>.<ext>,  manifest.csv (id column `id`, round-2 format),
            transcription/ (vocals, accomp, midi, musicxml, f0_rmvpe, f0_pesto, dataset_index.csv)

A round is discovered when data/regions_v<N>/manifest.csv exists. See .claude/skills/colour-regions-curation.
"""

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data"


@dataclass(frozen=True)
class Round:
    n: int
    base: Path
    audio: Path
    manifest: Path
    id_col: str
    trans: Path
    f0: Path

    @property
    def index(self) -> Path:
        return self.trans / "dataset_index.csv"


def rounds() -> dict[int, Round]:
    out = {1: Round(1, D / "regions_audio", D / "regions_audio", D / "regions_audio" / "manifest.csv", "video_id",
                    D / "regions_transcription", D / "transcription" / "critic")}
    for p in sorted(D.glob("regions_v*/manifest.csv")):
        m = re.fullmatch(r"regions_v(\d+)", p.parent.name)
        if m and int(m.group(1)) >= 2:
            b = p.parent
            out[int(m.group(1))] = Round(int(m.group(1)), b, b / "audio", p, "id", b / "transcription",
                                         b / "transcription")
    return dict(sorted(out.items()))
