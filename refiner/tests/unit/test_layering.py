"""
Asserts the dependency direction ADR 0016 calls for: `core < db, services < api`.

This is the import-graph test open question 4 of the ADR asks for. It needs no new
dependency -- it reads the source with `ast` rather than importing anything, so it
cannot be fooled by a module that happens to be loaded already, and it sees
function-local imports, which are still dependencies even when they are deferred to
call time to break a cycle.

`KNOWN_UPWARD_IMPORTS` is a baseline, not a blessing. Every entry is an E1 item. The
test fails on any import not listed there, so today's boundaries cannot erode
silently, and E1 becomes "drive this dict to empty" rather than an archaeology
exercise.
"""

import ast
from pathlib import Path

import pytest

REFINER_ROOT = Path(__file__).resolve().parents[2]
APP = REFINER_ROOT / "app"

# the total order from ADR 0016 option E1. `db` and `services` share a rank: each may
# import the other, and `services/configurations.py` legitimately does. what neither
# may do is import `api`
LAYER_RANK = {
    "core": 0,
    "db": 1,
    "services": 1,
    "api": 2,
    "lambda": 3,
}

# every one of these is an E1 item. the reason is recorded so that a reader can tell a
# deliberate deferral from a fresh mistake
KNOWN_UPWARD_IMPORTS: dict[tuple[str, str], str] = {
    (
        "app.db.configurations.codes.db",
        "app.api.v1.configurations.codes.model",
    ): "E1: db function takes the `FilterInput` request model as a parameter",
    (
        "app.db.configurations.custom_codes.db",
        "app.api.v1.configurations.custom_codes.model",
    ): "E1: db function takes the `AddCustomCodeInput` request model as a parameter",
    (
        "app.db.configurations.db",
        "app.api.v1.configurations.model",
    ): "E1: db functions take the `AddSectionInput`/`DeleteSectionInput` request models",
    (
        "app.core.models.api",
        "app.services.assets",
    ): "E1: plain inversion -- a core model reaching into a service",
    (
        "app.core.models.types",
        "app.services.file_io",
    ): "structural: `XMLFiles` holds documents and needs a parser, so `parse_eicr`/`parse_rr` import it at call time to break the cycle -- see the NOTE on the class",
    (
        "app.services.conditions.refinement",
        "app.api.validation.file_validation",
    ): "E1: reaches up for `format_xml_document_for_display_or_raise`",
}

# the refinement core ships to Lambda without `app/api`, and must not need the database
# at all -- it refines documents handed to it. this is the invariant the `Db*` work in
# ADR 0016 step 1 bought, and the one most worth keeping
STANDALONE_CORE = (
    "app.services.ecr.refine",
    "app.services.ecr.augment",
    "app.services.pipeline",
    "app.services.file_io",
)


def _layer(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) > 1 and parts[0] == "app" and parts[1] in LAYER_RANK:
        return parts[1]
    return None


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(REFINER_ROOT).with_suffix("").parts)


