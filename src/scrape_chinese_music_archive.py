#!/usr/bin/env python3
"""Exhaustive scraper for chinesemusics.com/en_us/ — Chinese Music Archive.

Scrapes: instruments, composers, conductors, performers, programme notes, history.
Saves text as JSON, downloads images/media to data/raw/chinese_music_archive/.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://chinesemusics.com/en_us/"
OUT_DIR = Path("data/raw/chinese_music_archive")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AcademicResearchBot/1.0",
    "Accept-Language": "en-US,en;q=0.9",
}
DELAY = 2.5

session = requests.Session()
session.headers.update(HEADERS)

# Profile URLs follow date-based pattern
PROFILE_URL_RE = re.compile(r'chinesemusics\.com/en_us/\d{4}/\d{2}/\d{2}/')

# Nav/structural links to exclude
NAV_KEYWORDS = {
    "info-db", "info-archive", "nav-archive", "ump-account", "ump-login",
    "ump-register", "about-us", "donation", "member-tos", "front-page",
    "samav-archive", "av-others", "col/", "ss-av",
}


def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            time.sleep(DELAY)
            return BeautifulSoup(resp.content, "html.parser")
        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                return None
            print(f"  [attempt {attempt+1}] Error fetching {url}: {e}", flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"  [attempt {attempt+1}] Error fetching {url}: {e}", flush=True)
            time.sleep(3)
    return None


def download_file(url: str, dest_dir: Path, prefix: str = "") -> str | None:
    try:
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))
        if prefix:
            filename = f"{prefix}_{filename}"
        filename = re.sub(r'[^\w\.\-]', '_', filename)
        if not filename or filename == '_':
            return None
        dest = dest_dir / filename
        if dest.exists():
            return filename
        resp = session.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        dest_dir.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        time.sleep(0.3)
        return filename
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return None


def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {path}", flush=True)


def get_content_div(soup: BeautifulSoup):
    return soup.find("div", class_="entry-content") or soup.find("article") or soup


def extract_body_text(soup: BeautifulSoup) -> str:
    """Extract main content text, stripping nav/header/footer noise."""
    content = get_content_div(soup)
    if content is None:
        return ""
    text = content.get_text(separator="\n", strip=True)
    lines = text.split("\n")
    clean = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line in ("Home", "Trial", "Info-Archive", "Login/Register",
                     "About Us", "Donate", "Enter", "Register"):
            continue
        if line.startswith("- ") and len(line) < 20:
            continue
        clean.append(line)
    return "\n".join(clean)


def extract_images(soup_or_el, base_url: str) -> list[str]:
    imgs = []
    for img in soup_or_el.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if src:
            full = urljoin(base_url, src)
            if "chinesemusics.com" in full and "Site-title" not in full:
                imgs.append(full)
    return list(dict.fromkeys(imgs))


def extract_media(soup: BeautifulSoup, base_url: str) -> dict:
    media = {"audio": [], "video": [], "iframes": []}
    for tag in soup.find_all("audio"):
        src = tag.get("src")
        if not src:
            source = tag.find("source")
            if source:
                src = source.get("src")
        if src:
            media["audio"].append(urljoin(base_url, src))
    for tag in soup.find_all("video"):
        src = tag.get("src")
        if not src:
            source = tag.find("source")
            if source:
                src = source.get("src")
        if src:
            media["video"].append(urljoin(base_url, src))
    for tag in soup.find_all("iframe"):
        src = tag.get("src")
        if src:
            media["iframes"].append(urljoin(base_url, src))
    return {k: v for k, v in media.items() if v}


def is_profile_url(url: str) -> bool:
    return bool(PROFILE_URL_RE.search(url))


def extract_profile_links(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Extract only profile links (date-based URLs) from a listing page.

    Searches entire page (Elementor post cards live outside entry-content).
    Filters to elementor-post__title links first, falls back to all date-based links.
    """
    entries = []
    seen = set()

    # Prefer Elementor post title links (most reliable)
    title_links = soup.select("h3.elementor-post__title a[href]")
    if not title_links:
        title_links = soup.select(".elementor-post__title a[href]")

    if title_links:
        for a in title_links:
            href = urljoin(page_url, a["href"])
            if href in seen:
                continue
            name = a.get_text(strip=True)
            if name:
                seen.add(href)
                entries.append({"name": name, "url": href})
        return entries

    # Fallback: search entire page for date-based profile URLs
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        if not is_profile_url(href):
            continue
        if href in seen:
            continue
        name = a.get_text(strip=True)
        if not name or name in ("Personal Profile »", "Personal  Profile »", "»", "Read More"):
            continue
        seen.add(href)
        entries.append({"name": name, "url": href})

    return entries


