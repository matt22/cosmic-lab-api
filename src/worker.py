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
from offshore_oil_fields_api import (
    load_offshore_oil_fields,
    parse_query as parse_offshore_oil_fields_query,
    query_offshore_oil_fields,
)


AIRPORTS = load_airports()
CITIES = load_cities()
BOOKS = load_books()
MOVIES = load_movies()
INCIDENTS = load_incidents()
OFFSHORE_OIL_FIELDS = load_offshore_oil_fields()

README_URL = "https://github.com/matt22/cosmic-lab-api/blob/main/README.md"
DATASETS = (
    ("AIRPORTS", "100 records · US airports", "Filter by state code", "/api/v1/airports?state_code=CA&page=1"),
    ("CITIES", "1,000 records · Global cities", "Filter by country code", "/api/v1/cities?country_code=JP&page=1"),
    ("BOOKS", "1,000 records · Books and authors", "Search by title", "/api/v1/books?title=atomic&page=1"),
    ("MOVIES", "1,000 records · Films and ratings", "Search by title", "/api/v1/movies?title=Jurassic%20P&page=1"),
    ("INCIDENTS", "100 records · Fictional service events", "Search by service name", "/api/v1/incidents?service_name=gateway&page=1"),
)

DATASET_EXAMPLES = {
    "AIRPORTS": '{\n  "id": 1,\n  "airportName": "Hartsfield Jackson Atlanta International Airport",\n  "iataCode": "ATL",\n  "icaoCode": "KATL",\n  "city": "Atlanta",\n  "stateCode": "GA",\n  "stateName": "Georgia",\n  "countryCode": "US",\n  "countryName": "United States",\n  "latitude": 33.6367,\n  "longitude": -84.4281\n}',
    "CITIES": '{\n  "id": 1,\n  "cityName": "Aba",\n  "countryCode": "NG",\n  "countryName": "Nigeria",\n  "continent": "Africa",\n  "latitude": 5.1066,\n  "longitude": 7.3667\n}',
    "BOOKS": '{\n  "id": 1,\n  "title": "Atomic Habits",\n  "author": "James Clear",\n  "isbn13": "9781804220207",\n  "publicationDate": "2018-10-16",\n  "pages": 168\n}',
    "MOVIES": '{\n  "id": 1,\n  "title": "Back to the Future Part III",\n  "year": 1990,\n  "runtimeMinutes": 118,\n  "mpaaRating": "PG",\n  "scoreRating": 7.5,\n  "directorLastName": "Zemeckis"\n}',
    "INCIDENTS": '{\n  "id": 1,\n  "serviceName": "Practice API Gateway",\n  "severity": "major",\n  "status": "resolved",\n  "startTime": "2026-03-18T16:56:00Z",\n  "endTime": "2026-03-19T04:33:00Z"\n}',
}


