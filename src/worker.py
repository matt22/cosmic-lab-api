"""Cloudflare Python Worker entry point for Cosmic Lab API."""

from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

from airports_api import (
    QueryError,
    get_result_set,
    load_airports,
    paginate_result_set,
    parse_query,
)
from cities_api import (
    QueryError as CitiesQueryError,
    get_result_set as get_cities_result_set,
    load_cities,
    paginate_result_set as paginate_cities_result_set,
    parse_query as parse_cities_query,
)
from books_api import load_books, parse_query as parse_books_query, query_books
from incidents_api import (
    load_incidents,
    parse_query as parse_incidents_query,
    query_incidents,
)
from movies_api import load_movies, parse_query as parse_movies_query, query_movies


AIRPORTS = load_airports()
CITIES = load_cities()
BOOKS = load_books()
MOVIES = load_movies()
INCIDENTS = load_incidents()


def error_response(message: str, status: int) -> Response:
    return Response.json({"error": {"message": message}}, status=status)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)

        if request.method != "GET":
            return error_response("Method not allowed", 405)

        if url.path not in {
            "/api/v1/airports",
            "/api/v1/cities",
            "/api/v1/books",
            "/api/v1/movies",
            "/api/v1/incidents",
        }:
            return error_response("Not found", 404)

        try:
            params = parse_qs(url.query, keep_blank_values=True)
            if url.path == "/api/v1/airports":
                state_code, page = parse_query(params)
            elif url.path == "/api/v1/cities":
                country_code, page = parse_cities_query(params)
            elif url.path == "/api/v1/books":
                title, page = parse_books_query(params)
            elif url.path == "/api/v1/movies":
                title, page = parse_movies_query(params)
            else:
                service_name, page = parse_incidents_query(params)
        except (QueryError, CitiesQueryError) as error:
            return error_response(str(error), 400)

        if url.path == "/api/v1/airports":
            result_set = await get_result_set(
                self.env.QUERY_CACHE,
                AIRPORTS,
                state_code,
                int(self.env.AIRPORTS_CACHE_TTL_SECONDS),
            )
            return Response.json(paginate_result_set(result_set, page))

        if url.path == "/api/v1/books":
            return Response.json(query_books(BOOKS, title, page))
        if url.path == "/api/v1/movies":
            return Response.json(query_movies(MOVIES, title, page))
        if url.path == "/api/v1/incidents":
            return Response.json(query_incidents(INCIDENTS, service_name, page))

        result_set = await get_cities_result_set(
            self.env.QUERY_CACHE,
            CITIES,
            country_code,
            int(self.env.CITIES_CACHE_TTL_SECONDS),
        )
        return Response.json(paginate_cities_result_set(result_set, page))
