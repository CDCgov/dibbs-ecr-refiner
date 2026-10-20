# Database layer

## What belongs here

**Queries, and the frozen `Db*` models their rows land in.** Nothing else.

A function here runs a query and returns a faithful record of what it selected. It
does not combine sources, apply business rules, or shape anything for the browser --
that is `services/` and `api/`. Where a row goes next, and what it becomes on the way,
is in [`app/README.md`](../README.md#how-data-moves).

## The rule

- **every `*_db` function returns a `Db*`, a primitive, or a container of those.**
  Never a `core` or `api` model; the consumer maps it
- **every `Db*` is `@dataclass(frozen=True)`.** Nothing downstream mutates a query
  result
- **a `Db*` nests only primitives, other `Db*`, or frozen `core` types.** When a
  query aggregates into JSONB, parse it here, beside the SQL that chose the keys --
  `_to_condition_diff` in `tes/db.py` is the reference. If `services` did the parsing,
  it would have to know another layer's SQL aliases, and a renamed alias would break
  at runtime where mypy cannot see it

`tests/unit/test_db_models.py` enforces all three.

## Naming

- a query function ends in `_db` (ADR 0016 rule 6). Private helpers within a module
  are exempt
- a model is `Db*`, named for what the row **is** -- `DbLabeledCode`, not
  `DbCodeExportRow`. The query should not know which consumer reads it
- `pool.py`'s `create_db` and `get_db` end in `_db` without being queries. The guard
  test names them as its only exceptions, so "ends in `_db`" means "is a query"
  everywhere else

## Structure

One package per domain: `db.py` for the queries, and `model.py` when the models are
shared beyond it.

```
db/
├── pool.py                  # async psycopg pool; `create_db`, `get_db`
├── codes/
├── code_systems/
├── conditions/
├── configurations/          # + activations/, codes/, custom_codes/
├── events/
├── jurisdictions/
├── schema_migrations/
├── tes/
└── users/
```

## Grain

`conditions_codes_temp` is keyed `(condition_id, code_id, valueset_id)`, so **a row is
a membership, not a code**. Every aggregate over it must deduplicate:
`JSONB_AGG(DISTINCT JSONB_BUILD_OBJECT(...))` -- and it must be `JSONB_`, because
`json` has no equality operator and `DISTINCT` silently cannot apply to it.

`configurations/codes/db.py` is the reference implementation.
`tests/unit/test_sql_grain.py` fails on a new aggregate that forgets either half, and
`tests/integration/test_condition_code_grain.py` checks the counts against real data.
