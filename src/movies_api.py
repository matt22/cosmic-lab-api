"""Query helpers for the movies endpoint."""

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from .search_api import paginate, parse_search_query, substring_matches
except ImportError:  # Cloudflare Worker loads source modules as top-level files.
    from search_api import paginate, parse_search_query, substring_matches

MOVIES_PAGE_SIZE = 10
MOVIES_PATH = Path(__file__).with_name("movies.json")


def load_movies(path: Path = MOVIES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_query(params: Mapping[str, Sequence[str]]) -> tuple[str, int]:
    return parse_search_query(params, "title")


def query_movies(movies: Sequence[Mapping[str, Any]], title: str, page: int):
    return paginate(substring_matches(movies, "title", title), page, MOVIES_PAGE_SIZE)
