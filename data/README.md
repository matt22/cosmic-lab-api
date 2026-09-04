# Movies dataset

`movies.json` is a flat, read-only practice dataset containing 1,000 real
movies released from 1990 through 2026. Every year in that inclusive range is
represented.

## Schema

Each object has exactly seven scalar fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | integer | Stable dataset ID from 1 through 1,000 |
| `title` | string | IMDb primary title |
| `year` | integer | IMDb start year |
| `runtimeMinutes` | integer | IMDb runtime in minutes |
| `mpaaRating` | string | US MPA classification: `G`, `PG`, `PG-13`, `R`, or `NC-17` |
| `scoreRating` | number | IMDb weighted-average user score on a 1–10 scale |
| `directorLastName` | string | Director's family name from Wikidata |

## Sources and snapshot

Generated on 2026-09-04 from:

- [IMDb non-commercial datasets](https://developer.imdb.com/non-commercial-datasets/):
  `title.basics.tsv.gz` and `title.ratings.tsv.gz`
- [Wikidata Query Service](https://query.wikidata.org/): film identity, US MPA
  classification, director identity, and director family name

IMDb data is refreshed daily, and `scoreRating` represents the value in the
downloaded snapshot rather than a permanently fixed score. IMDb's
non-commercial dataset terms apply to the IMDb-derived fields. Wikidata
structured data is available under CC0.

## Selection rules

Records must have all seven fields, exactly one director, one explicit family
name, one recognized US MPA classification, and no duplicate title/year pair.
`Not Rated`, missing values, co-directed films, and ambiguous source records are
excluded.

To produce a useful, recognizable practice set, the generator selects the
highest-vote eligible film from each year first, then fills the remaining slots
with the highest-vote eligible films overall. Final records are ordered by year
and title before sequential IDs are assigned.

## Rebuilding

The Wikidata export query is saved as `scripts/movies.sparql`. The deterministic
builder is `scripts/build_movies.py`; it accepts the query's JSON export plus
the two compressed IMDb TSV files:

```bash
python3 scripts/build_movies.py \
  --wikidata /path/to/wikidata-movies.json \
  --imdb-basics /path/to/title.basics.tsv.gz \
  --imdb-ratings /path/to/title.ratings.tsv.gz
```

Rebuilding from newer source snapshots can change scores, selected films, and
IDs. Review such changes before committing them.
