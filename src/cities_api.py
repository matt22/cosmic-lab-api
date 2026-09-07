"""Query and response helpers for the cities endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


CITIES_PAGE_SIZE = 10
CITIES_PATH = Path(__file__).with_name("cities.json")
CITIES_CACHE_KEY_VERSION = "2026-09-07"


class QueryError(ValueError):
    """An invalid cities API query."""


def load_cities(path: Path = CITIES_PATH) -> list[dict[str, Any]]:
    """Load the bundled cities dataset."""
    return json.loads(path.read_text(encoding="utf-8"))


def parse_query(params: Mapping[str, Sequence[str]]) -> tuple[str, int]:
    """Validate and normalize the supported query parameters."""
    unsupported = sorted(set(params) - {"country_code", "page"})
    if unsupported:
        raise QueryError(
            "Unsupported query parameter(s): " + ", ".join(unsupported)
        )

    country_values = params.get("country_code", [])
    if len(country_values) != 1 or not country_values[0].strip():
        raise QueryError("country_code is required and must appear exactly once")

    country_code = country_values[0].strip().upper()
    if len(country_code) != 2 or not country_code.isalpha():
        raise QueryError("country_code must be a two-letter code")

    page_values = params.get("page", ["1"])
    if len(page_values) != 1:
        raise QueryError("page must appear at most once")
    try:
        page = int(page_values[0])
    except ValueError as error:
        raise QueryError("page must be a positive integer") from error

    if page < 1:
        raise QueryError("page must be a positive integer")

    return country_code, page


def serialize_city(city: Mapping[str, Any]) -> dict[str, Any]:
    """Combine latitude and longitude while retaining every other field."""
    return {
        "id": city["id"],
        "city_name": city["cityName"],
        "country_code": city["countryCode"],
        "country_name": city["countryName"],
        "continent": city["continent"],
        "coordinates": f"{city['latitude']},{city['longitude']}",
    }


def build_result_set(
    cities: Sequence[Mapping[str, Any]], country_code: str
) -> list[dict[str, Any]]:
    """Build the complete ordered result set for a country."""
    return [
        serialize_city(city)
        for city in cities
        if city["countryCode"] == country_code
    ]


def cache_key(country_code: str) -> str:
    """Return a versioned key shared by every page of a country query."""
    return f"api:v1:cities:{CITIES_CACHE_KEY_VERSION}:country_code:{country_code}"


async def get_result_set(
    cache: Any,
    cities: Sequence[Mapping[str, Any]],
    country_code: str,
    ttl_seconds: int,
) -> list[dict[str, Any]]:
    """Read a country result set from KV, populating it on a cache miss."""
    key = cache_key(country_code)
    cached_value = await cache.get(key)
    if cached_value is not None:
        return json.loads(cached_value)

    result_set = build_result_set(cities, country_code)
    await cache.put(
        key,
        json.dumps(result_set, separators=(",", ":")),
        expirationTtl=ttl_seconds,
    )
    return result_set


def paginate_result_set(
    result_set: Sequence[Mapping[str, Any]], page: int
) -> dict[str, Any]:
    """Return one fixed-size page from an ordered cities result set."""
    start_index = (page - 1) * CITIES_PAGE_SIZE
    page_records = result_set[start_index : start_index + CITIES_PAGE_SIZE]

    return {
        "pagination": {
            "page": page,
            "page_size": CITIES_PAGE_SIZE,
            "count": len(page_records),
            "total": len(result_set),
        },
        "data": list(page_records),
    }


def query_cities(
    cities: Sequence[Mapping[str, Any]], country_code: str, page: int
) -> dict[str, Any]:
    """Build and paginate a result without using a cache."""
    return paginate_result_set(build_result_set(cities, country_code), page)
