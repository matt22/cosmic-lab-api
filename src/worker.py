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


AIRPORTS = load_airports()


def error_response(message: str, status: int) -> Response:
    return Response.json({"error": {"message": message}}, status=status)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)

        if request.method != "GET":
            return error_response("Method not allowed", 405)

        if url.path != "/api/v1/airports":
            return error_response("Not found", 404)

        try:
            params = parse_qs(url.query, keep_blank_values=True)
            state_code, page = parse_query(params)
        except QueryError as error:
            return error_response(str(error), 400)

        result_set = await get_result_set(
            self.env.QUERY_CACHE,
            AIRPORTS,
            state_code,
            int(self.env.AIRPORTS_CACHE_TTL_SECONDS),
        )
        return Response.json(paginate_result_set(result_set, page))
