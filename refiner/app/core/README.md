# Core layer

Shared vocabulary, configuration and exceptions. `core` sits at the bottom of the
dependency order, so anything here is importable from every layer -- including the
refinement core and the Lambda, which never touch the database.

## What earns a place here

**A shape two layers both need.** In practice that is one of:

- **built by `services`** and read by `api` or the Lambda -- `Coding`, built where a
  configuration's codes are merged and serialized to `active.json`
- **read by every layer** -- the `Literal` spellings of what we persist, like
  `ConfigurationStatus`
- **a boundary of its own** -- the `*Payload`/`*Metadata` shapes that cross to the
  Lambda through S3

Being important is not enough. A shape only `api` uses belongs in `api`; a row only a
query produces is a `Db*` in `db`. The full table is in
[`app/README.md`](../README.md#where-a-model-lives).

`core` models are **frozen dataclasses**, which is what lets other layers hold them
safely: a `Db*` may nest one, and a `*Response` may carry one to the browser.

## Structure

```
core/
├── app/
│   ├── base.py              # `BaseService`, the DIBBs FastAPI wrapper, and its health route
│   └── openapi.py           # custom OpenAPI generation
├── models/
│   ├── api.py               # the base service's health response, OpenAPI examples
│   ├── configurations.py    # persisted `Literal`s, `ConfiguredSection`
│   ├── labels.py            # user-visible labels for section and narrative actions
│   ├── limits.py            # upload size limits, typed so `orval` ships them to the client
│   ├── payloads.py          # what crosses to the Lambda via S3
│   ├── terminology.py       # `CodeLabel`, `Coding`, `CodeExportRow`
│   └── types.py             # `FileUpload`, `XMLFiles`
├── config.py                # environment-driven config objects
└── exceptions.py            # the exception hierarchy
```

> [!NOTE]
> `config.py`'s `DbConfig` is the database **connection** config, not a query row.
> It shares the `Db` prefix by coincidence, and lives outside `app/db`, which is the
> only place `tests/unit/test_db_models.py` looks.

## Imports

`core` imports nothing from `db`, `services` or `api`. The two exceptions today are
listed with their reasons in `KNOWN_UPWARD_IMPORTS` in `tests/unit/test_layering.py`:
`models/api.py` reads its examples through `services/assets.py`, and `XMLFiles` needs
a parser from `services/file_io.py` at call time.
