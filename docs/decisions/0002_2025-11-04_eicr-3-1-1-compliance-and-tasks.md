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

- **Strongly-typed configuration as code:** All configuration (supported documents, versions, sections, entries, and relationships) is represented as Python TypedDicts or objects in `refiner_config.py` (see implementation). The in-code config is the source of truth; there are no flat JSON config files in the repo.
- **Object-Oriented, Centralized Config**: Configuration will be loaded/analyzed once at application start as a single config object (or per-document/section objects as needed), avoiding the need to pass dicts around and improving discoverability. Helper methods (e.g., for finding required sections, trigger OIDs) will be instance methods attached to these objects.
- **Future extensibility:** This models document, section, and entry structure directly in Python. It lays groundwork for per-section/entry specialization in document handling and validation.

Validation and automation targets HL7’s official Schematron and sample files published in [HL7/CDA-phcaserpt](https://github.com/HL7/CDA-phcaserpt), which explicitly references 3.1.1 in its README and assets. Subsequent incremental spec updates (e.g., v3.1.2) will be handled as Python code updates in the config models.

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

| Option                          | Pros                                                                      | Cons                                                  |
| ------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------- |
| Flat JSON                       | Portable, S3/Lambda-friendly, language-agnostic                           | No type safety, no relationships, no comments         |
| YAML                            | Comments, more readable                                                   | Parsing overhead, less direct for Python, unnecessary |
| **Python TypedDict** or Classes | Maximizes type safety, docstrings, relationships, enables static analysis | Python only, config changes are code reviews/PRs      |
| Pydantic Model                  | Runtime validation, error reporting                                       | Extra overhead, still Python-centric                  |
| Database/API                    | Dynamic updates, online editing                                           | Overkill for static config                            |

**Chosen Approach:**  
All configuration is defined as Python TypedDicts and/or dataclasses in code (`refiner_config.py` or related modules). There are no JSON configuration files. Any new version, document, section, or entry is added as a Python code change, type-checked via mypy, and reviewed in PR. This hierarchy encodes all relationships, supported document types/versions, and enables focused, documented updates as standards evolve.

> [!NOTE]
> This file should live somewhere in `refiner/app/core/`

## Implementation Details

### Object-Oriented Config Structure

- All configuration is defined and maintained as Python dataclasses or TypedDicts; the config hierarchy is instantiated as one or more objects at app startup (e.g., a `RefinerConfig` or per-version document objects). A minimal example of the new pattern:

```python
class Section:
    def __init__(self, config):
        self.code = config['code']
        self.trigger_oids = config.get('trigger_oids', [])
        # ...other attributes and nesting...

    def get_loinc(self) -> str:
        return self.code

    def get_trigger_oids(self) -> list[str]:
        return self.trigger_oids

class Document:
    def __init__(self, config):
        self.sections = [Section(sec) for sec in config['sections']]

    def get_all_section_loincs(self) -> list[str]:
        return [s.get_loinc() for s in self.sections]

    def get_all_trigger_code_oids(self) -> list[str]:
        oids = []
        for section in self.sections:
            oids.extend(section.get_trigger_oids())
        return oids

# example instantiation
config = ... # (hardcoded data)
doc = Document(config)
```

- This avoids passing around `config: dict` everywhere, and co-locates helper logic with the relevant data.
- All logic that manipulates or queries documents, sections, or entries now "lives" alongside the data they pertain to, instead of as loose functions.

#### Namespaces and XPath Handling

- A central `NAMESPACES` dictionary is defined at the config or class level, and passed/used internally for all XPath queries across document/section/entry helpers.
- This avoids repetition, reduces risk of lxml gotchas (esp. around disconnected \_Element trees), and ensures every XPath uses the same, authoritative prefix mapping.

```python
class RefinerConfig:
    NAMESPACES = {
        "cda": "urn:hl7-org:v3",
        # ... other namespaces ...
    }
```

> [!NOTE]
> Some exploration is still required to ensure we can successfully move from the current implementation of namespaces to a centralized one.

### Refactor: Location/Discovery

- All config objects and their logic will be moved to/refactored under a clear "core" namespace, e.g. `refiner/app/core/config.py`, making it obvious where the source of truth for config lives. This replaces scattered or legacy config.

### Testing and Validation Philosophy

- **Schematron as the Ground Truth**: The main integration testing for output structure/correctness is based on Schematron validation (HL7 official). This is the authoritative pass/fail check in CI.
- Additional tests, such as expected OID/section presence or "container" checks via XPath, may be added for integration test coverage or future deeper validation (and are iceboxed for follow-up if we ever find Schematron is not sufficient).
- New config/code must pass static analysis (`mypy`, pre-commit, and CI workflows).

### Helper Method Development

Update and implement helpers as instance methods rather than top-level functions. For example:

```python
class Document:
    ...
    def get_required_sections(self) -> list[str]:
        ...
    def get_trigger_code_template_oids(self) -> set[str]:
        ...
    def get_section_display_name(self, loinc_code: str) -> str | None:
        ...
    def get_section_trigger_code_oids(self, loinc_code: str) -> list[str]:
        ...
```

### Document Processing & Version Detection

- Centralize version/type detection (from CDA `<templateId>` and header extension) as a utility or config-bound function.
- All codepaths route document handling logic using detected values, never hardcoded literals.

### Trigger Code Template Discovery

- Discovery logic for trigger codes uses only the config object, never hardcoded values.
- All new or modified section templates for 3.1.1+ must be represented in central config and accessed via the model.
- See mapping for XPath element coverage above.

### Integration & QA

- Continue proactive error metrics/logging for unknown types/versions.
- Document, revisit, and iterate on edge cases surfaced in integration tests or feedback.

## Decision Outcome

- **Python class and/or TypedDict-powered config** becomes the developer source of truth.
- The config object pattern ensures all helper methods and logic are naturally co-located with their data.
- The system is easily extensible—add a document version, section, or OID by extending code+tests, not patching loose files.
- All correctness and regression validation is enforced at both static analysis time and through Schematron as ground truth in integration tests.

## Consequences

**Positive:**

- Maximal developer safety and productivity: type checks, code review for every config change, and docstring-driven onboarding.
- Helper logic is always close to its associated data; easier maintenance and onboarding.
- Centralized definitions for things like XPath namespaces that reduce cross-file bugs and confusion.
- Clear, well-reviewed logic for every supported document, section, and version.
- Easy to extend and maintain for future HL7 changes.
- No risk of config drift between JSON and code.

**Negative:**

- Slightly higher bar for non-Pythonic contributors (but clarity/review value outweighs).
- All config changes require Python PR and CI cycle.
- Additional up-front work to migrate config helpers into class/object methods (but this pays dividends for code quality).

## Appendix

### Related tickets

**Spike:**

- [#563](https://github.com/CDCgov/dibbs-ecr-refiner/issues/563)

### Sources for more information

- [eCR-CDA-Notes.md](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/refiner/eCR-CDA-Notes.md) — CDA implementation details
- [refiner_config.py] (proposed) — single source of config, maintained in code as TypedDicts or classes
- [refiner_config.json](https://github.com/CDCgov/dibbs-ecr-refiner/blob/main/refiner/assets/refiner_config.json) — legacy config, for comparison only
- [HL7/CDA-phcaserpt](https://github.com/HL7/CDA-phcaserpt) — HL7 Implementation Guide and Schematron for eICR/RR (including 3.1.1)

### Needs future discussion / icebox

- Add more granular config-driven “container” (section/entry/OID) structure checks as needed, but prioritize HL7 Schematron validation as proxy for output correctness until shown necessary.
- Revisit namespace-handling edge cases specific to lxml/XPath if/when custom container traversal logic expands.
