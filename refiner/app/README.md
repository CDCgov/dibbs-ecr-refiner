# Refiner application

The FastAPI web app, and the core refinement logic the AWS Lambda shares with it.
This file is the map: how the layers depend on each other, where a model lives, and
how data moves between them. Each layer's README covers what is specific to it.

## Layers

```
app/
├── core/       # shared vocabulary, config, exceptions -- depends on nothing above it
├── db/         # queries, and the frozen `Db*` models their rows land in
├── services/   # business logic, S3, and the refinement core (`services/ecr/`)
├── api/        # routes, auth, request validation, and every wire model
└── lambda/     # the S3-triggered batch entrypoint
```

The dependency direction is `core < db, services < api`. `db` and `services` share a
rank -- each may import the other -- but neither may import `api`, and `core` imports
none of them.

Two boundaries matter more than the rest:

- **the refinement core needs neither the database nor the API.**
  `services/ecr/`, `services/pipeline.py` and `services/file_io.py` refine documents
  they are handed. The Lambda image ships without `app/api` or `app/db` at all
- **the Lambda reads configuration from S3, never from Postgres.** Activation
  serializes a configuration to `active.json`; the Lambda deserializes it

`tests/unit/test_layering.py` enforces all of this by reading every import with
`ast`. The few existing upward imports are listed in `KNOWN_UPWARD_IMPORTS`, each
with its reason; a new one fails the test.

## Where a model lives

Ask **who builds it, and who reads it**.

| who builds it | who reads it | home |
| --- | --- | --- |
| a query | anything | `app/db`, as a frozen `Db*` -- always |
| `services`, from `Db*` rows | `services`, `api`, the Lambda | `app/core/models` |
| a route | that route only | the route module |
| a route | another module too | a sibling `model.py` |
| nobody in particular | every layer | `app/core/models` |

Two consequences that are easy to get backwards:

- **`core` is earned by having two layers that need the same shape**, not by being
  important. A shape only `api` uses lives in `api`, however central it feels
- **`services` may read a `Db*` directly.** A lookup -- the six-row `systems` table,
  say -- needs no copy of itself in `core`. A `core` model exists only where
  `services` *produces* something new

## How data moves

```
query ──→ frozen Db* ──┬── services builds something new ──→ core model
                       ├── route returns it as-is ─────────→ *Response, via a mapper
                       └── stays internal ─────────────────→ stays Db*
```

- **a query result is never mutated.** It lands in a `@dataclass(frozen=True)` `Db*`
  and every model past that point is built on purpose. `frozen` is shallow; `list`
  fields are still lists
- **a `Db*` nests only primitives, other `Db*`, or frozen `core` types.** JSONB is
  parsed into those in `db`, beside the SQL that chose its keys -- `db/tes/db.py`'s
  `_to_condition_diff` is the reference. Parsing is not transforming: it changes no
  meaning, only turns a `dict` into a shape mypy can check
- **the body a route returns is a `*Response`** (for a list body, its element). Types
  nested inside it are plain nouns, and may be frozen `core` types
- **a mapper is `_to_<model it builds>(row: Db*) -> Model`** -- pure, sync, beside
  the model it builds. Never `..._from_db`: anything ending in `_db` is a query
- **mapping stays in the route** until it needs its own unit test or a second route
  needs it. Then it moves to `services`

`tests/unit/test_db_models.py` enforces that every query returns a `Db*`, the first
three points above, and that no `Db*` ever appears in the generated OpenAPI schema.

### Pending: a client-side marker for API data

Whether the client marks every generated type as API data -- `ApiAuditEvent`, say --
is a decision for the front-end engineers. `orval` supports it in one line
(`override.components.schemas.prefix` in `client/orval.config.ts`), independently of
the Python names, so nothing here needs to change for it.

## The refinement pipeline

`services/pipeline.py` owns the parse/serialize boundary; `services/ecr/` does the
refining and provenance stamping. Both the web app and the Lambda call it.
`services/ecr/README.md` has the full design.

## API documentation

Served at `/docs` (Swagger UI) and `/redoc`. In the local environment the app also
writes `refiner/openapi.json` on startup, which `orval` turns into the client's
TanStack Query hooks and types under `client/src/api/` -- generated, never
hand-edited.
