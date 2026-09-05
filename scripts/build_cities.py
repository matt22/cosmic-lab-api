#!/usr/bin/env python3
"""Build the practice city dataset from a GeoNames snapshot."""

import argparse
import csv
import json
import re
from pathlib import Path


CITY_COUNT = 1000
CONTINENTS = {
    "AF": "Africa",
    "AN": "Antarctica",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "OC": "Oceania",
    "SA": "South America",
}


def read_countries(path):
    countries = {}
    with open(path, encoding="utf-8", newline="") as source:
        rows = (line for line in source if not line.startswith("#"))
        for row in csv.reader(rows, delimiter="\t"):
            if len(row) < 9 or row[8] not in CONTINENTS:
                continue
            countries[row[0]] = {
                "countryName": row[4],
                "continent": CONTINENTS[row[8]],
            }
    return countries


def read_cities(path, countries):
    candidates = []
    with open(path, encoding="utf-8", newline="") as source:
        for row in csv.reader(source, delimiter="\t"):
            if len(row) != 19:
                continue
            country_code = row[8]
            if country_code not in countries or not row[1] or not row[14]:
                continue
            population = int(row[14])
            latitude = round(float(row[4]), 4)
            longitude = round(float(row[5]), 4)
            candidates.append(
                {
                    "cityName": row[1],
                    "countryCode": country_code,
                    **countries[country_code],
                    "latitude": latitude,
                    "longitude": longitude,
                    "_population": population,
                    "_geonameId": int(row[0]),
                }
            )
    return candidates


def select_cities(candidates):
    selected = []
    seen = set()
    ranked = sorted(
        candidates,
        key=lambda city: (-city["_population"], city["_geonameId"]),
    )
    for city in ranked:
        key = (city["cityName"].casefold(), city["countryCode"])
        if key in seen:
            continue
        seen.add(key)
        selected.append(city)
        if len(selected) == CITY_COUNT:
            break

    if len(selected) != CITY_COUNT:
        raise ValueError(f"Expected {CITY_COUNT} cities, found {len(selected)}")

    selected.sort(
        key=lambda city: (
            city["cityName"].casefold(),
            city["countryCode"],
            city["_geonameId"],
        )
    )
    return [
        {
            "id": index,
            "cityName": city["cityName"],
            "countryCode": city["countryCode"],
            "countryName": city["countryName"],
            "continent": city["continent"],
            "latitude": city["latitude"],
            "longitude": city["longitude"],
        }
        for index, city in enumerate(selected, start=1)
    ]


def validate(cities):
    assert len(cities) == CITY_COUNT
    assert [city["id"] for city in cities] == list(range(1, CITY_COUNT + 1))
    assert len(
        {(city["cityName"].casefold(), city["countryCode"]) for city in cities}
    ) == CITY_COUNT
    for city in cities:
        assert set(city) == {
            "id",
            "cityName",
            "countryCode",
            "countryName",
            "continent",
            "latitude",
            "longitude",
        }
        assert city["cityName"] and city["countryName"]
        assert re.fullmatch(r"[A-Z]{2}", city["countryCode"])
        assert city["continent"] in CONTINENTS.values()
        assert -90 <= city["latitude"] <= 90
        assert -180 <= city["longitude"] <= 180


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", required=True)
    parser.add_argument("--countries", required=True)
    parser.add_argument("--output", default="data/cities.json")
    args = parser.parse_args()

    countries = read_countries(args.countries)
    candidates = read_cities(args.cities, countries)
    cities = select_cities(candidates)
    validate(cities)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as destination:
        json.dump(cities, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    print(f"Wrote {len(cities)} validated cities to {output}")


if __name__ == "__main__":
    main()
