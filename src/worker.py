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


AIRPORTS = load_airports()
CITIES = load_cities()


def error_response(message: str, status: int) -> Response:
    return Response.json({"error": {"message": message}}, status=status)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)

        if request.method != "GET":
            return error_response("Method not allowed", 405)

        if url.path not in {"/api/v1/airports", "/api/v1/cities"}:
            return error_response("Not found", 404)

        try:
            params = parse_qs(url.query, keep_blank_values=True)
            if url.path == "/api/v1/airports":
                state_code, page = parse_query(params)
            else:
                country_code, page = parse_cities_query(params)
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

        result_set = await get_cities_result_set(
            self.env.QUERY_CACHE,
            CITIES,
            country_code,
            int(self.env.CITIES_CACHE_TTL_SECONDS),
        )
        return Response.json(paginate_cities_result_set(result_set, page))