# ── INSTRUMENTS ──────────────────────────────────────────────────────────

INSTRUMENT_URLS = {
    "bow": "https://chinesemusics.com/en_us/info-db/instrument/%e6%a8%82%e5%99%a8%e6%8b%89/",
    "pluck": "https://chinesemusics.com/en_us/info-db/instrument/%e6%a8%82%e5%99%a8%e5%bd%88/",
    "wind": "https://chinesemusics.com/en_us/info-db/instrument/%e6%a8%82%e5%99%a8%e5%90%b9/",
    "percussion": "https://chinesemusics.com/en_us/info-db/instrument/%e6%a8%82%e5%99%a8%e6%89%93/",
}


def scrape_instrument_page(url: str, category: str) -> list[dict]:
    print(f"  Scraping instruments: {category}", flush=True)
    soup = fetch(url)
    if not soup:
        return []

    content = get_content_div(soup)
    instruments = []
    current = None

    for el in content.descendants:
        if not isinstance(el, Tag):
            continue
        if el.name in ("h2", "h3", "h4"):
            if current and (current["description"] or current["images"]):
                instruments.append(current)
            title = el.get_text(strip=True)
            anchor = el.get("id", "")
            current = {
                "name": title,
                "anchor": anchor,
                "category": category,
                "description": "",
                "images": [],
            }
        elif el.name == "img" and current is not None:
            src = el.get("src") or el.get("data-src") or el.get("data-lazy-src")
            if src:
                full = urljoin(url, src)
                if "chinesemusics.com" in full and full not in current["images"] and "Site-title" not in full:
                    current["images"].append(full)
        elif el.name == "p" and current is not None:
            txt = el.get_text(strip=True)
            if txt:
                current["description"] += txt + "\n"
    if current and (current["description"] or current["images"]):
        instruments.append(current)

    media = extract_media(soup, url)

    media_dir = OUT_DIR / "media" / "instruments"
    for inst in instruments:
        for img_url in inst["images"]:
            slug = re.sub(r'[^\w]', '_', inst["name"][:20])
            local = download_file(img_url, media_dir, prefix=slug)
            if local:
                inst.setdefault("local_images", []).append(str(media_dir / local))

    return instruments


def scrape_all_instruments():
    print("\n=== INSTRUMENTS ===", flush=True)
    all_instruments = {}
    for cat, url in INSTRUMENT_URLS.items():
        instruments = scrape_instrument_page(url, cat)
        all_instruments[cat] = instruments
        print(f"  {cat}: {len(instruments)} instruments", flush=True)

    save_json(all_instruments, OUT_DIR / "instruments" / "all_instruments.json")

    overview_url = "https://chinesemusics.com/en_us/info-db/instrument/"
    soup = fetch(overview_url)
    if soup:
        overview_text = extract_body_text(soup)
        overview_images = extract_images(soup, overview_url)
        save_json({
            "url": overview_url,
            "text": overview_text,
            "images": overview_images,
        }, OUT_DIR / "instruments" / "overview.json")

    total = sum(len(v) for v in all_instruments.values())
    print(f"  Total instruments: {total}", flush=True)
    return all_instruments


# ── PERSON PROFILES ──────────────────────────────────────────────────────

def scrape_person_profile(url: str) -> dict:
    soup = fetch(url)
    if not soup:
        return {"url": url, "error": "failed to fetch"}

    title_el = soup.find("h1", class_="entry-title") or soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else ""
    if not title:
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True).split("–")[0].strip()
    body_text = extract_body_text(soup)
    images = extract_images(soup, url)
    media = extract_media(soup, url)

    return {
        "url": url,
        "title": title,
        "full_text": body_text,
        "images": images,
        "media": media,
    }


def scrape_listing_with_profiles(url: str) -> list[dict]:
    """Get profile links from a listing page (composers, conductors)."""
    soup = fetch(url)
    if not soup:
        return []
    return extract_profile_links(soup, url)


