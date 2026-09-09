"""Query helpers for the offshore oil fields endpoint."""
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
try:
    from .search_api import paginate, parse_search_query, substring_matches
except ImportError:
    from search_api import paginate, parse_search_query, substring_matches

OFFSHORE_OIL_FIELDS_PAGE_SIZE = 10
OFFSHORE_OIL_FIELDS_PATH = Path(__file__).with_name("offshore_oil_fields.json")

def load_offshore_oil_fields(path: Path = OFFSHORE_OIL_FIELDS_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))

def parse_query(params: Mapping[str, Sequence[str]]) -> tuple[str, int]:
    return parse_search_query(params, "country_code")

def query_offshore_oil_fields(fields: Sequence[Mapping[str, Any]], country_code: str, page: int):
    return paginate(substring_matches(fields, "country", country_code), page, OFFSHORE_OIL_FIELDS_PAGE_SIZE)
