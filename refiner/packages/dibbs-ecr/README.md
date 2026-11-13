# dibbs-ecr

`dibbs-ecr` is a shared Python library for electronic case reporting (eCR)
specification knowledge, intended for use by the DIBBs eCR Refiner and Difference
in Docs (DiD). It lets consumers share document definitions and XML behavior while
keeping their own processing policy.

The package currently contains a skeleton. Planned modules are `cda/` for CDA
namespaces and XML helpers, `vocab/` for code-system OIDs and vocabulary, `eicr/`
for section catalogs and version detection, `rr/` for Reportability Response
parsing, and `augment/` for shared Data Augmentation IG writing.

## Install

Requires Python 3.14 or newer. `lxml` is the only runtime dependency and is installed
automatically; test and tooling dependencies are separate.

From the repository root:

```sh
python -m pip install ./refiner/packages/dibbs-ecr
```

For local development, use an editable installation so source changes are available
without reinstalling:

```sh
python -m pip install -e ./refiner/packages/dibbs-ecr
```

## Import

```python
import dibbs_ecr
```

## Tests and checks

In a Python 3.14+ virtual environment, install the development tools and package
from the package directory:

```sh
cd refiner/packages/dibbs-ecr
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r dev-requirements.txt -e .
```

Then run the tests and checks:

```sh
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy --config-file pyproject.toml
```

With the tools and package installed in `refiner/.venv`, the equivalent commands
from the repository root are `just server test-dibbs-ecr`,
`just server lint-dibbs-ecr`, and `just server check-dibbs-ecr`.

## Dependency boundary

Code in `dibbs_ecr` must not import anything from elsewhere in the Refiner
codebase, including `app` modules. This applies to imports inside functions and
`TYPE_CHECKING` blocks as well. The package must work independently of the Refiner
application.

Consumers may import `dibbs_ecr`. Product-specific match rules, pruning,
precedence, processing state, tool identity, and ID-generation policy belong in
the consuming applications.
