#!/usr/bin/env python3
"""Build the 100-largest-US-airports dataset from FAA and OurAirports data."""

import argparse
import csv
import json
import re
from pathlib import Path


AIRPORT_COUNT = 100


def read_regions(path):
    with open(path, encoding="utf-8", newline="") as source:
        return {
            row["code"]: row["name"]
            for row in csv.DictReader(source)
            if row["code"].startswith("US-") and row["name"]
        }


def read_airports(path):
    by_code = {}
    with open(path, encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            if row["iso_country"] != "US":
                continue
            for code in (row["iata_code"], row["local_code"]):
                if code:
                    by_code[code] = row
    return by_code


def build_airports(ranking_path, airport_path, region_path):
    regions = read_regions(region_path)
    airport_metadata = read_airports(airport_path)
    airports = []
    with open(ranking_path, encoding="utf-8-sig", newline="") as source:
        for ranking in csv.DictReader(source):
            if not ranking["Rank"]:
                continue
            code = ranking["Locid"].strip()
            metadata = airport_metadata.get(code)
            if metadata is None:
                # FAA rankings include US territories; this dataset is limited to
                # airports whose ISO country is the United States.
                continue
            region_code = metadata["iso_region"]
            icao_code = metadata["icao_code"]
            iata_code = metadata["iata_code"]
            if not all(
                (
                    metadata["name"],
                    ranking["City"],
                    ranking["ST"],
                    regions.get(region_code),
                    iata_code,
                    icao_code,
                    metadata["latitude_deg"],
                    metadata["longitude_deg"],
                )
            ):
                raise ValueError(f"Incomplete airport metadata for {code}")
            airports.append(
                {
                    "id": len(airports) + 1,
                    "airportName": metadata["name"],
                    "iataCode": iata_code,
                    "icaoCode": icao_code,
                    "city": ranking["City"].strip(),
                    "stateCode": ranking["ST"].strip(),
                    "stateName": regions[region_code],
                    "countryCode": "US",
                    "countryName": "United States",
                    "latitude": round(float(metadata["latitude_deg"]), 4),
                    "longitude": round(float(metadata["longitude_deg"]), 4),
                }
            )
            if len(airports) == AIRPORT_COUNT:
                break
    airports.sort(key=lambda airport: airport["id"])
    return airports


def validate(airports):
    assert len(airports) == AIRPORT_COUNT
    assert [airport["id"] for airport in airports] == list(
        range(1, AIRPORT_COUNT + 1)
    )
    assert len({airport["iataCode"] for airport in airports}) == AIRPORT_COUNT
    assert len({airport["icaoCode"] for airport in airports}) == AIRPORT_COUNT
    for airport in airports:
        assert set(airport) == {
            "id",
            "airportName",
            "iataCode",
            "icaoCode",
            "city",
            "stateCode",
            "stateName",
            "countryCode",
            "countryName",
            "latitude",
            "longitude",
        }
        assert all(value != "" for value in airport.values())
        assert re.fullmatch(r"[A-Z]{3}", airport["iataCode"])
        assert re.fullmatch(r"[A-Z0-9]{4}", airport["icaoCode"])
        assert re.fullmatch(r"[A-Z]{2}", airport["stateCode"])
        assert airport["countryCode"] == "US"
        assert -90 <= airport["latitude"] <= 90
        assert -180 <= airport["longitude"] <= 180


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", required=True)
    parser.add_argument("--airports", required=True)
    parser.add_argument("--regions", required=True)
    parser.add_argument("--output", default="data/airports.json")
    args = parser.parse_args()

    airports = build_airports(args.ranking, args.airports, args.regions)
    validate(airports)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as destination:
        json.dump(airports, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    print(f"Wrote {len(airports)} validated airports to {output}")


if __name__ == "__main__":
    main()
