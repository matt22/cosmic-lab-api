"""Shared helpers for case-insensitive substring search endpoints."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def parse_search_query(
    params: Mapping[str, Sequence[str]], field: str
) -> tuple[str, int]:
    """Validate a required search value and optional page number."""
    unsupported = sorted(set(params) - {field, "page"})
    if unsupported:
        raise ValueError(
            "Unsupported query parameter(s): " + ", ".join(unsupported)
        )

    values = params.get(field, [])
    if len(values) != 1 or not values[0].strip():
        raise ValueError(f"{field} is required and must appear exactly once")

    page_values = params.get("page", ["1"])
    if len(page_values) != 1:
        raise ValueError("page must appear at most once")
    try:
        page = int(page_values[0])
    except ValueError as error:
        raise ValueError("page must be a positive integer") from error
    if page < 1:
        raise ValueError("page must be a positive integer")

    return values[0].strip(), page


def paginate(records: Sequence[Mapping[str, Any]], page: int, page_size: int):
    """Return one fixed-size page and pagination metadata."""
    start = (page - 1) * page_size
    page_records = records[start : start + page_size]
    return {
        "pagination": {
            "page": page,
            "page_size": page_size,
            "count": len(page_records),
            "total": len(records),
        },
        "data": list(page_records),
    }


def substring_matches(
    records: Sequence[Mapping[str, Any]], field: str, query: str
) -> list[Mapping[str, Any]]:
    """Find records whose field contains query, ignoring case."""
    normalized_query = query.casefold()
    return [
        record
        for record in records
        if normalized_query in str(record[field]).casefold()
    ]
