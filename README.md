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
datasets are complete. The API itself has not been implemented yet.

- The repository contains five validated, flat practice datasets in `data/`:
  movies, cities, US airports, books, and fictional service incidents.
- Cloudflare Worker `api` is connected to `matt22/cosmic-lab-api`.
- Cloudflare watches the `main` branch and uses `npx wrangler deploy` as its
  deploy command.
- The existing endpoint was initially created through Cloudflare and remains
  live from that manual deployment.
- There is not yet a `wrangler.jsonc`, Worker entry point, package manifest,
  API contract, or test suite in this repository.

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
GET /api/airports?stateCode=CA
GET /api/books?publicationDate_gte=2000-01-01&pages_lte=400
GET /api/incidents?endTime=null
GET /api/movies?sort=scoreRating&order=desc&limit=10
```

The stored data models are now defined. Supported query operators, response
envelope, errors, pagination, and practice exercises remain undecided.

## Suggested next-session checklist

1. Inspect the response currently served by the public endpoint so its useful
   behavior is not accidentally lost.
2. Decide whether to preserve that generated implementation or replace it.
3. Scaffold a minimal Cloudflare Worker with `wrangler.jsonc` and local scripts.
4. Run it locally with Wrangler and add a basic automated health check.
5. Deploy a minimal version through GitHub and verify that the public endpoint
   still works.
6. Define filtering, sorting, null handling, pagination, response envelopes,
   errors, and expected exercise results against the existing datasets.

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
