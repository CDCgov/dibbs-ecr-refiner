"""
Asserts where a query result lands and how it travels to the client.

The rule, in full:

* every query -- an `async def` in an `app/db/**/db.py` -- returns a frozen `Db*`
  dataclass, a primitive, or a container of those; never a `core` or `api` model,
  and never a raw row
* a `Db*`'s fields hold primitives, other `Db*`, or frozen `core` types; JSONB is
  parsed into them in `db`, beside the SQL that chose its keys
* a route's body is a `*Response`; the types nested inside it are plain nouns, and
  no `Db*` reaches the generated schema at all

Rules 1-3 read the source with `ast`, like `test_layering.py`, so they see every
module whether or not anything imports it. Rule 4 reads the schema FastAPI actually
generates, because that -- not the Python names -- is what `orval` turns into client
types.
"""

import ast
from pathlib import Path

import pytest

from app.main import create_fastapi_app

REFINER_ROOT = Path(__file__).resolve().parents[2]
APP = REFINER_ROOT / "app"
DB = APP / "db"
CORE_MODELS = APP / "core" / "models"

# immutable values and the generic containers that wrap them. `dict`/`list` are
# allowed as containers -- `frozen` is shallow, and making `Db*` collections into
# tuples is deferred. `Any` is not: it is how a raw row would get past this guard
PRIMITIVES = {
    "None",
    "bool",
    "int",
    "float",
    "str",
    "bytes",
    "UUID",
    "datetime",
    "date",
    "Literal",
    "list",
    "dict",
    "tuple",
    "set",
    "AsyncIterator",
    "Iterator",
}


def _annotation_names(node: ast.expr | None) -> set[str]:
    if node is None:
        return {"<missing>"}
    names: set[str] = set()
    for n in ast.walk(node):
        match n:
            case ast.Name(id=name) | ast.Attribute(attr=name):
                names.add(name)
            case ast.Constant(value=None):
                names.add("None")
            case ast.Constant(value=str() as forward_ref):
                names |= _annotation_names(ast.parse(forward_ref, mode="eval").body)
    return names


def _is_frozen_dataclass(cls: ast.ClassDef) -> bool:
    return any(
        isinstance(d, ast.Call)
        and _annotation_names(d.func) == {"dataclass"}
        and any(
            k.arg == "frozen"
            and isinstance(k.value, ast.Constant)
            and k.value.value is True
            for k in d.keywords
        )
        for d in cls.decorator_list
    )


def _modules(root: Path) -> list[tuple[Path, ast.Module]]:
    return [
        (path, ast.parse(path.read_text()))
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    ]


def _db_classes() -> list[tuple[Path, ast.ClassDef]]:
    return [
        (path, node)
        for path, tree in _modules(DB)
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name.startswith("Db")
    ]


def _frozen_core_vocabulary() -> set[str]:
    # frozen `core` dataclasses, plus `core` type aliases -- the `Literal` spellings in
    # `core/models/configurations.py`, which are immutable by nature
    names: set[str] = set()
    for _, tree in _modules(CORE_MODELS):
        for node in ast.walk(tree):
            match node:
                case ast.ClassDef() if _is_frozen_dataclass(node):
                    names.add(node.name)
                case ast.TypeAlias(name=ast.Name(id=alias)):
                    names.add(alias)
    return names


def _where(path: Path, node: ast.AST) -> str:
    return f"{path.relative_to(REFINER_ROOT)}:{node.lineno}"


def _dicts_without_db_values(node: ast.expr | None) -> set[str]:
    # a `dict` is returned as a lookup keyed by id -- `dict[UUID, DbCodeSystem]`. one
    # whose values are not `Db*`, or a bare `dict`, is a row that skipped its dataclass
    if node is None:
        return set()
    found: set[str] = set()
    subscripted: set[int] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Subscript) and _annotation_names(n.value) == {"dict"}:
            subscripted.add(id(n.value))
            value = n.slice.elts[-1] if isinstance(n.slice, ast.Tuple) else n.slice
            if not any(name.startswith("Db") for name in _annotation_names(value)):
                found.add(ast.unparse(n))
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id == "dict" and id(n) not in subscripted:
            found.add("dict")
    return found


def test_queries_return_db_models_or_primitives():
    offenders = []
    for path, tree in _modules(DB):
        if path.name != "db.py":
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            bad = {
                n
                for n in _annotation_names(node.returns)
                if n not in PRIMITIVES and not n.startswith("Db")
            } | _dicts_without_db_values(node.returns)
            if bad:
                offenders.append(
                    f"{_where(path, node)} {node.name} returns {sorted(bad)}"
                )

    assert not offenders, (
        "a query must land its result in a frozen `Db*` (or return a primitive); map "
        "it to a `core` or `api` model where it is consumed:\n  "
        + "\n  ".join(offenders)
    )


def test_db_models_are_frozen():
    offenders = [
        f"{_where(path, cls)} {cls.name}"
        for path, cls in _db_classes()
        if not _is_frozen_dataclass(cls)
    ]

    assert not offenders, (
        "every `Db*` is a faithful record of a row and must be "
        "`@dataclass(frozen=True)`:\n  " + "\n  ".join(offenders)
    )


def test_db_model_fields_nest_only_db_or_frozen_core_types():
    allowed = PRIMITIVES | _frozen_core_vocabulary()
    offenders = []
    for path, cls in _db_classes():
        for stmt in cls.body:
            if not isinstance(stmt, ast.AnnAssign):
                continue
            bad = {
                n
                for n in _annotation_names(stmt.annotation)
                if n not in allowed and not n.startswith("Db")
            }
            if bad:
                field = ast.unparse(stmt.target)
                offenders.append(
                    f"{_where(path, stmt)} {cls.name}.{field}: {sorted(bad)}"
                )

    assert not offenders, (
        "a `Db*` field may hold primitives, other `Db*`, or frozen `core` types -- "
        "parse JSONB into one of those in `db`:\n  " + "\n  ".join(offenders)
    )


@pytest.fixture(scope="module")
def openapi() -> dict:
    return create_fastapi_app(lifespan=None).openapi()


def _ref_name(schema: dict) -> str | None:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if schema.get("type") == "array" and "$ref" in schema.get("items", {}):
        return schema["items"]["$ref"].rsplit("/", 1)[-1]
    return None


def test_route_bodies_are_responses(openapi):
    # only what the client is generated from: `orval.config.ts` excludes `internal`
    offenders = []
    for path, operations in openapi["paths"].items():
        for method, op in operations.items():
            if "internal" in op.get("tags", []):
                continue
            for status, response in op.get("responses", {}).items():
                if not status.startswith("2"):
                    continue
                schema = response.get("content", {}).get("application/json", {})
                name = _ref_name(schema.get("schema", {}))
                if name is not None and not name.endswith("Response"):
                    offenders.append(f"{method.upper()} {path} -> {name}")

    assert not offenders, (
        "the body a route returns is named `*Response` (for a list body, its "
        "element); types nested inside it are plain nouns:\n  " + "\n  ".join(offenders)
    )


def test_no_db_model_reaches_the_schema(openapi):
    leaked = sorted(n for n in openapi["components"]["schemas"] if n.startswith("Db"))

    assert not leaked, (
        f"`Db*` models are never generated to the client; map them at the route: {leaked}"
    )
