#!/usr/bin/env python3
"""Fetch compact canonical-edition metadata for Open Library search results."""

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


BATCH_SIZE = 40
API_URL = "https://openlibrary.org/api/books"
USER_AGENT = "cosmic-lab-api-dataset/1.0 (https://github.com/matt22/cosmic-lab-api)"


def request_batch(keys):
    query = urllib.parse.urlencode(
        {
            "bibkeys": ",".join(f"OLID:{key}" for key in keys),
            "jscmd": "data",
            "format": "json",
        }
    )
    request = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def compact(record):
    return {
        "key": record.get("key"),
        "title": record.get("title"),
        "authors": [author.get("name") for author in record.get("authors", [])],
        "numberOfPages": record.get("number_of_pages"),
        "isbn13": record.get("identifiers", {}).get("isbn_13", []),
        "publishDate": record.get("publish_date"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("search", nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    keys = []
    seen = set()
    for path in args.search:
        with open(path, encoding="utf-8") as source:
            for work in json.load(source)["docs"]:
                key = work.get("cover_edition_key")
                if key and key not in seen:
                    seen.add(key)
                    keys.append(key)

    editions = {}
    for offset in range(0, len(keys), BATCH_SIZE):
        batch = keys[offset : offset + BATCH_SIZE]
        for attempt in range(3):
            try:
                response = request_batch(batch)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        for key, record in response.items():
            editions[key.removeprefix("OLID:")] = compact(record)
        time.sleep(0.1)

    output = Path(args.output)
    with output.open("w", encoding="utf-8") as destination:
        json.dump(editions, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    print(f"Wrote {len(editions)} canonical editions to {output}")


if __name__ == "__main__":
    main()
