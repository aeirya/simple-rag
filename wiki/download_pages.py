from pathlib import Path
from wiki.pages import wiki_pages
from wiki.fetch import get_wiki_text


def download_wiki_pages(
    pages: dict[str, list[str]] = wiki_pages,
    output_dir: str | Path = "data/wiki",
) -> dict[str, list[str]]:
    downloaded = {}

    for topic, titles in pages.items():
        downloaded[topic] = []

        for title in titles:
            try:
                get_wiki_text(title, output_dir=output_dir)
                downloaded[topic].append(title)
            except Exception as e:
                print(f"failed: {title} -> {e}")

    return downloaded