#!/usr/bin/env python3
"""Build deterministic fictional service incidents for API exercises."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random


INCIDENT_COUNT = 100
SNAPSHOT_TIME = datetime(2026, 9, 4, 18, 0, tzinfo=timezone.utc)
SERVICES = (
    "Airport Data API",
    "Book Catalog API",
    "City Search API",
    "Movie Search API",
    "Practice API Gateway",
)
SEVERITIES = ("minor", "major", "critical")


def timestamp(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def build_incidents():
    random = Random(20260904)
    statuses = ["resolved"] * 60 + ["active"] * 20 + ["planned"] * 20
    random.shuffle(statuses)
    incidents = []
    for index, status in enumerate(statuses, start=1):
        service = SERVICES[(index * 3 + 1) % len(SERVICES)]
        severity = SEVERITIES[(index * 5 + 2) % len(SEVERITIES)]
        if status == "resolved":
            start = SNAPSHOT_TIME - timedelta(
                days=random.randint(2, 180), minutes=random.randint(0, 1439)
            )
            end = start + timedelta(minutes=random.randint(8, 720))
        elif status == "active":
            start = SNAPSHOT_TIME - timedelta(
                minutes=random.randint(15, 4320)
            )
            end = None
        else:
            start = None
            end = SNAPSHOT_TIME + timedelta(
                days=random.randint(1, 90), minutes=random.randint(0, 1439)
            )
        incidents.append(
            {
                "id": index,
                "serviceName": service,
                "severity": severity,
                "status": status,
                "startTime": timestamp(start) if start else None,
                "endTime": timestamp(end) if end else None,
            }
        )
    return incidents


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(incidents):
    assert len(incidents) == INCIDENT_COUNT
    assert [incident["id"] for incident in incidents] == list(
        range(1, INCIDENT_COUNT + 1)
    )
    for incident in incidents:
        assert set(incident) == {
            "id",
            "serviceName",
            "severity",
            "status",
            "startTime",
            "endTime",
        }
        assert incident["serviceName"] in SERVICES
        assert incident["severity"] in SEVERITIES
        start = incident["startTime"]
        end = incident["endTime"]
        assert start is not None or end is not None
        if incident["status"] == "planned":
            assert start is None and parse_timestamp(end) > SNAPSHOT_TIME
        elif incident["status"] == "active":
            assert end is None and parse_timestamp(start) <= SNAPSHOT_TIME
        else:
            assert incident["status"] == "resolved"
            assert start is not None and end is not None
            assert parse_timestamp(start) < parse_timestamp(end) <= SNAPSHOT_TIME


def main():
    incidents = build_incidents()
    validate(incidents)
    output = Path("data/incidents.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as destination:
        json.dump(incidents, destination, indent=2)
        destination.write("\n")
    print(f"Wrote {len(incidents)} validated incidents to {output}")


if __name__ == "__main__":
    main()
