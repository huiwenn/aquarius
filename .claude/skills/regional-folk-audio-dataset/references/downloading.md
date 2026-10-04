# Downloading (YouTube, rate-limit-safe)

## Contents
1. Output layout and provenance
2. The bot wall: what triggers it and what doesn't fix it
3. The downloader that worked (settings + why)
4. Retrying failures: the fallback cascade
5. Traps
6. Other sources

---

## 1. Output layout and provenance

- Audio: `data/regions_audio/<class>/<video_id>.<ext>`. Native best stream (opus/webm or m4a), **no transcoding**:
  keep the original; decoding happens downstream with ffmpeg.
- `<video_id>.info.json`: yt-dlp metadata (title, uploader, channel_id, upload_date, license, duration, acodec).
- `manifest.csv`: every curated candidate with curation fields, audio_path, status (ok/failed/pending), error,
  and download metadata. Always rebuild it from disk (`download_curated.py --manifest-only`). Never trust an
  in-memory status after an interruption.

## 2. The bot wall

Symptom: `ERROR: [youtube] <id>: Sign in to confirm you're not a bot.`

| Event | What happened |
|---|---|
| First pass: 6 parallel workers, no cookies | ~150 downloads, then 190 consecutive walls |
| After the wall | every player client failed (web, android_vr, tv, web_safari, mweb, ios); flat **search kept working** |
| Second run: Firefox cookies, 1 worker, 4–12 s sleeps | 85 downloads, then walled again |
| Adding a PO-token provider (bgutil) + JS runtime | did **not** lift an active wall |
| Without cookies at that point | also walled, so the limit is IP-level and timed |
| Two 40-min cooldowns | not enough; the wall cleared after ~1–2 h |
| Restart at **45–90 s** sleeps, 1 h cooldowns | ~400 downloads with **zero** further walls |

Budget ~45 downloads/hour. For 600 items that's ~13–14 h wall-clock. Plan to transcribe in parallel
(see scaling.md).

## 3. The downloader that worked: `src/secaiqu/download_curated.py`

- **Cookies:** `cookiesfrombrowser=("firefox",)`. Chrome on macOS stalled forever on a keychain prompt. Firefox
  cookies are read without one. Ask the user before using their browser session, and suggest a throwaway
  Google account.
- **Pacing:** 1 worker; `--min-sleep 45 --max-sleep 90` (uniform random).
- **Order:** round-robin across classes by rank. An interruption then leaves every class partially filled rather
  than some full and some empty, and early ranks (best candidates) come first everywhere.
- **Bot wall handling:** detect "not a bot"/"Sign in" and sleep `--cooldown 3600`, then retry the *same* item, up
  to `--max-cooldowns`.
- **JS runtime:** yt-dlp needs one for YouTube's JS challenges. Without it, `[jsc]` providers are unavailable and it
  falls back to degraded clients. Install `yt-dlp[default]` (brings yt-dlp-ejs) and point at Node:
  `js_runtimes={"node": {"path": ...}}`. In the worked example the system Node 15 was broken (missing ICU dylib),
  so Node 26 was installed in its own arm64 conda env `node`.
- **PO tokens (optional):** bgutil-ytdlp-pot-provider (`third_party/bgutil-ytdlp-pot-provider`, `node build/main.js`
  serves on :4416; `pip install bgutil-ytdlp-pot-provider`). It didn't lift an active wall. It may reduce wall
  frequency, but that wasn't measured separately.
- `noplaylist=True`, `writeinfojson=True`, `retries=3`.

## 4. Retrying failures: `src/secaiqu/download_fallbacks.py`

After the full pass, 27/600 had failed, nearly all with `HTTP Error 403: Forbidden` (~5%, sporadic).
- A retry with `--player-client tv,web_safari` recovered 2. Every other video now failed with
  **"The page needs to be reloaded", which the `tv` client causes**. Don't use it for retries.
- The cascade script tries, per video, stopping at the first success:
  1. yt-dlp + cookies with player clients `default, mweb, ios, web_embedded, android_vr, tv_simply`
  2. yt-dlp without cookies
  3. Invidious API proxies (`/api/v1/videos/<id>`, stream via `latest_version?...&local=true`)
  4. Piped API (`/streams/<id>`)
  5. with `--allow-replacement`: search for another upload of the same song and append it to the curated list
     with `replaces: <id>` and a "needs listening check" note
- Result: **25/25 recovered.** 23 with the *default* client on a plain retry (the 403s were transient), 1 with
  `mweb`, 1 with `web_embedded`. Stages 2–5 were never needed.
- Every attempt is logged to `data/regions_audio/fallback_log.csv`: which method worked is a finding worth keeping.

## 5. Traps

- **Playlist/channel URLs.** `noplaylist` only affects `watch?v=…&list=` URLs. A `/playlist?list=` or `/@channel`
  URL downloads everything. Filter candidates to `watch?v=` / `youtu.be/` before downloading.
- **Leading-dash IDs** (e.g. `-iokiXPhoIM`). Pass directories rather than filenames to CLIs, or use `--`.
- **`.part` files** from killed runs. Delete them before restarting; manifest code should only count real audio
  extensions.
- **Downloads racing a transcription pass.** Stage audio via symlinks and tolerate `FileExistsError`. Two processes
  staging at once crashed one of them in the worked example.
- **Harness/tool outages.** Run long jobs with `nohup` from scripts, not inside a chat tool call, so they survive
  the orchestrator being blocked.

## 6. Other sources

- **Bilibili:** has a lot of Chinese folk material, but `bilisearch` returned `HTTP 412 Precondition Failed`, even
  with Firefox cookies (WBI signing). Direct video downloads may work; search needs extra work.
- **Archives and field-recording libraries** (national archives, ethnomusicology collections, CHIME, Smithsonian
  Folkways, Zenodo datasets) have better provenance and licensing. Prefer them when the dataset will be
  redistributed.
- Whatever the source, keep the same structure: search-only candidate IDs, a manifest, a per-item metadata sidecar,
  idempotent retries.