def _import_targets(path: Path, tree: ast.Module) -> set[str]:
    """
    Every dotted name an import statement could load, before resolving to files.

    `from x import y` names `x` and, when `y` is a submodule rather than an attribute,
    `x.y` -- both are returned, and `_resolve` keeps whichever exists as a file.
    """

    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0:
                module = node.module or ""
            else:
                # resolve `from ..x import y` against this file's package
                base = path.parent
                for _ in range(node.level - 1):
                    base = base.parent
                prefix = _module_name(base / "__init__.py").removesuffix(".__init__")
                module = f"{prefix}.{node.module}" if node.module else prefix
            targets.add(module)
            targets.update(f"{module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
    return targets


def _resolve(name: str, modules: set[str]) -> str | None:
    # the graph is keyed by file, so a package is its `__init__`
    if name in modules:
        return name
    if (package := f"{name}.__init__") in modules:
        return package
    return None


def _build_graph() -> dict[str, set[str]]:
    paths = [
        path
        for path in sorted(APP.rglob("*.py"))
        if "__pycache__" not in path.parts and ".venv" not in path.parts
    ]
    modules = {_module_name(path) for path in paths}

    graph: dict[str, set[str]] = {module: set() for module in modules}
    for path in paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        for target in _import_targets(path, tree):
            if not target.startswith("app"):
                continue
            # a name with no file of its own is an attribute (`from x import func`)
            # or a namespace package; neither runs any code
            if resolved := _resolve(target, modules):
                graph[_module_name(path)].add(resolved)
    return graph


def _parent_packages(module: str) -> list[str]:
    parts = module.removesuffix(".__init__").split(".")
    return [".".join(parts[:i]) + ".__init__" for i in range(1, len(parts))]


def _reachable(graph: dict[str, set[str]], start: str) -> set[str]:
    """
    Every module importing `start` executes, as file-keyed graph nodes.

    Importing `a.b.c` runs `a/__init__.py` and `a/b/__init__.py` first, so those
    count as reached too -- an import planted in a package's `__init__` ships
    with everything below it.
    """

    seen: set[str] = set()
    stack = [start]
    while stack:
        module = stack.pop()
        for target in graph.get(module, set()) | set(_parent_packages(module)):
            if target not in seen and target in graph:
                seen.add(target)
                stack.append(target)
    return seen


@pytest.fixture(scope="module")
def graph() -> dict[str, set[str]]:
    return _build_graph()


def test_no_unapproved_upward_imports(graph):
    found: dict[tuple[str, str], str] = {}
    for source, targets in graph.items():
        source_layer = _layer(source)
        if source_layer is None:
            continue
        for target in targets:
            target_layer = _layer(target)
            if target_layer is None:
                continue
            if LAYER_RANK[target_layer] > LAYER_RANK[source_layer]:
                found[(source, target)] = f"app/{source_layer}/ -> app/{target_layer}/"

    new = sorted(set(found) - set(KNOWN_UPWARD_IMPORTS))
    assert not new, (
        "new upward import(s) -- ADR 0016 orders core < db/services < api:\n"
        + "\n".join(
            f"  {src}\n    imports {dst}  ({found[(src, dst)]})" for src, dst in new
        )
    )


def test_known_upward_imports_are_still_real(graph):
    """
    The baseline shrinks as E1 lands; a stale entry should be deleted, not left to rot.
    """

    stale = sorted(
        pair
        for pair in KNOWN_UPWARD_IMPORTS
        if pair[1] not in graph.get(pair[0], set())
    )
    assert not stale, (
        "KNOWN_UPWARD_IMPORTS lists import(s) that no longer exist -- delete them:\n"
        + "\n".join(f"  {src} -> {dst}" for src, dst in stale)
    )


@pytest.mark.parametrize("entry", STANDALONE_CORE)
def test_refinement_core_needs_neither_db_nor_api(graph, entry):
    reached = _reachable(graph, entry)
    leaks = sorted(
        m
        for m in reached
        if m.startswith(("app.db.", "app.api.")) or m in {"app.db", "app.api"}
    )
    assert not leaks, (
        f"{entry} transitively imports the database or api layer.\n"
        "the refinement core runs in the Lambda, which ships neither `app/api` nor a\n"
        "database connection, so this breaks the deploy boundary:\n"
        + "\n".join(f"  {m}" for m in leaks)
    )


@pytest.mark.parametrize("layer", ["app.api", "app.db"])
def test_lambda_entrypoint_ships_neither_api_nor_db(graph, layer):
    """
    `Dockerfile.lambda` copies `app/core` and `app/services` only.

    `app/db` was in that image until the S3 payload shapes moved to
    `core/models/payloads.py` -- it was never there because the Lambda touches a
    database, which it cannot: there is no connection in the Lambda's environment.
    It was there because `*Payload`/`*Metadata`, the one ADR 0016 rule 3 family with
    no home of its own, had been filed under `app/db` by default.

    An import of either layer only fails once deployed, so assert it here instead.
    """

    reached = _reachable(graph, "app.lambda.lambda_function")
    leaks = sorted(m for m in reached if m.startswith(f"{layer}."))
    assert not leaks, (
        f"the Lambda cannot import `{layer.replace('.', '/')}` -- "
        f"`Dockerfile.lambda` does not copy it:\n" + "\n".join(f"  {m}" for m in leaks)
    )
