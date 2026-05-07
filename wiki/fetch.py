import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests
from wiki.clean import clean_wiki_md, extract_section, clean_wiki_text


def split_title_section(title: str) -> tuple[str, str | None]:
    if "#" not in title:
        return title.replace("_", " "), None

    page, section = title.split("#", 1)
    return page.replace("_", " "), section.replace("_", " ")

def title_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    return unquote(slug).replace("_", " ")


def safe_filename(text: str) -> str:
    text = text.lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_\-]+", "", text)


def wiki_url_from_title(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"


def scrape_wiki_raw(url: str, output_dir) -> Path:
    output_dir = Path(output_dir)

    page_title = title_from_url(url)
    raw_md = output_dir / f"{safe_filename(page_title)}_raw.md"

    if not raw_md.exists():
        subprocess.run(
            ["scrapling", "extract", "get", url, str(raw_md)],
            check=True,
        )

    return raw_md


def scrape_wiki(url: str, output_dir: str | Path = "data/wiki") -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    page_title = title_from_url(url)
    
    tmp_md = scrape_wiki_raw(url, output_dir)
    
    # 2) clean markdown
    text = tmp_md.read_text(encoding="utf-8")
    cleaned = clean_wiki_md(text, page_title=page_title)

    # 3) save cleaned output
    clean_md = output_dir / f"{safe_filename(page_title)}.md"
    clean_md.write_text(cleaned, encoding="utf-8")

    # optional: remove raw file
    tmp_md.unlink(missing_ok=True)

    return clean_md

def search_wiki_url(title: str) -> str:
    print("searching for a wiki page for", title)

    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": title,
        "limit": 1,
        "namespace": 0,
        "format": "json",
    }
    headers = {"User-Agent": "simple-rag/0.1 (coursework)"}

    res = requests.get(search_url, params=params, headers=headers, timeout=20)

    if not res.ok:
        raise RuntimeError(f"Wikipedia search failed: {res.status_code}")

    try:
        data = res.json()
    except Exception:
        raise RuntimeError(f"Wikipedia returned non-JSON:\n{res.text[:500]}")

    if not data[3]:
        raise ValueError(f"No Wikipedia page found for: {title}")

    return data[3][0]


def fetch_wiki_text_from_url(
    url: str,
    title: str,
    section_title: str | None,
    output_dir: Path,
) -> str | None:
    try:
        if section_title:
            raw_text = scrape_wiki_raw(url, output_dir).read_text(encoding="utf-8")
            text = extract_section(raw_text, section_title)
        else:
            text = scrape_wiki(url, output_dir).read_text(encoding="utf-8")

        text = clean_wiki_text(text)

        return text or None

    except Exception as e:
        print(f"failed: {title} -> {e}")
        return None

def cache_name(title: str, section_title: str | None = None) -> str:
    name = safe_filename(title)
    if section_title:
        name += "__" + safe_filename(section_title)
    return name + ".md"

def get_wiki_text(title: str, output_dir="data/wiki") -> str:
    page_title, section_title = split_title_section(title)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / cache_name(page_title, section_title)

    if path.exists():
        return path.read_text(encoding="utf-8")

    # 1) try direct URL
    direct_url = wiki_url_from_title(page_title)

    text = fetch_wiki_text_from_url(
        direct_url,
        title,
        section_title,
        output_dir,
    )

    # 2) if direct failed, try search result URL
    if text is None:
        search_url = search_wiki_url(page_title)

        text = fetch_wiki_text_from_url(
            search_url,
            title,
            section_title,
            output_dir,
        )

    if text is None:
        raise ValueError(f"Could not fetch Wikipedia text for: {title}")

    path.write_text(text, encoding="utf-8")
    return text