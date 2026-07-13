import json
import sys
from pathlib import Path
import griffe
from docstring_parser import parse as parse_docstring, Style


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


def _is_leaf_module(module):
    """Check if a module is a leaf (contains no submodules)."""
    for member_name, member in module.members.items():
        if member_name.startswith("_") or member.is_alias:
            continue
        if member.kind == "module":
            return False
    return True


def _extract_members(module):
    """Extract members (functions, classes) from a module."""
    members = []
    for member_name, member in module.members.items():
        if member.is_alias:
            continue
        if member_name.startswith("_") and member_name != "__init__":
            continue

        member_info = {
            "name": member_name,
            "type": member.kind,
            "docstring": _get_docstring(member),
            "parsed_docstring": _parse_google_docstring(_get_docstring(member)),
            "lineno": member.lineno,
        }

        if member.kind == "function" and member.signature:
            member_info["signature"] = member.signature()
            member_info["parameters"] = [
                {
                    "name": p.name,
                    "annotation": _get_annotation(p.annotation),
                    "default": str(p.default) if p.default else None,
                }
                for p in member.parameters
            ]
            if member.returns:
                member_info["return_annotation"] = _get_annotation(member.returns)

        if member.kind == "class":
            member_info["methods"] = []
            for method_name, method in member.members.items():
                if method.is_alias:
                    continue
                if method_name.startswith("_") and method_name != "__init__":
                    continue
                if method.kind not in ("function", "class"):
                    continue
                method_info = {
                    "name": method_name,
                    "docstring": _get_docstring(method),
                    "parsed_docstring": _parse_google_docstring(_get_docstring(method)),
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

        members.append(member_info)
    return members


def extract_python_docs(search_path: str) -> dict:
    """Extract Python API docs using griffe.

    Filters out db/, main.py, asgi.py.
    Uses resolve_aliases=False to avoid crashes on stdlib imports.
    Recursively finds leaf modules.
    """
    excluded_paths = {"db", "main", "asgi"}

    api_data: dict = {"modules": []}

    pkg = griffe.load("app", search_paths=[search_path], resolve_aliases=False)

    def process_module(module):
        module_name = module.name
        if module_name in excluded_paths:
            return
        if _is_leaf_module(module):
            module_info = {
                "name": module.path,
                "docstring": _get_docstring(module),
                "members": _extract_members(module),
            }
            api_data["modules"].append(module_info)
        else:
            for member_name, member in module.members.items():
                if member_name.startswith("_") or member.is_alias:
                    continue
                if member.kind == "module":
                    process_module(member)

    process_module(pkg)
    return api_data


def main():
    print("Extracting Python API documentation with griffe...")
    search_path = "refiner"
    output_dir = Path("docs/_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        data = extract_python_docs(search_path)
        module_count = len(data["modules"])
        with open(output_dir / "python-api.json", "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"Wrote {module_count} Python modules to {output_dir / 'python-api.json'}")
    except Exception as e:
        print(f"Error extracting Python docs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