def html_document(base_url: str) -> str:
    dataset_cards = "".join(
        f'''<article class="dataset"><div class="dataset-top"><span>{name}</span><span class="dot"></span></div>
        <p>{description}</p><small>{action}</small><code><a href="{path}">{base_url}{path}</a></code><pre>{DATASET_EXAMPLES[name]}</pre></article>'''
        for name, description, action, path in DATASETS
    )
    sample_json = '''{
  "data": [
    {
      "id": 1,
      "airportName": "Los Angeles International Airport",
      "iataCode": "LAX",
      "icaoCode": "KLAX",
      "city": "Los Angeles",
      "stateCode": "CA",
      "stateName": "California",
      "countryCode": "US",
      "countryName": "United States",
      "latitude": 33.9425,
      "longitude": -118.4081
    },
    {
      "id": 2,
      "airportName": "San Francisco International Airport",
      "iataCode": "SFO",
      "icaoCode": "KSFO",
      "city": "San Francisco",
      "stateCode": "CA",
      "stateName": "California",
      "countryCode": "US",
      "countryName": "United States",
      "latitude": 37.6213,
      "longitude": -122.3790
    }
  ],
  "page": 1,
  "pageSize": 3,
  "total": 10
}'''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cosmic Lab API</title><style>
:root{{--ink:#f5f0e7;--muted:#a9aaa3;--line:#353832;--panel:#181b18;--accent:#d7f36b;--bg:#0d0f0e}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}}
a{{color:inherit}}.shell{{max-width:1120px;margin:auto;padding:20px 24px 48px}}header{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid var(--line);padding-bottom:16px}}
.brand{{display:flex;gap:14px;align-items:center}}.mark{{display:grid;place-items:center;width:38px;height:38px;border:1px solid var(--accent);color:var(--accent);font-weight:800}}h1{{font-size:16px;margin:0;letter-spacing:.08em}}.eyebrow{{color:var(--accent);font-size:11px;letter-spacing:.14em}}.links{{display:flex;gap:16px;font-size:12px;color:var(--muted)}}
main{{padding-top:44px}}.hero{{display:block}}h2{{font:700 clamp(42px,7vw,88px)/.92 ui-sans-serif,system-ui,sans-serif;letter-spacing:-.07em;margin:0;max-width:720px}}.hero p{{color:var(--muted);max-width:560px;margin:16px 0 0}}
.status{{border:1px solid var(--line);background:var(--panel);padding:20px}}.status strong{{display:block;color:var(--accent);font-size:12px;letter-spacing:.13em;margin-bottom:16px}}.status div{{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding:11px 0;color:var(--muted);font-size:12px}}.status b{{color:var(--ink);font-weight:500}}
section{{margin-top:52px}}.section-label{{color:var(--muted);font-size:11px;letter-spacing:.14em;margin-bottom:12px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}}.dataset{{background:var(--panel);padding:16px;min-height:150px}}.dataset:last-child{{grid-column:1 / -1}}.dataset-top{{display:flex;justify-content:space-between;align-items:center;color:var(--accent);font-size:13px;letter-spacing:.1em;font-weight:700}}.dot{{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}}.dataset p{{color:var(--ink);margin:22px 0 4px}}.dataset small{{display:block;color:var(--muted);font-size:11px;margin-bottom:18px}}code{{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#c9cabf;font-size:11px}}code a{{color:#c9cabf;text-decoration:none}}code a:hover{{color:var(--accent)}}.cosmic-cell{{min-height:420px;background:linear-gradient(143deg,transparent 0 37%,rgba(231,241,231,.5) 38% 48%,rgba(130,161,166,.3) 49% 55%,transparent 56%),radial-gradient(ellipse at 68% 25%,rgba(238,247,235,.32) 0 7%,rgba(82,111,119,.38) 8% 11%,transparent 12%),linear-gradient(143deg,transparent 0 47%,rgba(231,241,231,.42) 48% 50%,transparent 51%),linear-gradient(28deg,transparent 0 55%,rgba(231,241,231,.32) 56% 58%,transparent 59%),linear-gradient(153deg,transparent 0 61%,rgba(231,241,231,.26) 62% 64%,transparent 65%),radial-gradient(circle at 72% 24%,rgba(215,243,107,.9) 0 2px,transparent 3px),radial-gradient(circle at 25% 68%,rgba(215,243,107,.55) 0 1px,transparent 2px),radial-gradient(circle at 78% 78%,rgba(245,240,231,.5) 0 1px,transparent 2px),radial-gradient(ellipse at 60% 42%,rgba(81,58,140,.6),transparent 48%),radial-gradient(ellipse at 25% 80%,rgba(22,93,110,.55),transparent 58%),linear-gradient(135deg,#11151d,#20233a 48%,#10282b)}}
.callout{{display:grid;grid-template-columns:1fr 1fr;gap:24px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:28px 0}}.callout h3{{font:600 26px/1.1 ui-sans-serif,system-ui,sans-serif;margin:0;letter-spacing:-.04em}}.callout p{{color:var(--muted);margin:0}}footer{{margin-top:28px;color:var(--muted);font-size:11px}}@media(max-width:700px){{.hero,.callout{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr}}.links{{display:none}}main{{padding-top:42px}}}}
.response{{border:1px solid var(--line);background:var(--panel)}}.response-head{{display:flex;justify-content:space-between;gap:16px;padding:15px 18px;border-bottom:1px solid var(--line);color:var(--accent);font-size:11px}}.response-head a{{color:var(--muted);white-space:nowrap}}pre{{margin:0;padding:22px;overflow:auto;color:#d9dbc9;font:12px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace}} 
.oil-cell{{min-height:300px;padding:20px;background:radial-gradient(circle at 76% 25%,rgba(215,243,107,.85) 0 3px,transparent 4px),linear-gradient(145deg,#101b24,#123e49 52%,#1c263b);display:flex;flex-direction:column;justify-content:space-between}}.oil-cell h3{{margin:0;font:700 30px/.95 ui-sans-serif,system-ui,sans-serif;letter-spacing:-.05em}}.oil-cell p{{max-width:270px;color:#dce8d9;margin:0;font-size:12px;line-height:1.6}}.oil-cell a{{color:var(--accent);font-size:11px;text-decoration:none;letter-spacing:.08em}}.oil-sample{{background:#181b18;padding:16px;min-height:300px;overflow:hidden}}.oil-sample strong{{display:block;color:var(--accent);font-size:12px;letter-spacing:.1em;margin-bottom:12px}}.oil-sample pre{{padding:0;font-size:11px;line-height:1.55}}
</style></head><body><div class="shell"><header><div class="brand"><div class="mark">CL</div><div><h1>COSMIC LAB API</h1><div class="eyebrow">PUBLIC API</div></div></div><nav class="links"><a href="{README_URL}">README ↗</a><a href="{base_url}/api/v1/airports?state_code=CA&page=1">LIVE API ↗</a></nav></header>
<main><div class="hero"><div><div class="eyebrow">API ONLINE · REST · JSON</div><h2>Cosmic Lab API.</h2><p>A REST API with six datasets, readable endpoints, query parameters, filtering, pagination, and JSON responses.</p></div></div>
<section><div class="section-label">RESPONSE METADATA</div><div class="response"><div class="response-head"><span>GET /api/v1/airports?state_code=CA&amp;page=1</span><a href="{base_url}/api/v1/airports?state_code=CA&amp;page=1">OPEN JSON ↗</a></div><pre>{{
  "page": 1,
  "pageSize": 3,
  "total": 10,
  "data": [ ... ]
}}</pre></div></section>
<section><div class="section-label">DATASETS / 05 · ONE RECORD EACH</div><div class="grid">{dataset_cards}<div class="oil-sample"><strong>OIL FIELDS · SAMPLE</strong><pre>{DATASET_EXAMPLES["OIL FIELDS"]}</pre></div></div></section>
</main><footer>Cosmic Lab · Built for curious developers · <a href="{README_URL}">Documentation ↗</a></footer></div></body></html>'''


def root_response(base_url: str) -> dict[str, object]:
    return {
        "message": "Cosmic Lab API",
        "readme": README_URL,
        "examples": {
            "airports": f"{base_url}/api/v1/airports?state_code=CA&page=1",
            "cities": f"{base_url}/api/v1/cities?country_code=JP&page=1",
            "books": f"{base_url}/api/v1/books?title=atomic&page=1",
            "movies": f"{base_url}/api/v1/movies?title=Jurassic%20P&page=1",
            "incidents": f"{base_url}/api/v1/incidents?service_name=gateway&page=1",
            "offshore_oil_fields": f"{base_url}/api/v1/offshore-oil-fields?country_code=BR&page=1",
        },
    }


def error_response(message: str, status: int) -> Response:
    return Response.json({"error": {"message": message}}, status=status)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)

        if request.method != "GET":
            return error_response("Method not allowed", 405)

        if url.path == "/":
            base_url = f"{url.scheme}://{url.netloc}"
            if "application/json" in request.headers.get("Accept", ""):
                return Response.json(root_response(base_url))
            return Response(html_document(base_url), headers={"Content-Type": "text/html; charset=utf-8"})

        if url.path not in {
            "/api/v1/airports",
            "/api/v1/cities",
            "/api/v1/books",
            "/api/v1/movies",
            "/api/v1/incidents",
            "/api/v1/offshore-oil-fields",
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
            elif url.path == "/api/v1/offshore-oil-fields":
                field_name, page = parse_offshore_oil_fields_query(params)
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
        if url.path == "/api/v1/offshore-oil-fields":
            return Response.json(query_offshore_oil_fields(OFFSHORE_OIL_FIELDS, field_name, page))

        result_set = await get_cities_result_set(
            self.env.QUERY_CACHE,
            CITIES,
            country_code,
            int(self.env.CITIES_CACHE_TTL_SECONDS),
        )
        return Response.json(paginate_cities_result_set(result_set, page))
