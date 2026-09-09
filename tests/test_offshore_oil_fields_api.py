import unittest

from src.offshore_oil_fields_api import load_offshore_oil_fields, parse_query, query_offshore_oil_fields


class OffshoreOilFieldsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fields = load_offshore_oil_fields()

    def test_has_fifty_ranked_records(self):
        self.assertEqual(len(self.fields), 50)
        self.assertEqual([field["id"] for field in self.fields], list(range(1, 51)))
        self.assertEqual(self.fields[0]["dailyProductionBbl"], 4800)

    def test_search_and_pagination(self):
        result = query_offshore_oil_fields(self.fields, "Brazil", 1)
        self.assertLessEqual(len(result["data"]), 10)
        self.assertTrue(all(field["country"] == "Brazil" for field in result["data"]))

    def test_query_is_case_insensitive_and_page_positive(self):
        self.assertEqual(parse_query({"country_code": ["BR"]}), ("BR", 1))
        with self.assertRaisesRegex(ValueError, "page must be a positive integer"):
            parse_query({"country_code": ["BR"], "page": ["0"]})


if __name__ == "__main__":
    unittest.main()
