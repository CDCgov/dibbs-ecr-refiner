# eCR Refiner Documentation Site

A local-first documentation site built with 11ty (Eleventy) that auto-generates
API reference pages from Python docstrings. It runs entirely on the developer's
machine with no external hosting.

## Quick Start

### Local Installation

```bash
just docs::install
just docs::build
just docs::serve
```

The preview server runs on port `9091`.

### Docker Alternative

For reviewers or those without a local Node/Python environment, the site can be
run via Docker (used by the design-review script):

```bash
docker build -t ecr-docs -f Dockerfile.docs .
docker run -p 9091:9091 ecr-docs
```

## What's Included

- **Home**: Main entry point to the documentation.
- **Onboarding**: Renders the project root `README.md` with GitHub-style
  admonitions.
- **Decisions**: A list of Architecture Decision Records (ADRs) with status
  badges (Accepted, Proposed, etc.).
- **Python API Reference**: Domain-organized module documentation featuring
  function signatures, parameters, and docstrings.
- **Lambda Reference**:
  - **Pipeline Diagram**: End-to-end processing flow.
  - **Function Reference**: Lambda functions grouped by pipeline Stage with Role
    badges.
  - **Processing Scenarios**: Integration test scenarios documenting real-world
    execution paths.
  - **Glossary**: Domain terminology used throughout the Lambda functions.

## How Extraction Works

The site uses a set of Python scripts in `.justscripts/py/docs/` to bridge
source code and documentation:

- `extract_python.py`: Uses `griffe` and `docstring-parser` to extract module
  and function metadata.
- `extract_lambda.py`: Specifically extracts `Stage` and `Role` metadata from
  Lambda function docstrings.
- `validate_lambda_docs.py`: Enforces that every production Lambda docstring
  contains `Stage` and `Role` annotations and cross-references terms against
  `docs/_data/glossary.toml`.
- `watch.py`: Monitors Python source files and triggers re-extraction
  automatically during `just docs::serve`.

**Data Flow**: Extraction scripts output JSON to `docs/_data/python-api.json`
and `docs/_data/lambda-api.json`. These files are checked into git but marked as
`-diff` in `.gitattributes` because they are generated artifacts.

## Just Recipes Reference

All documentation commands are prefixed with `docs::`.

| Recipe                      | Purpose                                                      |
| :-------------------------- | :----------------------------------------------------------- |
| `just docs::install`        | Install documentation site dependencies (11ty)               |
| `just docs::install-python` | Install Python deps for docs extraction/validation           |
| `just docs::sync`           | Extract Python API docs using griffe                         |
| `just docs::validate`       | Validate docs sync without writing files (CI-friendly)       |
| `just docs::build`          | Build the documentation site                                 |
| `just docs::serve`          | Launch local docs preview server on port 9091 with auto-sync |
| `just docs::debug-sync`     | Debug manual sync issues with detailed diagnostics           |

## Docstring Conventions for Authors

### Lambda Metadata

All functions and classes in `refiner/app/lambda/` must include `Stage:` and
`Role:` annotations in their docstrings to appear in the Lambda Reference. See
`refiner/app/lambda/README.md` for the full list of valid stages and roles.

**Example:**

```python
def my_function():
    """
    Summary of function.

    Stage:
        S3 Retrieval
    Role:
        S3 I/O
    """
```

### Formatting

Docstrings are rendered as markdown in the API reference. Use markdown-safe
formatting:

- Use backticks to escape XML-like tags (e.g., `` `<code>` ``).
- Use standard markdown for bulleted and numbered lists.

## Directory Layout

```text
docs/
├── .eleventy.js       # 11ty configuration and custom filters
├── _data/             # Data sources (JSON/TOML) and data loaders
├── _includes/         # Shared templates and components
├── reference/          # API reference pages (Python and Lambda)
├── decisions/         # ADR markdown files and index
├── onboarding/        # Root README rendering page
├── css/               # Generated Tailwind CSS
└── package.json       # Node dependencies and build scripts
```

## CI Status Note

The `.github/workflows/docs-validation.yml` workflow currently validates that
docstrings are present and correctly formatted (via `just docs::validate`).
There is currently no full site build step in CI.
