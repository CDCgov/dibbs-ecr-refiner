#!/usr/bin/env python3
"""
Analyze logger calls in the refiner/ directory.

Recursively finds all .py files, parses them with AST, and identifies
all logger.* method calls. Categorizes findings by:
- Category: Production (refiner/app/) vs Scripts/Dev (refiner/scripts/)
- Log Level: Production-ready (info, warning, error, critical) vs Development-only (debug)
"""

from __future__ import annotations

import ast
import logging
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)


class LogCall(NamedTuple):
    """Represents a single logger call."""

    file_path: str
    line_number: int
    log_level: str
    message: str
    fields: frozenset[str]


PRODUCTION_LOG_LEVELS = frozenset({"info", "warning", "error", "critical"})
DEV_LOG_LEVELS = frozenset({"debug"})


def find_python_files(base_dir: Path) -> list[Path]:
    """Recursively find all .py files in the given directory."""
    return list(base_dir.rglob("*.py"))


def extract_logger_calls(
    file_path: Path,
) -> tuple[list[LogCall], list[tuple[str, frozenset[str]]]]:
    """
    Parse a Python file and extract all logger.* method calls.

    Returns a tuple of (calls, append_keys_calls) where:
    - calls: list of LogCall tuples with file path, line number, log level,
             message, and fields (including fields from append_keys)
    - append_keys_calls: list of (file_path, fields) tuples for append_keys calls
    """
    calls: list[LogCall] = []
    append_keys_calls: list[tuple[str, frozenset[str]]] = []
    running_append_keys: set[str] = set()

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return calls, append_keys_calls

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if this is a call on an object named 'logger'
            if isinstance(node.func, ast.Attribute):
                # Get the attribute name (e.g., 'info' in logger.info)
                attr_name = node.func.attr

                # Check if the object being called is named 'logger'
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "logger"
                ):
                    # Extract message (first positional argument)
                    message = ""
                    if node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(
                            first_arg.value, str
                        ):
                            message = first_arg.value
                        elif isinstance(first_arg, ast.JoinedStr):
                            # f-string - capture source code representation
                            message = ast.unparse(first_arg)
                        else:
                            # Variable or other expression - capture source code
                            message = ast.unparse(first_arg)

                    # Extract fields from f-string interpolations and extra={...}
                    fields: set[str] = set()

                    # Extract variable names from f-string (JoinedStr)
                    if node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.JoinedStr):
                            for value in first_arg.values:
                                if isinstance(value, ast.FormattedValue):
                                    # Extract variable name from FormattedValue
                                    if isinstance(value.value, ast.Name):
                                        fields.add(value.value.id)
                                    elif isinstance(value.value, ast.Attribute):
                                        # Handle attribute access like obj.attr
                                        fields.add(value.value.attr)

                    # Extract fields from extra={...}
                    for keyword in node.keywords:
                        if keyword.arg == "extra" and isinstance(
                            keyword.value, ast.Dict
                        ):
                            for key_node in keyword.value.keys:
                                if isinstance(key_node, ast.Constant) and isinstance(
                                    key_node.value, str
                                ):
                                    fields.add(key_node.value)

                    # Extract ALL keyword arguments (not just extra=)
                    for keyword in node.keywords:
                        if keyword.arg is not None:
                            fields.add(keyword.arg)

                    # Check if this is an append_keys call
                    if attr_name == "append_keys":
                        append_keys_fields: set[str] = set()
                        for keyword in node.keywords:
                            if keyword.arg is not None:
                                append_keys_fields.add(keyword.arg)
                        append_keys_calls.append(
                            (str(file_path), frozenset(append_keys_fields))
                        )
                        # Update running set for subsequent log calls in this file
                        running_append_keys.update(append_keys_fields)

                    # Combine direct fields with running append_keys fields
                    combined_fields = fields | running_append_keys

                    calls.append(
                        LogCall(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            log_level=attr_name,
                            message=message,
                            fields=frozenset(combined_fields),
                        )
                    )

    return calls, append_keys_calls


