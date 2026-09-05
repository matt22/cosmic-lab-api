"""Cloudflare Python Worker entry point for Cosmic Lab API."""

from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

from airports_api import QueryError, load_airports, parse_query, query_airports


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

        return Response.json(query_airports(AIRPORTS, state_code, page))
