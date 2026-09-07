"""Query helpers for the books endpoint."""

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from .search_api import paginate, parse_search_query, substring_matches
except ImportError:  # Cloudflare Worker loads source modules as top-level files.
    from search_api import paginate, parse_search_query, substring_matches

BOOKS_PAGE_SIZE = 10
BOOKS_PATH = Path(__file__).with_name("books.json")


def load_books(path: Path = BOOKS_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_query(params: Mapping[str, Sequence[str]]) -> tuple[str, int]:
    return parse_search_query(params, "title")


def query_books(books: Sequence[Mapping[str, Any]], title: str, page: int):
    return paginate(substring_matches(books, "title", title), page, BOOKS_PAGE_SIZE)