def categorize_file(file_path: Path, base_dir: Path) -> str:
    """
    Categorize a file as Production or Scripts/Dev.

    Production: Files in refiner/app/ (including refiner/app/lambda/)
    Scripts/Dev: Files in refiner/scripts/
    """
    try:
        rel_path = file_path.relative_to(base_dir)
    except ValueError:
        return "Unknown"

    rel_str = str(rel_path)

    if rel_str.startswith("app/"):
        return "Production"
    elif rel_str.startswith("scripts/"):
        return "Scripts/Dev"
    else:
        return "Unknown"


def categorize_log_level(log_level: str) -> str:
    """Categorize a log level as Production-ready or Development-only."""
    if log_level in PRODUCTION_LOG_LEVELS:
        return "Production-ready"
    elif log_level in DEV_LOG_LEVELS:
        return "Development-only"
    else:
        return "Other"


def generate_report(base_dir: Path) -> None:
    """Generate and print the logging analysis report."""
    python_files = find_python_files(base_dir)

    # Structure: category -> log_level -> message -> {fields: frozenset, locations: [(file, line)]}
    report_data: dict[str, dict[str, dict[str, dict[str, list[tuple[str, int]]]]]] = (
        defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(lambda: {"fields": frozenset(), "locations": []})
            )
        )
    )

    for file_path in python_files:
        calls, append_keys_calls = extract_logger_calls(file_path)

        if not calls and not append_keys_calls:
            continue

        category = categorize_file(file_path, base_dir)

        if category == "Unknown":
            continue

        for call in calls:
            log_category = categorize_log_level(call.log_level)
            # Use log_category + log_level as the key for grouping
            key = f"{log_category} / {call.log_level}"

            # Merge fields (union of all fields seen for this message)
            existing_fields = report_data[category][key][call.message]["fields"]
            report_data[category][key][call.message]["fields"] = (
                existing_fields | call.fields
            )

            # Add location if not already present
            location = (str(file_path), call.line_number)
            if location not in report_data[category][key][call.message]["locations"]:
                report_data[category][key][call.message]["locations"].append(location)

    # Print the report
    logger.info("=" * 70)
    logger.info("LOGGER CALL ANALYSIS REPORT")
    logger.info("=" * 70)
    logger.info("")

    for category in ["Production", "Scripts/Dev"]:
        if category not in report_data:
            continue

        logger.info(f"[{category}]")
        logger.info("-" * 70)

        for log_category in ["Production-ready", "Development-only", "Other"]:
            # Find all log levels for this category
            levels_to_show = [
                k
                for k in report_data[category].keys()
                if k.startswith(f"{log_category} /")
            ]

            if not levels_to_show:
                continue

            logger.info(f"\n  [{log_category}]")

            for level_key in sorted(levels_to_show):
                # Extract just the log level name (e.g., "error" from "Production-ready / error")
                log_level_name = level_key.split(" / ")[1]

                logger.info(f"\n    [{log_level_name.upper()}]")

                # Get all messages for this level
                messages = report_data[category][level_key]

                # Sort messages: non-empty first, then empty
                sorted_messages = sorted(messages.keys(), key=lambda m: (m == "", m))

                for message in sorted_messages:
                    data = messages[message]
                    fields = data["fields"]
                    locations = data["locations"]

                    display_msg = message if message else "(empty message)"
                    logger.info(f'\n    - "{display_msg}"')
                    if fields:
                        fields_str = ", ".join(sorted(fields))
                        logger.info(f"      Fields: {{{fields_str}}}")
                    logger.info("      Locations:")
                    for file_path, line_num in sorted(locations):
                        file_path_obj = Path(file_path)
                        rel_path = file_path_obj.relative_to(base_dir)
                        logger.info(f"        - {rel_path}:{line_num}")

        logger.info("")

    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    total_calls = 0
    for category in report_data:
        for level_key in report_data[category]:
            messages = report_data[category][level_key]
            count = sum(len(data["locations"]) for data in messages.values())
            total_calls += count
            logger.info(f"  {category} / {level_key}: {count} call(s)")

    logger.info(f"\nTotal logger calls found: {total_calls}")


def main() -> None:
    """Main entry point."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    base_dir = Path(__file__).parent.parent.parent / "refiner"
    generate_report(base_dir)


if __name__ == "__main__":
    main()
