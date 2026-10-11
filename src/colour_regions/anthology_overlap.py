"""
Overlap between the Colour Regions recording corpus and the Anthology of Chinese Folk Songs
(《中国民间歌曲集成》, OMR edition, 11 volumes).

Pipeline (one run, deterministic):
  1. Candidate generation. Every non-generic song (song_key without '#') is compared by its song_name, song_key and
     alt_names with every Anthology title:
       exact      equal after norm_title (regionclf.corpus) + traditional→simplified
       variant    equal after variant rules: drop parentheticals / numbering, split on '·', strip a place prefix
                  (provinces, our recording places, Anthology-volume places), strip suffixes 调/歌/曲/儿/子/小调/民歌
       fuzzy      rapidfuzz ratio ≥ 80 on the normalised titles, both ≥ 3 characters
       contained  the shorter normalised title (≥ 3 chars) is contained in the longer one, length ratio ≥ 0.5
  2. Province evidence: any of the song's recording provinces (recordings.csv) or curated provinces (input_all.csv)
     equals the volume's province ('yes'); 东北 for Jilin and 重庆 for Sichuan (Chongqing was part of Sichuan when the
     Anthology was compiled) count as 'yes'; else 'no'. same_region = our colour region == the volume's region.
  3. Melodic evidence. Query = Anthology melody (MIDI, monophonised, repeated pitches merged, first 60 notes).
     Target = each of our primary transcriptions of the song (monophonised, repeats merged, first 800 notes).
     Score = Smith-Waterman local alignment on pitch classes, maximised over the 12 transpositions
     (key- and octave-invariant), divided by the query length; a song's score = max over its recordings.
     Calibration: (a) a per-pair null — the same recordings against 200 random Anthology scores with a different
     title core → melodic_percentile; (b) a pooled same-region baseline of random non-matching pairs.
  4. Verdicts (judge()). HOMONYM_CORES = theme/genre titles shared by unrelated songs (对花, 绣荷包, 五更, 采茶 …).
       title exact/variant + same province            → match (homonym-prone title with melodic pct < 50 → uncertain)
       title exact/variant + other province:
           melodic pct ≥ corrected threshold          → match; threshold = max(99, 100·(1 − 0.05/k)), k = the song's
                                                        cross-province comparisons; homonym-prone titles need ≥ 99.75
           pct ≥ 99, or ≥ 95 for a non-homonym title  → uncertain
           distinctive title (≥ 4 chars, not homonym-prone) and pct ≥ 50 or no transcription → uncertain
           otherwise                                  → rejected (possible homonym)
       fuzzy/contained title: same province and (pct ≥ 95 or fuzzy) → uncertain; other province and pct ≥ threshold
       and not homonym-prone → uncertain; otherwise rejected.
     Manual verdicts in data/colour_regions/anthology_overlap_manual.csv (song_id, anthology_item_id, verdict,
     reason) override the rule (genre labels such as 木鱼 / 情歌对唱, chance melodic hits, title-variant upgrades).
     `--verdicts-only` re-judges the saved candidates without recomputing melodic scores.

Outputs: data/colour_regions/anthology_overlap.csv (match|uncertain), anthology_overlap_rejected.csv,
         anthology_overlap_candidates.csv (all candidates with scores, before verdicts),
         anthology_overlap_baseline.csv (pooled same-region baseline scores).

Run (py312): python src/colour_regions/anthology_overlap.py
"""

import re
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from rapidfuzz import fuzz
from zhconv import convert

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from regionclf.corpus import midi_notes, norm_title  # noqa: E402

D = ROOT / "data" / "colour_regions"
ANTH = ROOT / "data" / "raw" / "anthology_chinese_folk_songs"
SEED = 20261010
N_QUERY, N_TARGET, N_NULL, N_BASE = 60, 800, 200, 3000
MEL_PCT = 95.0  # weak melodic support (percentile of the per-pair null) → at most 'uncertain'
MEL_STRONG = 99.0  # strong melodic support, raised per song for multiple comparisons (mel_threshold)

VOL_PROV = {"hebei1": "河北", "hebei2": "河北", "tianjin": "天津", "jilin": "吉林", "jiangsu1": "江苏",
            "jiangsu2": "江苏", "shanghai": "上海", "guangdong": "广东", "hainan": "海南", "henan": "河南",
            "sichuan1": "四川"}
