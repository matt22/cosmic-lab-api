"""Query helpers for the incidents endpoint."""

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from .search_api import paginate, parse_search_query, substring_matches
except ImportError:  # Cloudflare Worker loads source modules as top-level files.
    from search_api import paginate, parse_search_query, substring_matches

INCIDENTS_PAGE_SIZE = 10
INCIDENTS_PATH = Path(__file__).with_name("incidents.json")


def load_incidents(path: Path = INCIDENTS_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_query(params: Mapping[str, Sequence[str]]) -> tuple[str, int]:
    return parse_search_query(params, "service_name")


def query_incidents(
    incidents: Sequence[Mapping[str, Any]], service_name: str, page: int
):
    return paginate(
        substring_matches(incidents, "serviceName", service_name),
        page,
        INCIDENTS_PAGE_SIZE,
    )
