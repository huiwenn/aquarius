# Researching a song: composer, period, class, genre

The full protocol is `docs/song_labelling_protocol.md`; this is the working guide. One label row per song (`song_id`). Fill every protocol column.

## Order of work

1. **Read the row's evidence** in `input_<Region>.csv`:
   - the example video titles (they often say 原生态, 改编, 作曲, or name the singer);
   - the curator genre and `curator_dating_flag`;
   - `rhymoi_composer` (a composer line printed by the Musical Map of China);
   - `anthology_matches`;
   - `prior_*` (an earlier dating, with URLs).
2. **Decide whether a search can change the label.** Anonymous genre songs (山歌, 号子 …, especially generic titles) rarely need one. Search when the song:
   - may be composed or adapted (curator flag `check`/`composed`, a composer line, a modern-sounding title, a famous title);
   - has a documented collection history.
3. **Search in Chinese first:** `"<歌名>" 民歌 作曲`, `"<歌名>" 由来`, `"<歌名>" 创作 年`, `"<歌名>" 收集 整理`. Then English.
4. **Read the page you cite.** A search-result snippet alone gives at most `medium`.
5. **Write the row.** Fill `evidence` (one or two sentences on what the sources say), `sources` (URLs separated by `|`) and `confidence`.

## Sources, best first

1. Publications from 《中国民间歌曲集成》 (the Anthology): a same-province title match in `anthology_overlap.csv` with verdict `match`.
2. ihchina.cn (national heritage project pages), provincial culture or government sites, county gazetteers.
3. Academic articles, and newspapers with named authors (人民日报, 新华, provincial dailies).
4. zh.wikipedia.org (fetch `https://zh.wikipedia.org/wiki/<title>`).
5. Record-label and streaming credits (weak: they often credit the arranger or singer as "composer").

Notes:
- **Baidu Baike** blocks automated fetches (403). A Baike claim you saw only in a snippet stays `medium` at most.
- **Uploader descriptions** on Bilibili are secondary sources and are often copied from Baike.
- **No logins or cookies** for research, and no paywalled databases (CNKI).

## Decision rules

- **Folk songs have no composer.** A traditional song collected by someone keeps `composer` empty. The collector goes in `evidence`, and the collection year goes in `year_best` with `year_kind = collection`.
- **整理 / 改编 by a named person → `folk_adapted`.** The person goes in `arranger`, or in `lyricist` if only the words are new. Red-era new words on an old tune are `folk_adapted`, `year_kind = adaptation`.
- **A new song in a folk idiom with a named author → `folk_style_composed`** (浏阳河, 十送红军). It leaves the core subset automatically.
- **A collection or recording year does not set the period of a traditional song.** Use `traditional_undated` (or `ming` / `qing` when a source dates the origin). An adapted song with no date has period `unknown`.
- **Theatre excerpts are `opera`.** A song composed *for* an opera keeps its song class (洪湖水浪打浪 is `folk_style_composed`).
- **Two songs, one title, is common** (绣荷包, 五更调, 月光光). Make sure the source is about *this* song: compare the place, the lyrics and the example titles.
- **Region check:** use `disagree:<region>` only with a source. Region assignments that look odd but follow the project's region rules (southern Anhui → Jiangsu–Zhejiang Plain; Chaoshan → Min–Tai; Mongol/Daur songs → Northern Steppe wherever the singer lives; Hehuang hua'er → Northwest Plateau) are `agree`.
- **Never invent a name or a year.** If unsure, leave it empty and set `low`.

## Period from year

| Year | Period |
|---|---|
| 1368–1643 | `ming` |
| 1644–1911 | `qing` |
| 1912–1948 | `republic` |
| 1949–1965 | `prc_1949_1965` |
| 1966–1976 | `prc_1966_1976` |
| 1977–1999 | `prc_1977_1999` |
| 2000– | `after_2000` |

## Working at scale with Claude

Give each research agent 3–4 regions, `docs/song_labelling_protocol.md`, a search budget (about 40–60 searches), and the instruction to write rows every ~20 songs. A session has a limited web-search quota (it ran out at about 200 searches in one session), so plan the budget across agents. Afterwards:
- run `song_labels_check.py`;
- have a **separate** agent verify a sample (it writes `verification.csv`; it never edits labels);
- apply accepted corrections through `adjudication.csv`.