PROV_ALIASES = {"吉林": {"吉林", "东北"}, "四川": {"四川", "重庆", "重庆/四川"}}
PROVINCES = ["北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江", "上海", "江苏", "浙江", "安徽", "福建",
             "江西", "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州", "云南", "西藏",
             "陕西", "甘肃", "青海", "宁夏", "新疆", "台湾", "香港", "澳门", "东北", "陕北", "江南", "苏北", "苏南",
             "皖南", "皖北", "赣南", "闽南", "粤北", "川江", "川北", "川西", "川东", "冀东", "豫南", "豫西", "豫东", "鲁西",
             "胶东", "客家", "潮州", "潮汕", "扬州", "兴国", "苏州", "无锡", "南京", "南通", "海门", "如东", "盐城",
             "宝应", "高邮", "六合", "徐州", "淮安", "常州", "镇江", "昌黎", "沧州", "延边", "信阳", "南阳", "商城", "固始",
             "光山", "梅州", "梅县", "兴宁", "五华", "广州", "儋州", "崖州", "临高", "琼", "巴山", "巫山", "宜宾", "达县",
             "凤阳", "五河", "巢湖", "大别山", "沂蒙", "绥德", "府谷", "河曲", "左权", "茂名", "雷州", "湛江", "中山",
             "汕尾", "惠阳", "惠东", "龙川", "河源", "韶关", "台山", "顺德", "东莞", "南海", "番禺", "西北", "西南"]
SUFFIXES = ["小调", "民歌", "调", "歌", "曲", "儿", "子"]
GENERIC_CORES = {"山歌", "号子", "小调", "民歌", "情歌", "酒歌", "号", "小曲", "对歌", "盘歌", "田歌", "秧歌", "花灯",
                 "茶歌", "采茶", "渔歌", "船歌", "牧歌", "儿歌", "摇篮曲", "哭嫁歌", "哭嫁", "劳动号子", "打夯", "夯号",
                 "五更", "十二月", "四季", "叫卖", "放牛", "放羊", "唱", "歌", "调"}
# titles shared by many unrelated songs (theme/genre titles): cross-province pairs need strong melodic support
HOMONYM_CORES = GENERIC_CORES | {
    "对花", "绣荷包", "哭五更", "闹五更", "叫五更", "小五更", "五更鼓", "采茶", "倒采茶", "十二月采茶", "送郎", "望郎",
    "送情郎", "探妹", "十探妹", "四季探妹", "探情郎", "瞧情郎", "十二月花名", "四季花", "四季春", "采花", "放风筝", "绣花",
    "撑船", "迎客", "打夯", "打硪", "薅秧", "赶牛", "思乡", "割草", "担水", "离别", "拦路", "约定", "燕子", "想妈妈",
    "春之歌", "情歌对唱", "木鱼", "渔民号子", "长工", "十二条手巾", "绣花鞋", "红绣鞋", "打猎", "梳头", "花灯", "花鼓",
    "哭嫁", "嫁女", "盘歌", "月光光", "回娘家", "小女婿", "赶集", "相思病", "割韭菜", "四季棉花", "划龙船", "螃蟹",
    "扁担", "行船", "渔家乐", "数麻雀", "猜调", "十杯酒", "大实话", "打秋千", "捡棉花", "小拜年", "放羊", "牡丹",
    "映山红", "抓壮丁", "卖货郎", "九连环", "打鞋底"}


# ───────────────────────── titles ─────────────────────────
def zh(t: str) -> str:
    return re.sub(r"^[a-z]_", "", convert(str(t), "zh-cn"))  # 'a_' = alternative OMR rendering of the same score


def exact_key(t: str) -> str:
    return norm_title(zh(t))


def place_set() -> list[str]:
    r = pd.read_csv(D / "recordings.csv", usecols=["geo_name", "county_or_area"])
    i = pd.read_csv(D / "song_labels" / "input_all.csv", usecols=["places"])
    ps = set(PROVINCES)
    for v in pd.concat([r.geo_name, r.county_or_area, i.places.str.split(r"[;；/、 ]")
                        .explode()]).dropna().astype(str):
        v = re.sub(r"[?？（）()]", "", zh(v)).strip()
        v2 = re.sub(r"(特别行政区|自治州|自治县|自治旗|地区|省|市|县|区|盟|旗|州|镇|乡|村)$", "", v)
        for x in (v, v2):
            if 2 <= len(x) <= 4:
                ps.add(x)
    return sorted(ps, key=len, reverse=True)


