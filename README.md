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

Repository and deployment plumbing are connected. The first practice dataset
has been added, but the API itself has not been implemented yet.

- The repository contains validated, flat datasets of 1,000 movies covering
  1990 through 2026 and 1,000 real cities in `data/`.
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
│   └── ...               # Additional practice datasets
├── test/                 # Endpoint and filtering tests
├── package.json
└── wrangler.jsonc        # Cloudflare Worker configuration
```

Example endpoints may eventually look like:

```text
GET /api/movies
GET /api/movies?genre=comedy
GET /api/movies?year=2020&rating_gte=7
GET /api/movies?sort=rating&order=desc&limit=10
```

The data model, supported operators, response envelope, errors, pagination,
and practice exercises are intentionally undecided.

## Suggested next-session checklist

1. Inspect the response currently served by the public endpoint so its useful
   behavior is not accidentally lost.
2. Decide whether to preserve that generated implementation or replace it.
3. Scaffold a minimal Cloudflare Worker with `wrangler.jsonc` and local scripts.
4. Run it locally with Wrangler and add a basic automated health check.
5. Deploy a minimal version through GitHub and verify that the public endpoint
   still works.
6. Only then design datasets, filtering syntax, exercises, and expected results.

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
