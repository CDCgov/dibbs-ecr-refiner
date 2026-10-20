# API layer

Routes, authentication, request validation, and **every model the browser sees**.
How a model gets here from a query is in
[`app/README.md`](../README.md#how-data-moves).

## Structure

```
api/
├── auth/                  # OIDC login, session middleware, `get_logged_in_user`
├── validation/            # upload and XML validation shared by routes
└── v1/
    ├── v1_router.py       # mounts every v1 router behind `get_logged_in_user`
    ├── configurations/    # router.py + one module per concern, model.py shared
    ├── simulator/         # router.py + model.py -- the independent testing flow
    └── *.py               # one module per remaining resource
```

## Where a wire model is defined

- **used by one route module only** -- define it in that module, beside the route
- **imported by another module** -- move it to a sibling `model.py`. A route module
  imports the database layer, so importing a model *from* one is how
  `simulator/model.py` came to exist: the shared model sat in a route module and
  produced an import cycle
- **also built by `services`** -- it is a `core` model, not an `api` one; see the
  placement table in `app/README.md`

## Naming

- **the body a route returns is `*Response`.** For a list body, the element is the
  body -- `/code-systems` returns `list[CodeSystemResponse]`
- **types nested inside a body are plain nouns** -- `AuditEvent` inside
  `EventsResponse`. They may be frozen `core` types, like `CodeLabel` inside
  `GetConfigurationResponse`
- **request bodies are `*Input`**

`tests/unit/test_db_models.py` checks the `*Response` rule against the generated
schema, skipping `internal`-tagged routes the same way `client/orval.config.ts` does.

## Mapping from the database

A handler may read a `Db*` freely -- that is where the mapping happens. It may never
**return** one, and no `Db*` may appear in a response model; the guard test checks
the generated schema for that too.

```python
def _to_tes_update(row: DbTes) -> TesUpdate:
    return TesUpdate(id=row.id, version=row.version, created_at=row.created_at)
```

- name it `_to_<model it builds>`; keep it private unless another module needs it,
  as `to_configuration_version` in `configurations/model.py` does
- write the fields out. `Model(**asdict(row))` compiles, but mypy can no longer see
  a renamed field
- simple unpacking -- a sort, a filter -- stays in the route. Move it to `services`
  when it needs its own unit test or a second route needs it

## The client is generated from here

In the local environment the app writes `refiner/openapi.json` on startup, and `orval`
generates the client's hooks and types into `client/src/api/` from it. Renaming a
wire model therefore renames a client type: run `npx tsc -b --noEmit`, `eslint` and
`vitest` in `client/` afterwards. Never hand-edit `client/src/api/`.