def variant_keys(t: str, places: list[str]) -> set[str]:
    """Variant cores of a title (each ≥ 2 characters)."""
    raw = zh(t)
    raw = re.sub(r"^\d+[_\-\s.]*", "", raw)
    base = re.sub(r"[（(\[【].*?[)）\]】]", "", raw)
    parts = [base] + [p for p in re.split(r"[·・、/／]", base) if len(norm_title(p)) >= 3]
    out = set()
    for p in parts:
        k = norm_title(p)
        stack = [k]
        seen = set()
        while stack:
            x = stack.pop()
            if x in seen or len(x) < 2:
                continue
            seen.add(x)
            for pl in places:  # place prefix
                if x.startswith(pl) and len(x) - len(pl) >= 2:
                    stack.append(x[len(pl):])
                    break
            for sfx in SUFFIXES:
                if x.endswith(sfx) and len(x) - len(sfx) >= 2:
                    stack.append(x[: -len(sfx)])
        out |= seen
    return out


def core(t: str, places: list[str]) -> str:
    v = variant_keys(t, places)
    return min(v, key=len) if v else exact_key(t)


# ───────────────────────── melody ─────────────────────────
def merge_repeats(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, np.int64)
    return p[np.r_[True, np.diff(p) != 0]] if len(p) else p


@njit(cache=True)
def sw_pc(q, x):
    """Smith-Waterman on pitch classes (match +2, mismatch -1, gap -1), maximised over the 12 transpositions.
    Returns best[i] = best local-alignment score using only the first i+1 query notes (so any query prefix
    length can be scored from one pass)."""
    n, m = len(q), len(x)
    best = np.zeros(n)
    for t in range(12):
        prev = np.zeros(m + 1)
        run = 0.0
        for i in range(1, n + 1):
            cur = np.zeros(m + 1)
            qi = (q[i - 1] + t) % 12
            for j in range(1, m + 1):
                s = 2.0 if qi == x[j - 1] % 12 else -1.0
                v = prev[j - 1] + s
                if prev[j] - 1.0 > v:
                    v = prev[j] - 1.0
                if cur[j - 1] - 1.0 > v:
                    v = cur[j - 1] - 1.0
                if v < 0.0:
                    v = 0.0
                cur[j] = v
                if v > run:
                    run = v
            if run > best[i - 1]:
                best[i - 1] = run
            prev = cur
    return best


def mel_profile(q: np.ndarray, targets: list) -> np.ndarray:
    """Prefix-score profile of query q against the best of several targets (max over targets)."""
    return np.max([sw_pc(q, t) for t in targets], axis=0)


def mel_score(q: np.ndarray, x: np.ndarray) -> float:
    if len(q) < 8 or len(x) < 8:
        return np.nan
    return sw_pc(q, x)[-1] / (2.0 * len(q))


_ANTH_CACHE: dict[str, np.ndarray] = {}


def anth_seq(item_id: str) -> np.ndarray:
    if item_id not in _ANTH_CACHE:
        vol, stem = item_id.split(":", 1)[1].split("/", 1)
        hits = list(ANTH.glob(f"*/{vol}/{stem}.mid"))
        seq = np.zeros(0, np.int64)
        if hits:
            try:
                seq = merge_repeats(midi_notes(hits[0], beats=True)[:, 2])[:N_QUERY]
            except Exception:
                pass
        _ANTH_CACHE[item_id] = seq
    return _ANTH_CACHE[item_id]


def recording_midis() -> dict[str, Path]:
    r = pd.read_csv(D / "recordings.csv", usecols=["item_id", "region", "transcription_model"])
    t = pd.read_csv(D / "transcription_index.csv", usecols=["video_id", "midi_path"])
    out = {v: ROOT / p for v, p in zip(t.video_id, t.midi_path) if isinstance(p, str) and (ROOT / p).exists()}
    for _, x in r[r.transcription_model.notna() & ~r.item_id.isin(out)].iterrows():
        hits = list((ROOT / "data" / "regions_transcription" / "midi" / x.transcription_model).glob(f"*/{x.item_id}.mid"))
        if hits:
            out[x.item_id] = hits[0]
    return out


_REC_CACHE: dict[str, np.ndarray] = {}


