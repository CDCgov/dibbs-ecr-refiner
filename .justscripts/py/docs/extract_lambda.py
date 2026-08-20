import json
import re
import sys
from pathlib import Path
import griffe
from docstring_parser import parse as parse_docstring, Style


def _fold_continuation_lines(text: str) -> str:
    lines = text.split("\n")
    result = []
    for line in lines:
        if result and line.strip() and line[0] in (" ", "\t") and ":" not in line:
            result[-1] += " " + line.strip()
        else:
            result.append(line)
    return "\n".join(result)


def _parse_google_docstring(raw: str) -> dict:
    """Parse a Google-style docstring into structured data."""
    if not raw:
        return {
            "summary": "",
            "description": "",
            "params": [],
            "returns": None,
            "raises": [],
        }

    try:
        raw = _fold_continuation_lines(raw)
        parsed = parse_docstring(raw, style=Style.GOOGLE)
    except Exception:
        return {
            "summary": "",
            "description": "",
            "params": [],
            "returns": None,
            "raises": [],
        }

    summary = parsed.short_description or ""
    description = parsed.long_description or ""

    params = []
    if parsed.params:
        for p in parsed.params:
            params.append({
                "name": p.arg_name,
                "type": p.type_name or "",
                "description": p.description or "",
                "default": str(p.default) if p.default is not None else "",
            })

    returns = None
    if parsed.returns:
        returns = {
            "type": parsed.returns.type_name or "",
            "description": parsed.returns.description or "",
        }

    raises = []
    if parsed.raises:
        for r in parsed.raises:
            raises.append({
                "type": r.type_name or "",
                "description": r.description or "",
            })

    return {
        "summary": summary,
        "description": description,
        "params": params,
        "returns": returns,
        "raises": raises,
    }


def _strip_stage_role(raw: str) -> str:
    """Remove Stage and Role sections from a raw docstring."""
    return re.split(r"\nStage:", raw)[0].strip()


def _extract_stage_role(raw: str) -> dict:
    """Extract Stage and Role from a raw docstring using regex."""
    if not raw:
        return {"stage": None, "role": None}

    stage = None
    role = None

    stage_match = re.search(r"Stage:\s*\n?\s*(.+?)(?:\n\s*\n|\n\s*Role:|\Z)", raw, re.DOTALL)
    if stage_match:
        stage = stage_match.group(1).strip()

    role_match = re.search(r"Role:\s*\n?\s*(.+?)(?:\n\s*\n|\Z)", raw, re.DOTALL)
    if role_match:
        role = role_match.group(1).strip()

    return {"stage": stage, "role": role}


def _get_docstring(member):
    """Safely get docstring value, avoiding alias resolution crashes."""
    if member.is_alias:
        return ""
    if member.docstring:
        try:
            return member.docstring.value or ""
        except Exception:
            return ""
    return ""


def _get_annotation(annotation):
    """Safely get annotation string from a griffe annotation object."""
    if annotation is None:
        return None
    try:
        return str(annotation)
    except Exception:
        return str(annotation) if hasattr(annotation, 'name') else None


def _build_member_info(sub_member, source_type: str = "production") -> dict:
    """Build a member info dict with stage, role, and source_type."""
    docstring = _get_docstring(sub_member)
    stage_role = _extract_stage_role(docstring)
    clean_docstring = _strip_stage_role(docstring)

    member_info = {
        "name": sub_member.path,
        "docstring": docstring,
        "parsed_docstring": _parse_google_docstring(clean_docstring),
        "lineno": sub_member.lineno,
        "stage": stage_role["stage"],
        "role": stage_role["role"],
        "source_type": source_type,
    }

    if sub_member.kind == "function" and sub_member.signature:
        member_info["signature"] = sub_member.signature()
        member_info["parameters"] = [
            {
                "name": p.name,
                "annotation": _get_annotation(p.annotation),
                "default": str(p.default) if p.default else None,
            }
            for p in sub_member.parameters
        ]
        if sub_member.returns:
            member_info["return_annotation"] = _get_annotation(sub_member.returns)

    if sub_member.kind == "class":
        member_info["methods"] = []
        for method_name, method in sub_member.members.items():
            if method.is_alias:
                continue
            if method_name.startswith("_") and method_name != "__init__":
                continue
            if method.kind not in ("function", "class"):
                continue

            method_docstring = _get_docstring(method)
            method_info = {
                "name": method_name,
                "docstring": method_docstring,
                "parsed_docstring": _parse_google_docstring(method_docstring),
                "lineno": method.lineno,
            }
            if method.signature:
                method_info["signature"] = method.signature()
                method_info["parameters"] = [
                    {
                        "name": p.name,
                        "annotation": _get_annotation(p.annotation),
                        "default": str(p.default) if p.default else None,
                    }
                    for p in method.parameters
                ]
            member_info["methods"].append(method_info)

    return member_info


def extract_lambda_docs(search_path: str) -> dict:
    """Extract Lambda function docs using griffe."""
    api_data: dict = {"modules": []}

    pkg = griffe.load("app", search_paths=[search_path], resolve_aliases=False)

    try:
        lambda_module = pkg["lambda"]
    except KeyError:
        print("Warning: lambda module not found", file=sys.stderr)
        return api_data

    # Lambda has submodules (lambda_function, test_lambda), recurse into them
    for member_name, member in lambda_module.members.items():
        if member.is_alias:
            continue
        if member_name.startswith("_"):
            continue

        # Determine source type
        source_type = "test" if member_name.startswith("test_") else "production"

        # If it's a submodule, recurse into it
        if member.kind == "module":
            for sub_name, sub_member in member.members.items():
                if sub_member.is_alias:
                    continue
                if sub_name.startswith("_"):
                    continue
                # Only process functions and classes, skip attributes
                if sub_member.kind not in ("function", "class"):
                    continue

                member_info = _build_member_info(sub_member, source_type)
                api_data["modules"].append(member_info)
        else:
            # Only process functions and classes at top level
            if member.kind not in ("function", "class"):
                continue

            member_info = _build_member_info(member, source_type)
            api_data["modules"].append(member_info)

    return api_data


def main():
    print("Extracting Lambda documentation with griffe...")
    search_path = "refiner"
    output_dir = Path("docs/_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        data = extract_lambda_docs(search_path)
        module_count = len(data["modules"])
        with open(output_dir / "lambda-api.json", "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"Wrote {module_count} Lambda functions to {output_dir / 'lambda-api.json'}")
    except Exception as e:
        print(f"Error extracting Lambda docs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
