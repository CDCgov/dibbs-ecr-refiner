#!/usr/bin/env python3
"""Validate Lambda docstrings against glossary and check Stage/Role completeness."""

import json
import re
import sys
import tomllib
from pathlib import Path


def _build_term_patterns(terms: list[dict]) -> list[dict]:
    """Build regex patterns for each glossary term."""
    patterns = []
    for entry in terms:
        term = entry["term"]
        patterns.append({
            "term": term,
            "pattern": re.compile(re.escape(term), re.IGNORECASE),
        })
    return patterns


def _collect_text(parsed: dict) -> list[str]:
    """Collect all text fields from a parsed docstring."""
    texts = []
    if parsed.get("summary"):
        texts.append(parsed["summary"])
    if parsed.get("description"):
        texts.append(parsed["description"])
    if parsed.get("params"):
        for p in parsed["params"]:
            if p.get("description"):
                texts.append(p["description"])
    if parsed.get("returns") and parsed["returns"].get("description"):
        texts.append(parsed["returns"]["description"])
    if parsed.get("raises"):
        for r in parsed["raises"]:
            if r.get("description"):
                texts.append(r["description"])
    return texts


def validate_glossary(data_dir: Path) -> list[str]:
    """Cross-reference docstrings against glossary. Warn on undefined terms."""
    warnings = []

    glossary_path = data_dir / "glossary.toml"
    if not glossary_path.exists():
        warnings.append("glossary.toml not found — skipping glossary validation")
        return warnings

    with open(glossary_path, "rb") as f:
        glossary = tomllib.load(f)

    known_terms = {entry["term"] for entry in glossary.get("terms", [])}
    term_patterns = _build_term_patterns(glossary.get("terms", []))

    api_path = data_dir / "lambda-api.json"
    if not api_path.exists():
        warnings.append("lambda-api.json not found — skipping glossary validation")
        return warnings

    with open(api_path) as f:
        api_data = json.load(f)

    for module in api_data.get("modules", []):
        texts = _collect_text(module.get("parsed_docstring", {}))

        if module.get("methods"):
            for method in module["methods"]:
                texts.extend(_collect_text(method.get("parsed_docstring", {})))

        full_text = " ".join(texts)

        for tp in term_patterns:
            if tp["pattern"].search(full_text):
                continue

        # Check for CamelCase terms that might be undefined
        camelcase_terms = set(re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", full_text))
        for t in camelcase_terms:
            if t not in known_terms:
                warnings.append(
                    f"Undefined term '{t}' in docstring for {module.get('name', 'unknown')}"
                )

    return warnings


def validate_stage_role(data_dir: Path) -> list[str]:
    """Validate that all production functions have Stage and Role defined."""
    errors = []

    api_path = data_dir / "lambda-api.json"
    if not api_path.exists():
        errors.append("lambda-api.json not found — skipping Stage/Role validation")
        return errors

    with open(api_path) as f:
        api_data = json.load(f)

    for module in api_data.get("modules", []):
        name = module.get("name", "unknown")
        source_type = module.get("source_type", "production")

        if source_type == "test":
            continue

        stage = module.get("stage")
        role = module.get("role")

        if not stage:
            errors.append(f"Missing Stage: in docstring for {name}")
        if not role:
            errors.append(f"Missing Role: in docstring for {name}")

        if module.get("methods"):
            for method in module["methods"]:
                # Methods don't need Stage/Role since they inherit from parent
                pass

    return errors


def main():
    data_dir = Path("docs/_data")
    has_errors = False

    print("Validating Lambda docstrings...")

    stage_errors = validate_stage_role(data_dir)
    if stage_errors:
        has_errors = True
        for err in stage_errors:
            print(f"  ERROR: {err}", file=sys.stderr)

    glossary_warnings = validate_glossary(data_dir)
    for warn in glossary_warnings:
        has_errors = True
        print(f"  WARNING: {warn}", file=sys.stderr)

    if has_errors:
        print("Validation failed.", file=sys.stderr)
        sys.exit(1)
    else:
        print("Validation passed.")


if __name__ == "__main__":
    main()
