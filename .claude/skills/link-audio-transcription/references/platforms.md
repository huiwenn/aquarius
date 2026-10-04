# Platforms: what worked, with evidence

## Contents
1. YouTube
2. Bilibili
3. Archives (Europeana / CREM and similar)
4. One process, several platforms
5. Manifest fields

---

## 1. YouTube

- **Bot wall:** "Sign in to confirm you're not a bot".
  - It started after ~150 fast downloads with 6 workers, and after ~85 with 1 worker at 4–12 s pauses.
  - Once active, it blocked every player client and also requests without cookies, so it is IP-level and timed.
  - PO-token providers and a JS runtime did not lift an active wall.
- **What worked:**
  - 1 worker, 45–90 s random pauses, a 1 h cooldown and retry of the same item when the wall appears;
  - Firefox cookies (Chrome on macOS stalls on a keychain prompt);
  - `yt-dlp[default]` plus a working Node for the JS challenges (the system Node was broken, so Node lives in its own conda env).
  - This gave ~45 downloads per hour with no further walls. A later run that interleaved YouTube with Bilibili hit no wall in ~100 YouTube downloads.
- **Retries:** transient 403s (~5%). A retry with the default client recovered them; `mweb` and `web_embedded` each rescued one more in an earlier run. Never use `tv`.
- **Search** (`ytsearchN:` with flat extraction) still works during a wall.
- **Link check:** the oEmbed endpoint `https://www.youtube.com/oembed?format=json&url=<url>` returns 200 for live public videos and 400/401/404 otherwise. It is cheap and does not touch the download path.

## 2. Bilibili

- **Search:** use the web API `https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=...`.
  - Use an opener that first loads `https://www.bilibili.com/` to set `buvid3` cookies, with a browser User-Agent and Referer `https://search.bilibili.com/`. It works without login.
  - yt-dlp's `bilisearch` returns HTTP 412.
- **Download:** yt-dlp with Firefox cookies, `bestaudio/best` (m4a), 8–20 s pauses. There were no bans in ~570 downloads.
- **Link check:**
  - `/x/web-interface/view?bvid=` returns 412 without signed requests, and video pages return anti-bot shells with no `<title>`.
  - What worked: `yt_dlp.YoutubeDL({"skip_download": True, "cookiesfrombrowser": ("firefox",)}).extract_info(url, download=False, process=False)`.
- **Undecodable m4a:** some files fail in libsndfile and macOS Core Audio (`Format not recognised`; audioread `MacError 1650549857`; ffmpeg warns "Number of bands (12) exceeds limit (8)" but decodes them). Decode with ffmpeg.
- **Deleted accounts** all show the same display name. Key channels by platform channel ID (`bilibili:<mid>`).
- **Re-uploads:** large commercial series are re-uploaded by many accounts. Treat known re-upload channels as the original channel when you enforce channel caps or keep collection rounds apart.

## 3. Archives

- **Europeana API** (`wskey=api2demo` for testing) finds field recordings, for example CREM ethnomusicology items. Direct MP3 URLs can be fetched with urllib.
- **Rights:** they are often "In Copyright, research use only". Release links and metadata only, until the archive permits derived data.
- **Duration:** archive items may lack a duration in their metadata. Fill it with `ffprobe` after download.

## 4. One process, several platforms

- Keep a per-platform `next_ok` time.
- Each loop, pick the next queued item whose platform is ready; otherwise sleep until the earliest `next_ok`.
- Visit groups (regions, genres) round-robin by rank, so an interruption leaves every group partly filled.

## 5. Manifest fields

`group, rank, platform, id, url, title, channel, channel_id, duration_s, ..., audio_path, status, error, uploader, uploader_id, upload_date, duration_s_actual, license`

Rebuild the manifest from disk (audio file present → `ok`) after each run.
