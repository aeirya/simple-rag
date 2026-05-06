import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests


def clean_contents_block(block: str) -> str:
    text = re.sub(r"\s+", " ", block)

    items = re.findall(
        r"[*+\-]\s+\[(\d+(?:\.\d+)*)\s+([^\]]+?)\]\(#[^)]+\)",
        text
    )

    lines = []
    for num, title in items:
        indent = "  " * num.count(".")
        lines.append(f"{indent}- {title.strip()}")

    return "\n".join(lines)

def drop_ending_sections(article: str) -> str:
    return re.split(
        r"\n(?:Notes|References|Further reading|External links)\n[-=]+\n",
        article,
        maxsplit=1,
    )[0].strip()

def simplify_markdown_links(text: str) -> str:
    text = re.sub(r"\[\[edit\]\([^)]+\)\]", "", text)
    text = re.sub(r"\[\[\d+\]\]\([^)]+\)", "", text)
    # remove empty links/images:
    text = re.sub(r"!?\[\]\([^)]+\)", "", text)
    # normal links/images to text
    text = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", text)
    
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def split_title_section(title: str) -> tuple[str, str | None]:
    if "#" not in title:
        return title.replace("_", " "), None

    page, section = title.split("#", 1)
    return page.replace("_", " "), section.replace("_", " ")

def extract_title(lines: list[str], page_title: str):
    for i in range(len(lines) - 1):
        if lines[i].strip() == page_title and re.fullmatch(r"=+", lines[i + 1].strip()):
            title_text = f"{page_title}\n{'=' * len(page_title)}"
            return i, title_text

    raise ValueError(f"Title not found: {page_title}")

def extract_contents(lines: list[str], title_i: int) -> str:
    contents_i = next(
        (i for i, l in enumerate(lines) if l.strip() == "Contents"),
        None
    )

    if contents_i is None or contents_i >= title_i:
        return ""

    block = "\n".join(lines[contents_i:title_i])
    return clean_contents_block(block)

def extract_article_body(lines: list[str], title_i: int, title_text: str) -> str:
    article = "\n".join(lines[title_i:])

    marker = "From Wikipedia, the free encyclopedia"
    if marker in article:
        article = article.split(marker, 1)[1].strip()

    article = f"{title_text}\n\n{article}"

    article = drop_ending_sections(article)
    article = drop_wiki_footer(article)
    article = simplify_markdown_links(article)

    return article

def heading_text(line: str) -> str:
    return re.sub(r"^#{1,6}\s*", "", line.strip()).strip()


def heading_level(lines: list[str], i: int) -> int | None:
    line = lines[i].strip()

    # ### Heading
    m = re.match(r"^(#{1,6})\s+", line)
    if m:
        return len(m.group(1))

    # Heading
    # -------
    if i < len(lines) - 1 and re.fullmatch(r"[-=]+", lines[i + 1].strip()):
        return 1 if lines[i + 1].startswith("=") else 2

    return None


def extract_section(md_text: str, section_title: str) -> str:
    lines = md_text.splitlines()

    start = None
    start_level = None

    for i, line in enumerate(lines):
        level = heading_level(lines, i)
        if level and heading_text(line) == section_title:
            start = i
            start_level = level
            break

    if start is None:
        raise ValueError(f"Section not found: {section_title}")

    end = len(lines)

    for j in range(start + 1, len(lines)):
        level = heading_level(lines, j)
        if level and level <= start_level:
            end = j
            break

    section = "\n".join(lines[start:end])
    section = drop_ending_sections(section)
    section = drop_wiki_footer(section)
    section = simplify_markdown_links(section)

    return section.strip()

def clean_wiki_md(md_text: str, page_title: str) -> str:
    lines = md_text.splitlines()

    title_i, title_text = extract_title(lines, page_title)
    contents = extract_contents(lines, title_i)
    article = extract_article_body(lines, title_i, title_text)

    parts = []
    if contents:
        parts.append("Contents\n--------\n")
        parts.append(contents)
        parts.append("")

    parts.append(article)
    return "\n".join(parts).strip()

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

def drop_wiki_footer(text: str) -> str:
    return re.split(
        r'\n(?:Retrieved from|Category:|Categories:|Hidden categories:|\* This page was last edited)',
        text,
        maxsplit=1,
    )[0].strip()

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

        text = drop_wiki_footer(text)
        text = simplify_markdown_links(text)

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