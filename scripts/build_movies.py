#!/usr/bin/env python3
"""Build the practice movie dataset from Wikidata and IMDb snapshots."""

import argparse
import csv
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path


MPA_RATINGS = {"G", "PG", "PG-13", "R", "NC-17"}
FIRST_YEAR = 1990
LAST_YEAR = 2026
MOVIE_COUNT = 1000


def read_imdb_ratings(path):
    ratings = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            ratings[row["tconst"]] = (
                float(row["averageRating"]),
                int(row["numVotes"]),
            )
    return ratings


def read_imdb_movies(path, wanted_ids):
    movies = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source, delimiter="\t"):
            imdb_id = row["tconst"]
            if imdb_id not in wanted_ids or row["titleType"] != "movie":
                continue
            if row["startYear"] == "\\N" or row["runtimeMinutes"] == "\\N":
                continue
            year = int(row["startYear"])
            if FIRST_YEAR <= year <= LAST_YEAR:
                movies[imdb_id] = {
                    "title": row["primaryTitle"],
                    "year": year,
                    "runtimeMinutes": int(row["runtimeMinutes"]),
                }
    return movies


def read_wikidata(path):
    with open(path, encoding="utf-8") as source:
        rows = json.load(source)["results"]["bindings"]

    grouped = defaultdict(
        lambda: {
            "imdbIds": set(),
            "directors": set(),
            "familyNames": set(),
            "ratings": set(),
        }
    )
    for row in rows:
        film_id = row["film"]["value"].rsplit("/", 1)[-1]
        item = grouped[film_id]
        item["imdbIds"].add(row["imdb"]["value"])
        item["directors"].add(row["director"]["value"])
        item["familyNames"].add(row["familyNameLabel"]["value"])
        item["ratings"].add(row["ratingLabel"]["value"])
    return grouped


def build_candidates(wikidata, imdb_movies, imdb_ratings):
    candidates = []
    seen_imdb_ids = set()
    for item in wikidata.values():
        if not (
            len(item["imdbIds"]) == 1
            and len(item["directors"]) == 1
            and len(item["familyNames"]) == 1
            and len(item["ratings"]) == 1
        ):
            continue
        imdb_id = next(iter(item["imdbIds"]))
        mpa_rating = next(iter(item["ratings"]))
        family_name = next(iter(item["familyNames"]))
        if (
            imdb_id in seen_imdb_ids
            or imdb_id not in imdb_movies
            or imdb_id not in imdb_ratings
            or mpa_rating not in MPA_RATINGS
            or re.fullmatch(r"Q\d+", family_name)
        ):
            continue
        seen_imdb_ids.add(imdb_id)
        score, votes = imdb_ratings[imdb_id]
        candidates.append(
            {
                **imdb_movies[imdb_id],
                "mpaaRating": mpa_rating,
                "scoreRating": score,
                "directorLastName": family_name,
                "_votes": votes,
            }
        )
    return candidates


def select_movies(candidates):
    by_year = defaultdict(list)
    for movie in candidates:
        by_year[movie["year"]].append(movie)

    missing_years = [
        year for year in range(FIRST_YEAR, LAST_YEAR + 1) if not by_year[year]
    ]
    if missing_years:
        raise ValueError(f"No complete candidates for years: {missing_years}")

    selected = []
    selected_keys = set()
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        movie = max(by_year[year], key=lambda item: item["_votes"])
        selected.append(movie)
        selected_keys.add((movie["title"], movie["year"]))

    ranked = sorted(candidates, key=lambda item: item["_votes"], reverse=True)
    for movie in ranked:
        key = (movie["title"], movie["year"])
        if key in selected_keys:
            continue
        selected.append(movie)
        selected_keys.add(key)
        if len(selected) == MOVIE_COUNT:
            break

    if len(selected) != MOVIE_COUNT:
        raise ValueError(f"Expected {MOVIE_COUNT} movies, found {len(selected)}")

    selected.sort(key=lambda item: (item["year"], item["title"].casefold()))
    return [
        {
            "id": index,
            "title": movie["title"],
            "year": movie["year"],
            "runtimeMinutes": movie["runtimeMinutes"],
            "mpaaRating": movie["mpaaRating"],
            "scoreRating": movie["scoreRating"],
            "directorLastName": movie["directorLastName"],
        }
        for index, movie in enumerate(selected, start=1)
    ]


def validate(movies):
    assert len(movies) == MOVIE_COUNT
    assert [movie["id"] for movie in movies] == list(range(1, MOVIE_COUNT + 1))
    assert len({(movie["title"], movie["year"]) for movie in movies}) == MOVIE_COUNT
    assert {movie["year"] for movie in movies} == set(
        range(FIRST_YEAR, LAST_YEAR + 1)
    )
    for movie in movies:
        assert set(movie) == {
            "id",
            "title",
            "year",
            "runtimeMinutes",
            "mpaaRating",
            "scoreRating",
            "directorLastName",
        }
        assert movie["title"] and movie["directorLastName"]
        assert not re.fullmatch(r"Q\d+", movie["directorLastName"])
        assert movie["runtimeMinutes"] > 0
        assert movie["mpaaRating"] in MPA_RATINGS
        assert 1 <= movie["scoreRating"] <= 10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wikidata", required=True)
    parser.add_argument("--imdb-basics", required=True)
    parser.add_argument("--imdb-ratings", required=True)
    parser.add_argument("--output", default="data/movies.json")
    args = parser.parse_args()

    wikidata = read_wikidata(args.wikidata)
    wanted_ids = {
        imdb_id for item in wikidata.values() for imdb_id in item["imdbIds"]
    }
    imdb_ratings = read_imdb_ratings(args.imdb_ratings)
    imdb_movies = read_imdb_movies(args.imdb_basics, wanted_ids)
    candidates = build_candidates(wikidata, imdb_movies, imdb_ratings)
    movies = select_movies(candidates)
    validate(movies)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as destination:
        json.dump(movies, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    print(f"Wrote {len(movies)} validated movies to {output}")


if __name__ == "__main__":
    main()