def scrape_paginated_listing(base_url: str) -> list[dict]:
    """Get profile links from a paginated listing (performers)."""
    all_entries = []
    page = 1
    url = base_url

    while url:
        print(f"    Page {page}: {url}", flush=True)
        soup = fetch(url)
        if not soup:
            break

        entries = extract_profile_links(soup, url)
        all_entries.extend(entries)

        next_url = None
        # Look for Elementor pagination or page-numbers
        for pag in soup.find_all(class_=["elementor-pagination", "page-numbers", "wp-pagenavi"]):
            for a in pag.find_all("a", href=True):
                text = a.get_text(strip=True)
                if "Next" in text or "»" in text or text == str(page + 1):
                    next_url = urljoin(url, a["href"])
                    break
            if next_url:
                break

        if next_url and next_url != url:
            url = next_url
            page += 1
        else:
            url = None

    seen = set()
    unique = []
    for e in all_entries:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)
    return unique


def scrape_composers():
    print("\n=== COMPOSERS ===", flush=True)
    url = "https://chinesemusics.com/en_us/info-db/composer/"
    entries = scrape_listing_with_profiles(url)
    print(f"  Found {len(entries)} composer links", flush=True)

    composers = []
    media_dir = OUT_DIR / "media" / "composers"
    for i, entry in enumerate(entries):
        print(f"  [{i+1}/{len(entries)}] {entry['name']}", flush=True)
        profile = scrape_person_profile(entry["url"])
        profile["name_from_listing"] = entry["name"]

        for img_url in profile.get("images", []):
            slug = re.sub(r'[^\w]', '_', entry["name"][:20])
            local = download_file(img_url, media_dir, prefix=slug)
            if local:
                profile.setdefault("local_images", []).append(str(media_dir / local))

        composers.append(profile)

    save_json(composers, OUT_DIR / "composers" / "all_composers.json")
    print(f"  Total composers scraped: {len(composers)}", flush=True)
    return composers


def scrape_conductors():
    print("\n=== CONDUCTORS ===", flush=True)
    url = "https://chinesemusics.com/en_us/info-db/conductor/"
    entries = scrape_listing_with_profiles(url)
    print(f"  Found {len(entries)} conductor links", flush=True)

    conductors = []
    media_dir = OUT_DIR / "media" / "conductors"
    for i, entry in enumerate(entries):
        print(f"  [{i+1}/{len(entries)}] {entry['name']}", flush=True)
        profile = scrape_person_profile(entry["url"])
        profile["name_from_listing"] = entry["name"]

        for img_url in profile.get("images", []):
            slug = re.sub(r'[^\w]', '_', entry["name"][:20])
            local = download_file(img_url, media_dir, prefix=slug)
            if local:
                profile.setdefault("local_images", []).append(str(media_dir / local))

        conductors.append(profile)

    save_json(conductors, OUT_DIR / "conductors" / "all_conductors.json")
    print(f"  Total conductors scraped: {len(conductors)}", flush=True)
    return conductors


# ── PERFORMERS ──────────────────────────────────────────────────────────

PERFORMER_URLS = {
    "guqin": "https://chinesemusics.com/en_us/info-db/performers/p-guqin/",
    "pipa": "https://chinesemusics.com/en_us/info-db/performers/p-pipa/",
    "guzheng": "https://chinesemusics.com/en_us/info-db/performers/p-guzheng/",
    "erhu": "https://chinesemusics.com/en_us/info-db/performers/p-erhu/",
    "wind": "https://chinesemusics.com/en_us/info-db/performers/p-wind/",
    "other_pluck": "https://chinesemusics.com/en_us/info-db/performers/p-opluck/",
    "other_bow": "https://chinesemusics.com/en_us/info-db/performers/p-obow/",
    "other_wind": "https://chinesemusics.com/en_us/info-db/performers/p-owind/",
    "percussion": "https://chinesemusics.com/en_us/info-db/performers/p-percussion/",
    "orchestra": "https://chinesemusics.com/en_us/info-db/performers/p-orchestra/",
}


