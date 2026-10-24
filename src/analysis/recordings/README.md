# Analysis of the transcribed recordings

Exploratory analyses of how the 15 colour regions differ in scale, intonation, rhythm and melody, how far the regions follow geography, and how well the music predicts the region. The results are written up in `docs/recordings_analysis.md`.

These scripts measure the **transcribed recordings** (F0 tracks and primary MIDI). `../musical_elements.py` analyses the Essen scores and the metadata instead. All results are **exploratory** (evidence rule in `CLAUDE.md`).

## Run order

Run every script from the repo root. Each one writes to its own folder under `data/analysis/recordings/` (gitignored). Later scripts read the tables of earlier ones.

| Step | Script | Reads | Writes (`data/analysis/recordings/…`) |
|---|---|---|---|
| 1 | `scales_by_region.py` | F0 (RMVPE) | `scales/`: pentatonic fit, non-pentatonic notes, mode of the final note. Also a shared module (paths, plotting style, `cluster_boot`) |
| 2 | `intonation_by_region.py` | F0 | `intonation/`: distance from the piano grid, drift, deviation per scale degree |
| 3 | `rhythm_by_region.py` | primary MIDI | `rhythm/`: notes per second, held notes, pauses, speed variation |
| 4 | `melody_by_region.py` | primary MIDI | `melody/`: range, intervals, leaps, phrase contour |
| 5 | `region_profiles.py` | steps 1–4 | `profiles/`: one profile per region, clusters, resampling stability, Mantel test |
| 6 | `geography_vs_music.py` | steps 1–5 | `geography/`: distance decay, Mantel tests per measure, gradients, region pairs that break the pattern |
| 7 | `region_classifier.py` | steps 1–4 | `classifier/`: region classifier under the strict protocol |
| 8 | `genre_breakdown.py` | steps 1–7 | `genre/`: genre against region |
| 9 | `style_folk_vs_trained.py` | steps 1–4 | `style/`: folk (原生态) against trained (民族唱法) singing |
| 10 | `confusion_blocks.py` | steps 5 and 7 | `classifier/`: confusion matrix with the region groups outlined |

```
for s in scales_by_region intonation_by_region rhythm_by_region melody_by_region region_profiles \
         geography_vs_music region_classifier genre_breakdown style_folk_vs_trained confusion_blocks; do
  python src/analysis/recordings/$s.py
done
python src/analysis/recordings/scales_by_region.py --min-margin 0.05 --out data/analysis/recordings/scales_clear   # optional: clear fits only
```

All ten scripts take `--out` (output folder). Steps 1–4 take `--all` to include non-core recordings. The whole run takes about two minutes.

## Inputs

- `metadata/recordings.csv`: region, group, genre, performance type, place. Only `core` recordings are analysed.
- **Transcriptions:** the shared transcription package (F0 in `f0/rmvpe/<region>/`, MIDI in `midi/primary/<region>/`). The default location is `../colour_regions_share`. Set the environment variable `AQUARIUS_SHARE` to use another folder. Round folders `data/regions_v*/transcription/` in this repo are read as well. A recording without a transcription is skipped, and each script prints how many.
- Python: numpy, pandas, scipy, scikit-learn, matplotlib and pretty_midi. The charts use a CJK font if one is installed (PingFang SC on macOS).

## Conventions

- **Uncertainty:** intervals resample whole groups (`group_id`: channel or singer), not single recordings. Recordings from one performer are not independent.
- **Folds** (step 7 and the scripts that import it): `add_folds` from `src/colour_regions/build_release.py`, computed from `metadata/recordings.csv`. A training set also drops every recording whose `song_key` occurs in the test fold. Models see musical measures only: no channel, place, genre or title. Settings are fixed in advance and are not tuned on test data.
- **Measures that are not reported,** because tests showed they cannot be trusted (details in `docs/recordings_analysis.md`): beats per minute and metre, glide share from the pitch tracks, and mode shares as a main result.
- No audio and nothing from `data/` goes into git.