def rec_seq(item_id: str, midis: dict) -> np.ndarray:
    if item_id not in _REC_CACHE:
        seq = np.zeros(0, np.int64)
        if item_id in midis:
            try:
                seq = merge_repeats(midi_notes(midis[item_id], beats=False)[:, 2])[:N_TARGET]
            except Exception:
                pass
        _REC_CACHE[item_id] = seq
    return _REC_CACHE[item_id]


# ───────────────────────── main ─────────────────────────
def main():
    rng = np.random.default_rng(SEED)
    places = place_set()
    sl = pd.read_csv(D / "song_labels.csv")
    ia = pd.read_csv(D / "song_labels" / "input_all.csv", usecols=["song_id", "alt_names", "provinces", "places"])
    songs = sl.merge(ia, on="song_id", how="left")
    songs = songs[~songs.song_key.str.contains("#")].copy()
    rec = pd.read_csv(D / "recordings.csv", usecols=["item_id", "province", "county_or_area", "region", "song_name"])
    # province of a recording; when missing, a macro-area such as 东北 given as county_or_area
    rprov = dict(zip(rec.item_id, rec.province.fillna(rec.county_or_area.where(rec.county_or_area.isin(["东北"])))))

    sec = pd.read_csv(D / "anthology_sections.csv")
    a = pd.read_csv(D / "scores.csv")
    a = a[a.source == "anthology"].merge(sec[["item_id", "section"]], on="item_id", how="left")
    a["vol_prov"] = a.volume.map(VOL_PROV)
    a["ex"] = a.title.map(exact_key)
    a["var"] = a.title.map(lambda t: variant_keys(t, places))
    a["core"] = a.title.map(lambda t: core(t, places))
    var_index: dict[str, set[int]] = {}
    for i, vs in zip(a.index, a["var"]):
        for v in vs:
            var_index.setdefault(v, set()).add(i)
    a_ex = a.ex.tolist()

    rows = []
    for _, s in songs.iterrows():
        names = {str(s.song_name), str(s.song_key)}
        if isinstance(s.alt_names, str):
            names |= {n.strip() for n in s.alt_names.split(";") if n.strip()}
        items = [x.strip() for x in str(s.item_ids).split(";") if x.strip()]
        provs = {rprov.get(x) for x in items if isinstance(rprov.get(x), str)}
        if isinstance(s.provinces, str):
            provs |= {p.strip() for p in s.provinces.split(";")}
        provs = {q for p in provs for q in re.split(r"[/、]", re.sub(r"[（(].*?[)）]", "", p))} | provs
        found: dict[int, tuple[int, str, str]] = {}  # anthology index → (rank, type, our name)
        for nm in names:
            ek = exact_key(nm)
            vk = variant_keys(nm, places)
            for i in a.index[a.ex == ek] if ek else []:
                found[i] = min(found.get(i, (9, "", "")), (0, "exact", nm))
            for v in vk:
                for i in var_index.get(v, ()):
                    found[i] = min(found.get(i, (9, "", "")), (1, "variant", nm))
            if len(ek) >= 3:
                for i, ak in enumerate(a_ex):
                    if len(ak) < 3:
                        continue
                    idx = a.index[i]
                    if fuzz.ratio(ek, ak) >= 80:
                        found[idx] = min(found.get(idx, (9, "", "")), (2, "fuzzy", nm))
                    else:
                        sh, lo = (ek, ak) if len(ek) <= len(ak) else (ak, ek)
                        if sh in lo and len(sh) / len(lo) >= 0.5:
                            found[idx] = min(found.get(idx, (9, "", "")), (3, "contained", nm))
        for i, (_, mt, nm) in found.items():
            x = a.loc[i]
            vp = x.vol_prov
            same_p = "yes" if (provs & PROV_ALIASES.get(vp, {vp})) else "no"
            rows.append(dict(song_id=s.song_id, song_name=s.song_name, song_key=s.song_key, region=s.region,
                             song_class=s.song_class, genre=s.genre, our_provinces="; ".join(sorted(provs)),
                             places=s.places, item_ids="; ".join(items), n_recordings=len(items),
                             matched_name=nm, anthology_item_id=x.item_id, anthology_volume=x.volume,
                             anthology_title=x.title, anthology_section=x.section, match_type=mt,
                             title_core=core(nm, places), anthology_core=x.core,
                             same_province=same_p, same_region=bool(s.region == x.region)))
    c = pd.DataFrame(rows)
    print(len(c), "candidate pairs;", c.song_id.nunique(), "songs;", c.match_type.value_counts().to_dict())
    if "--titles-only" in sys.argv:
        c.to_csv(D / "anthology_overlap_candidates.csv", index=False)
        return

    # ── melodic similarity ──
    midis = recording_midis()
    a_items = a.item_id.to_numpy()
    a_core = dict(zip(a.item_id, a.core))
    mel, pct, nrec = [], [], []
    null_cache: dict[str, list] = {}
    for _, p in c.iterrows():
        tg = [rec_seq(x, midis) for x in p.item_ids.split("; ")]
        tg = [t for t in tg if len(t) >= 8]
        q = anth_seq(p.anthology_item_id)
        nrec.append(len(tg))
        if not tg or len(q) < 8:
            mel.append(np.nan)
            pct.append(np.nan)
            continue
        L = len(q)
        sc = mel_profile(q, tg)[-1] / (2.0 * L)
        # per-pair null: the same recordings vs random Anthology scores with a different title core, each null
        # query truncated to the candidate's query length L (score per query note is length-dependent)
        cores = {p.title_core, p.anthology_core}
        if p.song_id not in null_cache:
            prng = np.random.default_rng(zlib.crc32(f"{p.song_id}|{SEED}".encode()))
            lst = []
            for j in prng.permutation(len(a_items)):
                if len(lst) >= N_NULL + 60:
                    break
                qq = anth_seq(a_items[j])
                if len(qq) >= 8:
                    lst.append((a_core[a_items[j]], mel_profile(qq, tg)))
            null_cache[p.song_id] = lst
        null = [pr[L - 1] / (2.0 * L) for k, pr in null_cache[p.song_id] if k not in cores and len(pr) >= L][:N_NULL]
        mel.append(sc)
        pct.append(100.0 * np.mean(np.array(null) < sc))
    c["n_transcribed"] = nrec
    c["melodic_similarity"] = np.round(mel, 4)
    c["melodic_percentile"] = np.round(pct, 1)

    # ── pooled same-region baseline (random non-matching pairs) ──
    recs = rec[rec.item_id.isin(midis)]
    rec_core = {i: core(n, places) for i, n in zip(recs.item_id, recs.song_name.fillna(""))}
    base = []
    reg_vols = a.groupby("region").item_id.apply(list).to_dict()
    rec_by_reg = recs.groupby("region").item_id.apply(list).to_dict()
    regs = [r for r in reg_vols if r in rec_by_reg]
    while len(base) < N_BASE:
        rg = regs[rng.integers(len(regs))]
        ri = rec_by_reg[rg][rng.integers(len(rec_by_reg[rg]))]
        ai = reg_vols[rg][rng.integers(len(reg_vols[rg]))]
        t, q = rec_seq(ri, midis), anth_seq(ai)
        if len(t) < 8 or len(q) < 8:
            continue
        if ((c.anthology_item_id == ai) & c.item_ids.str.contains(re.escape(ri))).any() \
                or a_core[ai] == rec_core.get(ri):
            continue
        base.append(dict(region=rg, item_id=ri, anthology_item_id=ai, melodic_similarity=round(mel_score(q, t), 4)))
    base = pd.DataFrame(base)
    base.to_csv(D / "anthology_overlap_baseline.csv", index=False)
    c.to_csv(D / "anthology_overlap_candidates.csv", index=False)

    print("baseline quantiles:", base.melodic_similarity.quantile([.5, .9, .95, .99]).round(3).to_dict())
    judge(c)