def scrape_performers():
    print("\n=== PERFORMERS ===", flush=True)
    all_performers = {}
    media_dir = OUT_DIR / "media" / "performers"

    for cat, base_url in PERFORMER_URLS.items():
        out_file = OUT_DIR / "performers" / f"{cat}.json"
        if out_file.exists():
            with open(out_file) as f:
                existing = json.load(f)
            all_performers[cat] = existing
            print(f"\n  Category: {cat} — ALREADY DONE ({len(existing)} entries)", flush=True)
            continue

        print(f"\n  Category: {cat}", flush=True)
        entries = scrape_paginated_listing(base_url)
        print(f"  Found {len(entries)} performer links for {cat}", flush=True)

        performers = []
        for i, entry in enumerate(entries):
            print(f"    [{i+1}/{len(entries)}] {entry['name']}", flush=True)
            profile = scrape_person_profile(entry["url"])
            profile["name_from_listing"] = entry["name"]
            profile["instrument_category"] = cat

            for img_url in profile.get("images", []):
                slug = re.sub(r'[^\w]', '_', entry["name"][:15])
                local = download_file(img_url, media_dir / cat, prefix=slug)
                if local:
                    profile.setdefault("local_images", []).append(
                        str(media_dir / cat / local)
                    )

            performers.append(profile)

        all_performers[cat] = performers
        save_json(performers, out_file)
        print(f"  Saved {len(performers)} {cat} performers", flush=True)

    save_json(
        {cat: len(v) for cat, v in all_performers.items()},
        OUT_DIR / "performers" / "summary.json",
    )
    total = sum(len(v) for v in all_performers.values())
    print(f"\n  Total performers scraped: {total}", flush=True)
    return all_performers


# ── PROGRAMME NOTES ──────────────────────────────────────────────────────

PNOTES_URLS = {
    "guqin": "https://chinesemusics.com/en_us/info-db/p-notes/guqin-pn/",
    "pipa": "https://chinesemusics.com/en_us/info-db/p-notes/pipa-pn/",
    "guzheng": "https://chinesemusics.com/en_us/info-db/p-notes/guzheng-pn/",
    "erhu": "https://chinesemusics.com/en_us/info-db/p-notes/erhu-pn/",
    "dizi": "https://chinesemusics.com/en_us/info-db/p-notes/dizi-pn/",
    "other_pluck": "https://chinesemusics.com/en_us/info-db/p-notes/other-plucked-pn/",
    "other_bow": "https://chinesemusics.com/en_us/info-db/p-notes/other-bow-pn/",
    "other_wind": "https://chinesemusics.com/en_us/info-db/p-notes/other-wind-pn/",
    "percussion": "https://chinesemusics.com/en_us/info-db/p-notes/percussion-pn/",
    "orchestra": "https://chinesemusics.com/en_us/info-db/p-notes/or-en-pn/",
    "ensemble": "https://chinesemusics.com/en_us/info-db/p-notes/en-pn/",
}


def scrape_programme_notes_page(url: str, category: str) -> dict:
    print(f"  Scraping programme notes: {category}", flush=True)
    soup = fetch(url)
    if not soup:
        return {"category": category, "url": url, "error": "failed to fetch"}

    content = get_content_div(soup)
    full_text = extract_body_text(soup)
    images = extract_images(content, url)
    media = extract_media(soup, url)

    # Discover numbered subpages (e.g., guqin-pn2, guqin-pn3)
    subpages = []
    slug_match = re.search(r'/([^/]+)-pn/?$', url)
    if slug_match:
        slug = slug_match.group(1)
        for n in range(2, 15):
            sub_url = f"https://chinesemusics.com/en_us/info-db/p-notes/{slug}-pn{n}/"
            subpages.append(sub_url)

    sub_texts = []
    for sub_url in subpages:
        print(f"    Subpage: {sub_url}", flush=True)
        sub_soup = fetch(sub_url)
        if sub_soup:
            sub_content = get_content_div(sub_soup)
            sub_text = extract_body_text(sub_soup)
            sub_images = extract_images(sub_content, sub_url)
            sub_media = extract_media(sub_soup, sub_url)
            if sub_text and len(sub_text) > 50:
                sub_texts.append({
                    "url": sub_url,
                    "text": sub_text,
                    "images": sub_images,
                    "media": sub_media,
                })
                images.extend(sub_images)

    # Parse individual pieces from the main page
    pieces = []
    current_piece = None
    for el in content.descendants:
        if not isinstance(el, Tag):
            continue
        if el.name in ("h2", "h3", "h4", "h5"):
            if current_piece and current_piece.get("description"):
                pieces.append(current_piece)
            title = el.get_text(strip=True)
            anchor = el.get("id", "")
            if title:
                current_piece = {
                    "title": title,
                    "anchor": anchor,
                    "description": "",
                }
        elif el.name == "p" and current_piece is not None:
            txt = el.get_text(strip=True)
            if txt:
                current_piece["description"] += txt + "\n"
    if current_piece and current_piece.get("description"):
        pieces.append(current_piece)

    # Also parse pieces from subpages
    for sub in sub_texts:
        sub_soup = BeautifulSoup(f"<div>{sub['text']}</div>", "html.parser")

    return {
        "category": category,
        "url": url,
        "full_text": full_text,
        "pieces": pieces,
        "subpage_texts": sub_texts,
        "images": list(dict.fromkeys(images)),
        "media": media,
    }


