# AGENTS.md

## Scope

Python API intended for deployment to Cloudflare Workers.

## Initial read set

Read only `README.md`, `pyproject.toml`, and the file named by the task. Do not recursively inspect `.venv*`, `python_modules/`, `data/`, or `scripts/` unless the task explicitly requires one of them.

## Commands

- Use the project’s documented test or deployment command from `README.md`.
- Run the narrowest relevant check after each bounded change.

## Work protocol

State the exact files to inspect before editing. Prefer focused changes. Do not regenerate datasets, modify dependency lockfiles, or change deployment configuration unless requested.
