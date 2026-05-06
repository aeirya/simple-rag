from wiki.fetch import get_wiki_text as get_text
from wiki.download_pages import download_wiki_pages as download
from wiki.pages import wiki_pages as pages

__all__ = [
    "get_text",
    "download",
    "pages",
]