def scrape_all_programme_notes():
    print("\n=== PROGRAMME NOTES ===", flush=True)
    all_notes = {}
    for cat, url in PNOTES_URLS.items():
        out_file = OUT_DIR / "programme_notes" / f"{cat}.json"
        if out_file.exists():
            with open(out_file) as f:
                existing = json.load(f)
            all_notes[cat] = existing
            n_pieces = len(existing.get("pieces", []))
            print(f"  {cat}: ALREADY DONE ({n_pieces} pieces)", flush=True)
            continue

        data = scrape_programme_notes_page(url, cat)
        all_notes[cat] = data
        save_json(data, out_file)
        n_pieces = len(data.get("pieces", []))
        n_subs = len(data.get("subpage_texts", []))
        print(f"  {cat}: {n_pieces} pieces, {n_subs} subpages", flush=True)

    save_json(
        {cat: len(v.get("pieces", [])) for cat, v in all_notes.items()},
        OUT_DIR / "programme_notes" / "summary.json",
    )
    return all_notes


# ── HISTORY ──────────────────────────────────────────────────────────────

HISTORY_ARTICLES = [
    "https://chinesemusics.com/en_us/2022/02/10/e-general002/",
    "https://chinesemusics.com/en_us/2022/02/09/e-general004/",
    "https://chinesemusics.com/en_us/2022/02/08/e-general003/",
    "https://chinesemusics.com/en_us/2022/02/06/e-general005/",
    "https://chinesemusics.com/en_us/2022/02/05/e-general006/",
]


def scrape_history():
    print("\n=== HISTORY ===", flush=True)
    articles = []
    for url in HISTORY_ARTICLES:
        print(f"  Fetching: {url}", flush=True)
        soup = fetch(url)
        if not soup:
            articles.append({"url": url, "error": "failed to fetch"})
            continue

        title_el = soup.find("h1", class_="entry-title") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""
        body_text = extract_body_text(soup)
        images = extract_images(soup, url)
        media = extract_media(soup, url)

        for img_url in images:
            download_file(img_url, OUT_DIR / "media" / "history")

        articles.append({
            "url": url,
            "title": title,
            "full_text": body_text,
            "images": images,
            "media": media,
        })

    save_json(articles, OUT_DIR / "history" / "articles.json")
    print(f"  Total history articles: {len(articles)}", flush=True)
    return articles


# ── MAIN ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60, flush=True)
    print("Chinese Music Archive Scraper", flush=True)
    print(f"Target: {BASE_URL}", flush=True)
    print(f"Output: {OUT_DIR}", flush=True)
    print("=" * 60, flush=True)

    section = sys.argv[1] if len(sys.argv) > 1 else "all"

    if section in ("all", "instruments"):
        scrape_all_instruments()
    if section in ("all", "composers"):
        scrape_composers()
    if section in ("all", "conductors"):
        scrape_conductors()
    if section in ("all", "performers"):
        scrape_performers()
    if section in ("all", "programme_notes"):
        scrape_all_programme_notes()
    if section in ("all", "history"):
        scrape_history()

    print("\n" + "=" * 60, flush=True)
    print("SCRAPING COMPLETE", flush=True)
    print("=" * 60, flush=True)

    for subdir in sorted(OUT_DIR.iterdir()):
        if subdir.is_dir():
            n_files = sum(1 for f in subdir.rglob("*") if f.is_file())
            print(f"  {subdir.name}: {n_files} files", flush=True)


if __name__ == "__main__":
    main()
