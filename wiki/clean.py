import re


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
        r"\n(?:Notes|References|Further reading|External links|See also)\n[-=]+\n",
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

def clean_wiki_text(text: str) -> str:
    text = drop_ending_sections(text)
    text = drop_wiki_footer(text)
    text = simplify_markdown_links(text)
    return text.strip()

def extract_article_body(lines: list[str], title_i: int, title_text: str) -> str:
    article = "\n".join(lines[title_i:])

    marker = "From Wikipedia, the free encyclopedia"
    if marker in article:
        article = article.split(marker, 1)[1].strip()

    article = f"{title_text}\n\n{article}"
    article = clean_wiki_text(article)

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
    section = clean_wiki_text(section)

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

def drop_wiki_footer(text: str) -> str:
    return re.split(
        r'\n(?:Retrieved from|Category:|Categories:|Hidden categories:|\* This page was last edited)',
        text,
        maxsplit=1,
    )[0].strip()
