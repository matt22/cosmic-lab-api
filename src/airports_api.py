"""Query and response helpers for the airports endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


AIRPORTS_PAGE_SIZE = 3
AIRPORTS_PATH = Path(__file__).with_name("airports.json")
AIRPORTS_CACHE_KEY_VERSION = "2026-09-04"


class QueryError(ValueError):
    """An invalid airports API query."""


def load_airports(path: Path = AIRPORTS_PATH) -> list[dict[str, Any]]:
    """Load the bundled airports dataset."""
    return json.loads(path.read_text(encoding="utf-8"))


def parse_query(params: Mapping[str, Sequence[str]]) -> tuple[str, int]:
    """Validate and normalize the supported query parameters."""
    unsupported = sorted(set(params) - {"state_code", "page"})
    if unsupported:
        raise QueryError(
            "Unsupported query parameter(s): " + ", ".join(unsupported)
        )

    state_values = params.get("state_code", [])
    if len(state_values) != 1 or not state_values[0].strip():
        raise QueryError("state_code is required and must appear exactly once")

    state_code = state_values[0].strip().upper()
    if len(state_code) != 2 or not state_code.isalpha():
        raise QueryError("state_code must be a two-letter code")

    page_values = params.get("page", ["1"])
    if len(page_values) != 1:
        raise QueryError("page must appear at most once")
    try:
        page = int(page_values[0])
    except ValueError as error:
        raise QueryError("page must be a positive integer") from error

    if page < 1:
        raise QueryError("page must be a positive integer")

    return state_code, page


def serialize_airport(airport: Mapping[str, Any]) -> dict[str, Any]:
    """Combine latitude and longitude while retaining every other field."""
    return {
        "id": airport["id"],
        "airport_name": airport["airportName"],
        "iata_code": airport["iataCode"],
        "icao_code": airport["icaoCode"],
        "city": airport["city"],
        "state_code": airport["stateCode"],
        "state_name": airport["stateName"],
        "country_code": airport["countryCode"],
        "country_name": airport["countryName"],
        "coordinates": f"{airport['latitude']},{airport['longitude']}",
    }


def build_result_set(
    airports: Sequence[Mapping[str, Any]], state_code: str
) -> list[dict[str, Any]]:
    """Build the complete ordered result set for a state."""
    return [
        serialize_airport(airport)
        for airport in airports
        if airport["stateCode"] == state_code
    ]


def cache_key(state_code: str) -> str:
    """Return a versioned key shared by every page of a state query."""
    return f"api:v1:airports:{AIRPORTS_CACHE_KEY_VERSION}:state_code:{state_code}"


async def get_result_set(
    cache: Any,
    airports: Sequence[Mapping[str, Any]],
    state_code: str,
    ttl_seconds: int,
) -> list[dict[str, Any]]:
    """Read a state result set from KV, populating it on a cache miss."""
    key = cache_key(state_code)
    cached_value = await cache.get(key)
    if cached_value is not None:
        return json.loads(cached_value)

    result_set = build_result_set(airports, state_code)
    await cache.put(
        key,
        json.dumps(result_set, separators=(",", ":")),
        expirationTtl=ttl_seconds,
    )
    return result_set


def paginate_result_set(
    result_set: Sequence[Mapping[str, Any]], page: int
) -> dict[str, Any]:
    """Return one fixed-size page from an ordered airports result set."""
    start_index = (page - 1) * AIRPORTS_PAGE_SIZE
    page_records = result_set[start_index : start_index + AIRPORTS_PAGE_SIZE]

    return {
        "pagination": {
            "page": page,
            "page_size": AIRPORTS_PAGE_SIZE,
            "count": len(page_records),
            "total": len(result_set),
        },
        "data": list(page_records),
    }


def query_airports(
    airports: Sequence[Mapping[str, Any]], state_code: str, page: int
) -> dict[str, Any]:
    """Build and paginate a result without using a cache."""
    return paginate_result_set(build_result_set(airports, state_code), page)
