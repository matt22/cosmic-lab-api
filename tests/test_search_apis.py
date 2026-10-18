import unittest

from src.books_api import load_books, query_books
from src.incidents_api import load_incidents, query_incidents
from src.incidents_api import parse_query as parse_incidents_query
from src.movies_api import load_movies, query_movies
from src.movies_api import parse_query as parse_movies_query


class SearchApiTests(unittest.TestCase):
    def test_movie_title_is_case_insensitive_substring(self):
        result = query_movies(load_movies(), "jUrAsSiC p", 1)
        self.assertTrue(result["data"])
        self.assertTrue(
            all("jurassic p" in movie["title"].casefold() for movie in result["data"])
        )

    def test_book_title_is_case_insensitive_substring(self):
        result = query_books(load_books(), "atomic", 1)
        self.assertTrue(result["data"])
        self.assertTrue(all("atomic" in book["title"].casefold() for book in result["data"]))

    def test_incident_service_name_is_case_insensitive_substring(self):
        result = query_incidents(load_incidents(), "gateway", 1)
        self.assertTrue(result["data"])
        self.assertTrue(
            all("gateway" in incident["serviceName"].casefold() for incident in result["data"])
        )

    def test_missing_service_name_lists_all_incidents(self):
        incidents = load_incidents()
        service_name, page = parse_incidents_query({})
        result = query_incidents(incidents, service_name, page)
        self.assertEqual(result["pagination"]["total"], len(incidents))

    def test_empty_or_repeated_service_name_is_rejected(self):
        for params in ({"service_name": [""]}, {"service_name": ["api", "book"]}):
            with self.assertRaises(ValueError):
                parse_incidents_query(params)

    def test_missing_movie_title_lists_all_movies(self):
        movies = load_movies()
        title, page = parse_movies_query({})
        self.assertEqual(query_movies(movies, title, page)["pagination"]["total"], len(movies))

    def test_injection_like_input_is_treated_as_literal_text(self):
        query = "' OR 1=1 --"
        self.assertEqual(query_movies(load_movies(), query, 1)["data"], [])
        self.assertEqual(query_books(load_books(), query, 1)["data"], [])
        self.assertEqual(query_incidents(load_incidents(), query, 1)["data"], [])


if __name__ == "__main__":
    unittest.main()
