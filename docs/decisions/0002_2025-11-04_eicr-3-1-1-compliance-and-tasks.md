# 1. eICR 3.1.1 Compliance and Tasks

Date: 2025-11-04

## Status

Proposed

## Context and Problem Statement

HL7 has introduced Electronic Initial Case Report (eICR) version 3.1.1, and public health agencies are already receiving these documents. To remain compliant and extensible, the eCR Refiner must:

- Process new or updated section structures.
- Discover trigger code templates across an expanded set of CDA entry types.
- Validate output against the latest Schematron and requirements from HL7.

Key principles:

- **Strongly-typed configuration as code:** All configuration (supported documents, versions, sections, entries, and relationships) is represented as Python TypedDicts in `refiner_config.py`. The TypedDict module is source of truth for what is supported; there are no flat JSON config files in the repo.
- **Future extensibility:** This models document, section, and entry structure directly in Python. It lays groundwork for per-section/entry specialization in document handling and validation.

Validation and automation target HL7’s official Schematron and sample files published in [HL7/CDA-phcaserpt](https://github.com/HL7/CDA-phcaserpt), which explicitly references 3.1.1 in its README and assets. Subsequent incremental spec updates (e.g., v3.1.2) will be handled as Python code updates in the TypedDict config.

> [!NOTE]
> **HL7 Repository Versioning Note:**  
> The [HL7/CDA-phcaserpt](https://github.com/HL7/CDA-phcaserpt) repo is the canonical source for all eICR releases, including 3.1.1 and beyond, even when the repo or branch name does not change. All compliance, development, and validation are anchored to the assets, Schematron, and documentation present in this repository.

## Decision Drivers

- Regulatory compliance (must pass current HL7 Schematron for 3.1.1).
- Support for evolving HL7 standards with explicit, type-safe code.
- Safety handling of unknown/unsupported versions.
- Maintainability and governance via type-checked config and CI.
- Coverage and flexibility for current and future section/entry requirements.

## Considered Options

### Configuration Storage Format

| Option               | Pros                                             | Cons                                                  |
| -------------------- | ------------------------------------------------ | ----------------------------------------------------- |
| Flat JSON            | Portable, S3/Lambda-friendly, language-agnostic  | No type safety, no relationships, no comments         |
| YAML                 | Comments, more readable                          | Parsing overhead, less direct for Python, unnecessary |
| **Python TypedDict** | Maximizes type safety, docstrings, relationships | Python only, config changes are code reviews/PRs      |
| Pydantic Model       | Runtime validation, error reporting              | Extra overhead, slower, still Python-centric          |
| Database/API         | Dynamic updates, online editing                  | Overkill for static config                            |

**Chosen Approach:**  
All configuration is defined as Python TypedDicts in code (`refiner_config.py`). There are no JSON configuration files. Any new version, document, section, or entry is added as a Python code change, type-checked via mypy, and reviewed in PR. This TypedDict hierarchy encodes all relationships, supported document types/versions, and enables focused, documented updates as standards evolve.

## Implementation Details

### Configuration and Helper Refactor

- Completely remove legacy config (e.g. `refiner_config.json`, `refiner_details.json`) from the repository (except for archival comparison, not runtime).
- All configuration is defined and maintained in Python in `refiner_config.py` as TypedDicts:
  - Documents (eICR, RR, with all supported versions and substructure)
  - Sections (mapped to documents/versions, with required/optional metadata)
  - Entries/clinical elements—nested into section structures as needed.
- Creation or update of any config is a PR (reviewable Python code).
- Type-checked via mypy/gated by CI.
- All helper functions and refiner logic operate directly on these TypedDict data structures.

### Helper Function Development

Implement and document the following helpers, with tests to ensure version/type-awareness:

```python
from typing import Dict, List, Optional, Set, Tuple
from lxml.etree import _Element

def get_required_sections(config: dict, doc_type: str, version: str) -> list[str]:
    ...

def get_trigger_code_template_oids(config: dict, doc_type: str, version: str) -> set[str]:
    ...

def get_section_display_name(config: dict, doc_type: str, version: str, loinc_code: str) -> str | None:
    ...

def get_section_trigger_code_oids(config: dict, doc_type: str, version: str, loinc_code: str) -> list[str]:
    ...

def detect_document_version(xml_root: _Element) -> tuple[str, str]:
    ...
```

All processing of documents and sections routes through these helpers and TypedDicts. Any new section or version handling is strictly typed (enforced by static analysis).

### Document Processing & Version Detection

- Centralize version and type detection using CDA `<templateId root="..."/>` and its `extension` in the document XML header.
- All codepaths route document handling and section/OID/entry logic based on these detected values. No use of hardcoded version literals.
- If a version/type is unrecognized, log a clear diagnostic, emit metrics, skip refinement, and quarantine for review.

### Trigger Code Template Discovery

- Discovery logic for trigger codes is entirely config-driven, using information from `refiner_config.py`.
- Update/generate XPath queries to search all supported CDA element types for template IDs and trigger codes:
  - `<observation>`, `<act>`, `<procedure>`, `<organizer>`, `<manufacturedProduct>`, and direct `<templateId/@root>`.
- Ensure all newly introduced or modified section templates in 3.1.1 are backed by typed config and logic.

| Element Type            | Covered by Current Logic? | Extra XPath for Trigger Templates? |
| ----------------------- | :-----------------------: | :--------------------------------: |
| `<observation>`         |            Yes            |     Possibly (for templateId)      |
| `<act>`                 |            Yes            |     Possibly (for templateId)      |
| `<translation>`         |            Yes            |                 No                 |
| `<value>`               |            Yes            |                 No                 |
| `<procedure>`           |    Yes (if child code)    |     Possibly (for templateId)      |
| `<organizer>`           |    Yes (if child code)    |     Possibly (for templateId)      |
| `<manufacturedProduct>` |    Yes (if child code)    |     Possibly (for templateId)      |
| `<templateId/@root>`    |            No             |            Yes (needed)            |
| code on parent element  |            No             |               Maybe                |

### Validation, Testing, and Automation

- Archive and maintain a ZIP bundle containing:
  - Representative eICR 3.1.1 and 1.1 XML files testing all major code paths/sections/templates.
  - RR 1.1 XML sample.
- Expand pytest/unit test coverage for helpers, config structure, doc type/version detection, and section/entry mapping logic.
- Automate integration of test fixtures into CI to ensure every change passes:
  - mypy/type checks on config
  - Schematron validation (using HL7 assets for 3.1.1, 1.1, and any future releases)
  - Section/OID/entry lookup and extraction tests
- All validation is run on every PR/merge as part of CI.

### Integration & QA

- Review logs and metrics for skipped/unknown versions/types (proactive error detection).
- Document and iterate on edge case handling/bugfixes surfaced in test runs or from partner feedback.

## Decision Outcome

- **TypedDict-powered config in Python** (`refiner_config.py`) is the single source of truth. No primary use of JSON config; legacy JSON remains only as an archive.
- All helper functions and doc/version processing work directly with these TypedDict models.
- Refiner can easily accommodate per-section/per-entry specialization, additional versions, and new HL7 requirements.
- All processing, validation, and tests are driven by code—not external or desynchronized flat config files.

## Consequences

**Positive:**

- Maximal developer safety and productivity: type checks, code review for every config change, and docstring-driven onboarding.
- Clear, well-reviewed logic for every supported document, section, and version.
- Easy to extend and maintain for future HL7 changes.
- No risk of config drift between JSON and code.

**Negative:**

- Slightly higher bar for non-Pythonic contributors (but clarity/review value outweighs).
- All config changes require Python PR and CI cycle.

## Appendix

### Related tickets

**Implementation:**

- _add link to tickets created from this decision._

**Spike:**

- [#563](https://github.com/CDCgov/dibbs-ecr-refiner/issues/563)

### Sources for more information

- [eCR-CDA-Notes.md](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/refiner/eCR-CDA-Notes.md) — CDA implementation details
- [refiner_config.py] (proposed) — single source of config, maintained in code as TypedDicts
- [refiner_config.json](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/refiner/assets/refiner_config.json) — legacy config, for comparison only
- [HL7/CDA-phcaserpt](https://github.com/HL7/CDA-phcaserpt) — HL7 Implementation Guide and Schematron for eICR/RR (including 3.1.1)
