#!/usr/bin/env python3
"""Build a flat dataset of 1,000 widely read books from Open Library data."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


BOOK_COUNT = 1000
DATE_FORMATS = (
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
)


def normalize_date(value):
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value.strip()).replace("Sept ", "Sep ")
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, date_format).date().isoformat()
        except ValueError:
            pass
    return None


def valid_isbn13(value):
    if not re.fullmatch(r"\d{13}", value):
        return False
    total = sum(
        int(digit) * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(value[:12])
    )
    return (10 - total % 10) % 10 == int(value[-1])


def load_ranked_works(paths):
    works = []
    seen = set()
    for path in paths:
        with open(path, encoding="utf-8") as source:
            for work in json.load(source)["docs"]:
                key = work.get("key")
                if key and key not in seen:
                    seen.add(key)
                    works.append(work)
    return works


def build_books(search_paths, edition_paths):
    works = load_ranked_works(search_paths)
    editions = {}
    for edition_path in edition_paths:
        with open(edition_path, encoding="utf-8") as source:
            editions.update(json.load(source))

    books = []
    seen_isbns = set()
    seen_works = set()
    for work in works:
        edition_key = work.get("cover_edition_key")
        edition = editions.get(edition_key)
        if not edition or len(edition.get("authors", [])) != 1:
            continue
        title = work.get("title")
        author = edition["authors"][0]
        pages = edition.get("numberOfPages")
        publication_date = normalize_date(edition.get("publishDate"))
        isbn_candidates = sorted(
            {isbn for isbn in edition.get("isbn13", []) if valid_isbn13(isbn)}
        )
        if not (
            isinstance(title, str)
            and title.strip()
            and isinstance(author, str)
            and author.strip()
            and isinstance(pages, int)
            and 20 <= pages <= 2500
            and publication_date
            and isbn_candidates
        ):
            continue
        isbn = next((value for value in isbn_candidates if value not in seen_isbns), None)
        work_key = (title.casefold(), author.casefold())
        if isbn is None or work_key in seen_works:
            continue
        seen_isbns.add(isbn)
        seen_works.add(work_key)
        books.append(
            {
                "id": len(books) + 1,
                "title": title.strip(),
                "author": author.strip(),
                "isbn13": isbn,
                "publicationDate": publication_date,
                "pages": pages,
            }
        )
        if len(books) == BOOK_COUNT:
            break
    return books


def validate(books):
    assert len(books) == BOOK_COUNT
    assert [book["id"] for book in books] == list(range(1, BOOK_COUNT + 1))
    assert len({book["isbn13"] for book in books}) == BOOK_COUNT
    assert len({(book["title"].casefold(), book["author"].casefold()) for book in books}) == BOOK_COUNT
    for book in books:
        assert set(book) == {
            "id",
            "title",
            "author",
            "isbn13",
            "publicationDate",
            "pages",
        }
        assert book["title"] and book["author"]
        assert valid_isbn13(book["isbn13"])
        assert normalize_date(book["publicationDate"]) == book["publicationDate"]
        assert isinstance(book["pages"], int) and 20 <= book["pages"] <= 2500


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("search", nargs="+")
    parser.add_argument("--editions", nargs="+", required=True)
    parser.add_argument("--output", default="data/books.json")
    args = parser.parse_args()

    books = build_books(args.search, args.editions)
    validate(books)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as destination:
        json.dump(books, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    print(f"Wrote {len(books)} validated books to {output}")


if __name__ == "__main__":
    main()
