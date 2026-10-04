# Annotation guideline: expert notation of Chinese folk-song excerpts

**Version 1.1-draft, 2026-10-02.** Revised after review 02 (`../colour_regions_paper/reviews/review_02.md` §3). After the pilot, it becomes v1.1 and is frozen, and its sha256 is logged in `docs/thesis_evidence_plan.md`.

Background: `docs/thesis_evidence_plan.md`, sections A0–A2.

## Purpose

Three notators notate the same excerpts of Chinese folk singing, independently. We compare your notations with each other, with machine transcription, and with printed scores.

**Notate as you would for a publication that other experts will check.** We compare notations; we do not grade them. Do not move the singer toward a scale or a beat that the singer does not use.

Please do not:
- discuss the excerpts with the other notators;
- look up the songs;
- use any automatic transcription or pitch-to-MIDI tool. A pitch display (spectrogram or pitch curve) is allowed **only for the performance layer** (step 2 below).

## What you receive

| File | Content |
|---|---|
| `E##_mix.wav` | **Primary audio.** The original recording: the excerpt plus 2 s of context before and after. |
| `E##_guide.wav` | A click track: a 1 kHz click at the start and at the end of the excerpt. |
| `E##_voice.wav` | Optional. The voice, separated from the accompaniment by software. It can add or remove details, so trust the mix. Log when you used it. |
| `E##_info.txt` | The start and end time of the excerpt inside the mix file. |

All times are measured from the start of `E##_mix.wav`. The reference tuning is A4 = 440 Hz; do not retune.

Region, genre, song title and singer are withheld. You may still recognise a region or a song. That is expected: tell us your guess (step 4).

The audio is for this task only. Do not share it, and delete it when the task is finished.

## Order and sessions

- Do the excerpts **in the order on your list**. Each notator has a different order.
- Work in sessions of **at most 2 hours**, and note the date and time of each session.
- Some excerpts appear twice under different IDs. Treat every excerpt as new.
- Excerpt `E00` is a **calibration excerpt**. Notate it first and send it to us. We check only the format (times, columns, file names), and we do not comment on musical choices.

## Step 1: skeleton layer, by ear (`E##_<id>_jianpu.txt`)

Write the skeleton **first**, by ear, **without a pitch display**. Write it in numbered notation (简谱), as you would for a printed collection in the style of 《中国民间歌曲集成》.

Use the strict text format in `jianpu_examples.txt`:
- **Header:** the key (`1=D`) and the metre (`2/4`, or `散板`).
- **Notes:** degrees `1`–`7` and `0` for a rest, with octave marks written `,` (low) and `'` (high). Duration marks and the grammar are in the examples.
- **Grace notes:** only the ones you would print, in parentheses, for example `(6)5`.
- **Altered degrees:** if you would print them, write `#4`, `b7`, or the neutral-tone marks `4^` (raised) and `7v` (lowered).
- **Links (required):** after step 2, give each skeleton note the event IDs of the performance rows that it reduces, in braces, for example `5{e12,e13}`.

## Step 2: performance layer (`E##_<id>_performance.csv`)

Use Sonic Visualiser or Tony, and send us the session file (`.sv` or `.ton`) as well. Make one row per sung event.

| Column | Meaning |
|---|---|
| `event_id` | A unique ID inside the file: `e1`, `e2`, … |
| `onset_s` | The start of the event (for a scooped note, the start of the scoop), to 0.01 s. |
| `arrival_s` | For a scooped note, the time at which the main pitch is reached. Otherwise empty. |
| `offset_s` | The end of the event. |
| `steady_start_s`, `steady_end_s` | The **steady span**: the part after any scoop and before any release, where the pitch does not move in one direction by more than about a quarter tone. We compute the pitch of the span from the audio; you do not need to read cents. Leave both empty for a `glide`. |
| `type` | `note`, `grace`, `glide`, `vocable_note`, `spoken`, or `non_pitched` (breath, sob, laugh). |
| `glide_from`, `glide_to` | For glides, scoops and thrown endings: the start and end pitch, as a MIDI number (for example `62.3`). |
| `scoop_in`, `vibrato`, `throw`, `neutral`, `falsetto`, `glottal` | Attributes. Write 1 if the attribute is present, else leave empty. `neutral` means you hear the pitch as between two scale degrees. `glottal` covers glottal ornaments, for example the Mongolian *nugula* (诺古拉). |
| `melisma_group` | The same ID for all notes sung on one syllable (拖腔), for example `m3`. |
| `syllable` | The sung syllable, if audible. It is **required** for vocables (衬词: 呀, 哎, 嗬, 啰, 哟 …). |
| `voice` | `lead`, `second` or `chorus`. Notate the lead voice; mark other voices only where they replace the lead. |
| `doubled` | 1 where an instrument doubles the voice and you cannot separate them. |
| `conf_exists`, `conf_pitch`, `conf_onset` | Your confidence in each, from 1 (unsure) to 3 (sure). |

Rules:
- A grace note ends where the main note begins; the two never overlap.
- A note can carry several attributes, for example a scoop, vibrato and a thrown ending. Do not split it to show them.
- **Free rhythm:** add a row of type `free_rhythm_start` or `free_rhythm_end` with its time. Use `free_cadence` for a metred phrase that ends with a free fermata.
- If less than 10 s of the excerpt is sung, **tell the contact before you start**. Do not skip it on your own.

## Step 3: notes (`E##_<id>_notes.txt`)

The file has four required headings:
1. **Hesitations:** where you were unsure, and why.
2. **What neither layer can show.**
3. **Guess:** region and genre, each with a confidence from 1 to 3.
4. **Time and audio:** time spent, and whether you used the mix, the voice file, or both, per passage.

## After all excerpts: debrief (about 1 hour)

We show you the places where your notation differs from the others, without saying who wrote the others. For each difference, choose one reason:
- **P:** I heard it differently.
- **C:** convention or notational choice.
- **G:** the guideline was unclear.
- **S:** a slip or an error.

## Background form (once)

- training: institution, and major (composition, 民族音乐理论, ethnomusicology, performance);
- years of transcription experience, and the regions of any fieldwork;
- native language and dialect;
- absolute pitch (yes/no);
- main instrument, and experience with the tools;
- familiarity with each of the 15 regions, from 1 to 5.

## Time, pay and consent

- **Time:** expect **60–120 minutes per excerpt** for the performance layer, plus 15–20 minutes for the skeleton. The pilot will refine this estimate.
- **Pay:** [to be stated].
- **Consent:**
  - Your notations and your anonymised background answers will be analysed and **released as open data** (proposed licence CC BY 4.0).
  - You will be acknowledged by name, if you agree.
  - You may withdraw before the release.

## Questions

Ask the project contact only. We answer everyone in the same way.
