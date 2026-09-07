import unittest
from pathlib import Path

from src.cities_api import (
    CITIES_PAGE_SIZE,
    cache_key,
    get_result_set,
    load_cities,
    parse_query,
    query_cities,
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


class CitiesApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cities = load_cities()

    def test_returns_three_cities_per_page(self):
        result = query_cities(self.cities, "NG", 1)

        self.assertEqual(list(result), ["pagination", "data"])
        self.assertEqual(len(result["data"]), CITIES_PAGE_SIZE)
        self.assertEqual(result["pagination"]["page"], 1)
        self.assertEqual(result["pagination"]["page_size"], 3)
        self.assertEqual(result["pagination"]["count"], 3)

    def test_second_page_uses_page_number(self):
        first_page = query_cities(self.cities, "NG", 1)
        second_page = query_cities(self.cities, "NG", 2)

        self.assertTrue(
            {city["id"] for city in first_page["data"]}.isdisjoint(
                city["id"] for city in second_page["data"]
            )
        )
        self.assertEqual(second_page["pagination"]["page"], 2)

    def test_coordinates_replace_latitude_and_longitude(self):
        city = query_cities(self.cities, "NG", 1)["data"][0]

        self.assertEqual(city["coordinates"], "5.1066,7.3667")
        self.assertNotIn("latitude", city)
        self.assertNotIn("longitude", city)
        self.assertEqual(
            set(city),
            {
                "id",
                "city_name",
                "country_code",
                "country_name",
                "continent",
                "coordinates",
            },
        )

    def test_country_code_is_case_insensitive(self):
        country_code, page = parse_query({"country_code": [" ng "]})

        self.assertEqual((country_code, page), ("NG", 1))

    def test_page_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "page must be a positive integer"):
            parse_query({"country_code": ["NG"], "page": ["0"]})

    def test_rejects_unsupported_search_parameters(self):
        with self.assertRaisesRegex(ValueError, "Unsupported query parameter"):
            parse_query({"country_code": ["NG"], "city": ["Aba"]})

    def test_empty_result_has_pagination_metadata(self):
        result = query_cities(self.cities, "ZZ", 1)

        self.assertEqual(result["data"], [])
        self.assertEqual(result["pagination"]["count"], 0)
        self.assertEqual(result["pagination"]["total"], 0)

    def test_bundled_dataset_matches_source_dataset(self):
        repository_root = Path(__file__).parents[1]

        self.assertEqual(
            (repository_root / "src" / "cities.json").read_bytes(),
            (repository_root / "data" / "cities.json").read_bytes(),
        )


class CitiesCacheTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cities = load_cities()

    async def test_cache_write_uses_configured_ttl(self):
        cache = FakeCache()

        result_set = await get_result_set(cache, self.cities, "NG", 10800)

        self.assertGreater(len(result_set), CITIES_PAGE_SIZE)
        self.assertEqual(len(cache.put_calls), 1)
        key, _, options = cache.put_calls[0]
        self.assertEqual(key, cache_key("NG"))
        self.assertEqual(options, {"expirationTtl": 10800})

    async def test_cache_hit_does_not_rewrite_value(self):
        cache = FakeCache()

        first = await get_result_set(cache, self.cities, "NG", 10800)
        second = await get_result_set(cache, [], "NG", 10800)

        self.assertEqual(second, first)
        self.assertEqual(len(cache.put_calls), 1)


if __name__ == "__main__":
    unittest.main()