def mel_threshold(c: pd.DataFrame) -> pd.Series:
    """Multiple-testing-aware melodic threshold per song: a song compared with k cross-province scores needs
    percentile ≥ max(MEL_STRONG, 100·(1 − 0.05/k)) (≈ 5% family-wise false-match rate per song)."""
    k = c[(c.same_province == "no") & c.melodic_percentile.notna()].groupby("song_id").size()
    kk = c.song_id.map(k).fillna(1).clip(lower=1)
    return np.maximum(MEL_STRONG, 100 * (1 - 0.05 / kk))


def judge(c: pd.DataFrame) -> None:
    """Rule verdicts (see module docstring), then manual overrides; writes the two output tables."""
    c = c.copy()
    thr = mel_threshold(c)
    pct = c.melodic_percentile
    has_mel = pct.notna()
    homonym = c.title_core.isin(HOMONYM_CORES) | c.anthology_core.isin(HOMONYM_CORES)
    distinctive = (c.title_core.str.len() >= 4) & ~homonym
    title_ok = c.match_type.isin(["exact", "variant"])
    same = c.same_province == "yes"
    v, r = [], []
    for i in c.index:
        p, t = pct[i], thr[i]
        ps = "n/a" if np.isnan(p) else f"{p:.1f}"
        if title_ok[i] and same[i]:
            if homonym[i] and has_mel[i] and p < 50:
                v.append("uncertain"); r.append(f"homonym-prone title, same province, but melodic pct {ps} < 50 "
                                                "(may be a different song of the same title)")
            else:
                v.append("match"); r.append(f"title {c.match_type[i]} + same province (melodic pct {ps})")
        elif title_ok[i]:
            if homonym[i]:  # homonym-prone titles: must beat all 200 null scores (pct ≥ 99.75)
                t = max(t, 99.75)
            if has_mel[i] and p >= t:
                v.append("match"); r.append(f"title {c.match_type[i]}, other province; melodic pct {ps} ≥ corrected threshold {t:.1f}")
            elif has_mel[i] and (p >= MEL_STRONG or (p >= MEL_PCT and not homonym[i])):
                v.append("uncertain"); r.append(f"title {c.match_type[i]}, other province; melodic pct {ps} (≥95, below corrected {t:.1f})")
            elif distinctive[i] and (not has_mel[i] or p >= 50):
                v.append("uncertain"); r.append(f"distinctive title, other province; melodic pct {ps} neither supports nor contradicts")
            else:
                v.append("rejected"); r.append(("homonym-prone title" if homonym[i] else "title match") +
                                               f", other province, melodic pct {ps} below threshold (possible homonym)")
        else:
            if same[i] and has_mel[i] and p >= MEL_PCT:
                v.append("uncertain"); r.append(f"title {c.match_type[i]} only, same province; melodic pct {ps}")
            elif same[i] and c.match_type[i] == "fuzzy":
                v.append("uncertain"); r.append(f"near-identical title, same province; melodic pct {ps}")
            elif not same[i] and has_mel[i] and p >= t and not homonym[i]:
                v.append("uncertain"); r.append(f"title {c.match_type[i]} only, other province; melodic pct {ps}")
            else:
                v.append("rejected"); r.append(f"title {c.match_type[i]} only (different title); "
                                               f"{'same' if same[i] else 'other'} province; melodic pct {ps}")
    c["verdict"], c["reason"], c["melodic_threshold"] = v, r, thr.round(2)
    mp = D / "anthology_overlap_manual.csv"
    if mp.exists():
        m = pd.read_csv(mp)
        mm = {(a, b): (x, y) for a, b, x, y in zip(m.song_id, m.anthology_item_id, m.verdict, m.reason)}
        bad = set(mm) - set(zip(c.song_id, c.anthology_item_id))
        assert not bad, f"manual rows not among candidates: {bad}"
        for i in c.index:
            k = (c.song_id[i], c.anthology_item_id[i])
            if k in mm:
                c.loc[i, "verdict"], c.loc[i, "reason"] = mm[k][0], "manual: " + mm[k][1]
    cols = ["song_id", "song_name", "region", "our_provinces", "item_ids", "anthology_item_id", "anthology_volume",
            "anthology_title", "anthology_section", "match_type", "same_province", "same_region",
            "melodic_similarity", "melodic_percentile", "verdict", "reason"]
    keep = c[c.verdict.isin(["match", "uncertain"])].sort_values(["region", "song_id", "anthology_item_id"])
    keep[cols].to_csv(D / "anthology_overlap.csv", index=False)
    c[~c.verdict.isin(["match", "uncertain"])].sort_values(["region", "song_id", "anthology_item_id"])[cols].to_csv(
        D / "anthology_overlap_rejected.csv", index=False)
    print(keep.verdict.value_counts().to_dict(), "| songs with ≥1 match:", keep[keep.verdict == "match"].song_id.nunique())


if __name__ == "__main__":
    if "--verdicts-only" in sys.argv:  # re-judge the saved candidates (e.g. after editing the manual CSV)
        judge(pd.read_csv(D / "anthology_overlap_candidates.csv"))
    else:
        main()
