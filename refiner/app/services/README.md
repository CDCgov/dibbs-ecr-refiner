# Services layer

Business logic: everything that combines sources, applies a rule, or builds something
no single query returns. It also holds the refinement core, which is deliberately
independent of everything else here.

## Working with the database

- **read a `Db*` directly when you only need to look something up.** Matching a custom
  code's `system_id` to an OID reads `DbCodeSystem` as-is; no copy is needed
- **build a `core` model when you produce something new.** `convert_config_to_storage_payload`
  merges a configuration's query codes with its custom codes into one `list[Coding]`
  -- a shape neither source has on its own, and the one `active.json` is built from
- **never mutate a row.** Every `Db*` is frozen; construct the next model instead

The rest of the rule -- where models live and how they reach the browser -- is in
[`app/README.md`](../README.md).

## The refinement core

`ecr/`, `pipeline.py` and `file_io.py` refine documents they are handed. They import
nothing from `app/db` or `app/api`, which is what lets the Lambda image ship without
either -- `tests/unit/test_layering.py` asserts it. The core reads its configuration
from `terminology.py`'s `ProcessedConfiguration`, deserialized from `active.json`, and
never from Postgres.

`ecr/README.md` has the full design.

## Structure

```
services/
├── ecr/                     # refinement + augmentation; see ecr/README.md
├── pipeline.py              # parse -> refine -> augment -> serialize, for both runtimes
├── file_io.py               # ZIP and XML reading
├── terminology.py           # `ProcessedConfiguration`, `CodeSystemSets` -- active.json, read side
├── configurations.py        # active.json, write side; default and cloned sections
├── conditions/              # activation, grouper statuses, naming, refinement helpers
├── testing.py               # the simulator and inline testing flows
├── tes.py                   # TES version lookups and the diff CSV
├── code_systems.py          # code-system lookups over `DbCodeSystem`
├── configuration_locks.py   # edit locks on a configuration
├── aws/                     # S3 reads, writes and key layout
├── database/timing.py       # slow-query logging decorator
├── xslt.py                  # renders refined eICRs to HTML
└── assets.py, file_exports.py, format.py, logger.py, sample_file.py
```

## Appendix

> [!NOTE]
> `lxml` XML element types in this codebase
>
> When working with XML in Python using `lxml`, you will see both `_Element` and
> `etree.Element` in our code.

- **Type hints:** We use `_Element` (from `lxml.etree`) for type annotations, because
  it is the actual type of XML element objects. This is important for static analysis
  and tools.
- **Element construction:** We use `etree.Element(...)` in the code to create
  elements. This is a factory function that returns an `_Element` instance.

**Why?**

- `etree.Element` is _not_ a class, but a function. Using it as a type hint is
  incorrect and may confuse type checkers.
- `_Element` is the correct type for variables that hold XML elements.

See also: [lxml _Element API docs](https://lxml.de/api/lxml.etree._Element-class.html)

This pattern will change in `lxml` 6.0; check the
[PR](https://github.com/lxml/lxml/pull/405) for more information.
