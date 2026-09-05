import unittest
from pathlib import Path

from src.airports_api import (
    AIRPORTS_PAGE_SIZE,
    cache_key,
    get_result_set,
    load_airports,
    parse_query,
    query_airports,
)


class FakeCache:
    def __init__(self):
        self.values = {}
        self.put_calls = []

    async def get(self, key):
        return self.values.get(key)

    async def put(self, key, value, **options):
        self.values[key] = value
        self.put_calls.append((key, value, options))


class AirportsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.airports = load_airports()

    def test_returns_three_airports_per_page(self):
        result = query_airports(self.airports, "CA", 1)

        self.assertEqual(list(result), ["pagination", "data"])
        self.assertEqual(len(result["data"]), AIRPORTS_PAGE_SIZE)
        self.assertEqual(result["pagination"]["page"], 1)
        self.assertEqual(result["pagination"]["page_size"], 3)
        self.assertEqual(result["pagination"]["count"], 3)

    def test_second_page_uses_page_number(self):
        first_page = query_airports(self.airports, "CA", 1)
        second_page = query_airports(self.airports, "CA", 2)

        self.assertTrue(
            {airport["id"] for airport in first_page["data"]}.isdisjoint(
                airport["id"] for airport in second_page["data"]
            )
        )
        self.assertEqual(second_page["pagination"]["page"], 2)

    def test_coordinates_replace_latitude_and_longitude(self):
        airport = query_airports(self.airports, "GA", 1)["data"][0]

        self.assertEqual(airport["coordinates"], "33.6367,-84.4281")
        self.assertNotIn("latitude", airport)
        self.assertNotIn("longitude", airport)
        self.assertEqual(
            set(airport),
            {
                "id",
                "airport_name",
                "iata_code",
                "icao_code",
                "city",
                "state_code",
                "state_name",
                "country_code",
                "country_name",
                "coordinates",
            },
        )

    def test_state_code_is_case_insensitive(self):
        state_code, page = parse_query({"state_code": [" ca "]})

        self.assertEqual((state_code, page), ("CA", 1))

    def test_page_defaults_to_one(self):
        state_code, page = parse_query({"state_code": ["CA"]})
        result = query_airports(self.airports, state_code, page)

        self.assertEqual(page, 1)
        self.assertEqual(result["pagination"]["page"], 1)

    def test_accepts_page_number(self):
        state_code, page = parse_query({"state_code": ["CA"], "page": ["2"]})
        result = query_airports(self.airports, state_code, page)

        self.assertEqual(page, 2)
        self.assertEqual(result["pagination"]["page"], 2)

    def test_page_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "page must be a positive integer"):
            parse_query({"state_code": ["CA"], "page": ["0"]})

    def test_rejects_offset_parameter(self):
        with self.assertRaisesRegex(ValueError, "Unsupported query parameter"):
            parse_query({"state_code": ["CA"], "offset": ["3"]})

    def test_rejects_unsupported_search_parameters(self):
        with self.assertRaisesRegex(ValueError, "Unsupported query parameter"):
            parse_query({"state_code": ["CA"], "city": ["Oakland"]})

    def test_empty_result_has_pagination_metadata(self):
        result = query_airports(self.airports, "ZZ", 1)

        self.assertEqual(result["data"], [])
        self.assertEqual(result["pagination"]["count"], 0)
        self.assertEqual(result["pagination"]["total"], 0)

    def test_bundled_dataset_matches_source_dataset(self):
        repository_root = Path(__file__).parents[1]

        self.assertEqual(
            (repository_root / "src" / "airports.json").read_bytes(),
            (repository_root / "data" / "airports.json").read_bytes(),
        )


class AirportsCacheTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.airports = load_airports()

    async def test_cache_write_uses_configured_ttl(self):
        cache = FakeCache()

        result_set = await get_result_set(cache, self.airports, "CA", 10800)

        self.assertEqual(len(result_set), 12)
        self.assertEqual(len(cache.put_calls), 1)
        key, _, options = cache.put_calls[0]
        self.assertEqual(key, cache_key("CA"))
        self.assertEqual(options, {"expirationTtl": 10800})

    async def test_cache_hit_does_not_rewrite_value(self):
        cache = FakeCache()

        first = await get_result_set(cache, self.airports, "CA", 10800)
        second = await get_result_set(cache, [], "CA", 10800)

        self.assertEqual(second, first)
        self.assertEqual(len(cache.put_calls), 1)


if __name__ == "__main__":
    unittest.main()
