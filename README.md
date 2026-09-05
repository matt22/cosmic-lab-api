# Cosmic Lab API

A small JSON API for practicing HTTP requests, URL parameters, filtering,
sorting, pagination, and API-consumer exercises. The source of truth lives in
GitHub and the public API will run on Cloudflare Workers.

## Project links

- Public endpoint: <https://api.cosmic-lab.workers.dev>
- GitHub repository: <https://github.com/matt22/cosmic-lab-api>
- Repository visibility: private
- Production branch: `main`

## Current status

Repository and deployment plumbing are connected, and the initial practice
datasets are complete. The first API endpoint is implemented for airports.

- The repository contains five validated, flat practice datasets in `data/`:
  movies, cities, US airports, books, and fictional service incidents.
- Cloudflare Worker `api` is connected to `matt22/cosmic-lab-api`.
- Cloudflare KV namespace `cosmic-lab-api-query-cache` is configured as the
  `QUERY_CACHE` Worker binding in `wrangler.jsonc`.
- Cloudflare watches the `main` branch. Its existing `npx wrangler deploy`
  command must be changed to `uv run pywrangler deploy` before deploying this
  Python Worker.
- `GET /api/v1/airports` supports state-code filtering and fixed three-record
  page-based pagination.
- The Python Worker is deployed at <https://api.cosmic-lab.workers.dev> and the
  versioned airports endpoint has been verified in production.
- The Python Worker entry point, package manifest, and initial tests are tracked
  on the production branch.

Do not assume the code currently running at the endpoint exists in this Git
repository. Before relying on Git-based deployment, add and test the minimal
Worker project files locally.

## Available datasets

All datasets are checked-in JSON arrays. Records are intentionally flat: fields
contain strings, numbers, or documented null values rather than nested objects
or arrays. Dataset-specific provenance, selection rules, and rebuilding notes
live in [`data/README.md`](data/README.md).

| File | Records | Fields |
| --- | ---: | --- |
| `movies.json` | 1,000 | `id`, `title`, `year`, `runtimeMinutes`, `mpaaRating`, `scoreRating`, `directorLastName` |
| `cities.json` | 1,000 | `id`, `cityName`, `countryCode`, `countryName`, `continent`, `latitude`, `longitude` |
| `airports.json` | 100 | `id`, `airportName`, `iataCode`, `icaoCode`, `city`, `stateCode`, `stateName`, `countryCode`, `countryName`, `latitude`, `longitude` |
| `books.json` | 1,000 | `id`, `title`, `author`, `isbn13`, `publicationDate`, `pages` |
| `incidents.json` | 100 | `id`, `serviceName`, `severity`, `status`, `startTime`, `endTime` |

The movie, city, airport, and book datasets contain sourced real-world data.
Incidents are fictional and deterministic. Their null timestamps carry meaning:

- A planned incident has a null `startTime` and a future `endTime` target.
- An active incident has a populated `startTime` and a null `endTime`.
- A resolved incident has both timestamps, with the end after the start.
- Both incident timestamps are never null.

Validation and deterministic build scripts are kept in `scripts/`. Generated
JSON is committed so the Worker can eventually bundle and serve it without a
database or a build-time network dependency.

## Intended architecture

The likely first version will keep small, read-only JSON datasets in the
repository and bundle them with a Cloudflare Worker:

```text
cosmic-lab-api/
├── src/
│   └── index.js          # Request routing and query processing
├── data/
│   ├── movies.json
│   ├── cities.json
│   ├── airports.json
│   ├── books.json
│   ├── incidents.json
│   └── ...               # Additional practice datasets
├── test/                 # Endpoint and filtering tests
├── package.json
└── wrangler.jsonc        # Cloudflare Worker configuration
```

Example endpoints may eventually look like:

```text
GET /api/movies
GET /api/movies?year=2020&scoreRating_gte=7
GET /api/cities?countryCode=JP&sort=cityName
GET /api/v1/airports?state_code=CA
GET /api/books?publicationDate_gte=2000-01-01&pages_lte=400
GET /api/incidents?endTime=null
GET /api/movies?sort=scoreRating&order=desc&limit=10
```

The stored data models are now defined. The airports endpoint establishes the
first response envelope and pagination behavior; broader query operators and
practice exercises remain undecided.

## Airports endpoint

The initial endpoint requires a two-letter `state_code`. It accepts an optional
positive `page`, which defaults to `1`. The airports page size is fixed at
three; other datasets can define their own pagination rules.

```text
GET /api/v1/airports?state_code=CA
GET /api/v1/airports?state_code=CA&page=2
```

Airport records contain every source field except `latitude` and `longitude`.
Those two values are returned as a comma-delimited `coordinates` string:

```json
{
  "coordinates": "33.9425,-118.408"
}
```

Responses place pagination metadata before the result array:

```json
{
  "pagination": {
    "page": 1,
    "page_size": 3,
    "count": 3,
    "total": 12
  },
  "data": []
}
```

Run the unit tests with:

```bash
python3 -m unittest discover -s tests -v
```

Run the Cloudflare Python Worker locally with:

```bash
uv run pywrangler dev
```

## Suggested next-session checklist

1. Inspect the response currently served by the public endpoint so its useful
   behavior is not accidentally lost.
2. Decide whether to preserve that generated implementation or replace it.
3. Change the Cloudflare build command to `uv run pywrangler deploy` and ensure
   the build environment provides `uv`.
4. Verify that a GitHub-based deployment preserves the public endpoint after
   the Cloudflare build command is updated.
5. Define filtering, sorting, null handling, pagination, response envelopes,
   errors, and expected exercise results for the remaining datasets.

## Local repository workflow

```bash
git pull
# make and test changes
git add <files>
git commit -m "Describe the change"
git push
```

Pushing to `main` starts a Cloudflare build, so implementation changes should
be locally tested before pushing.

## Security notes

- Never commit API tokens, passwords, `.env`, `.dev.vars`, or credential-bearing
  repository URLs.
- `.env`, `.dev.vars`, `.wrangler/`, `node_modules/`, and `.DS_Store` are ignored.
- Cloudflare's GitHub App was granted access only to this repository.
- A credential embedded in an earlier Cloudflare artifact clone URL was exposed
  during initial setup. Confirm that credential has been revoked or expired;
  never reuse it or copy it into this repository.
- Git remotes should remain credential-free. The expected remote is:
  `https://github.com/matt22/cosmic-lab-api.git`.
