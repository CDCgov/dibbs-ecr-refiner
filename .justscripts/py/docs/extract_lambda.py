import json
import sys
from pathlib import Path
import griffe


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

                member_info = {
                    "name": sub_member.path,
                    "docstring": _get_docstring(sub_member),
                    "lineno": sub_member.lineno,
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
                        # Only process functions/classes, skip attributes
                        if method.kind not in ("function", "class"):
                            continue
                        method_info = {
                            "name": method_name,
                            "docstring": _get_docstring(method),
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

                api_data["modules"].append(member_info)
        else:
            # Only process functions and classes at top level
            if member.kind not in ("function", "class"):
                continue

            member_info = {
                "name": member.path,
                "docstring": _get_docstring(member),
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
        print(f"Wrote {module_count} Lambda functions to {output_dir / 'lambda-api.json'}")
    except Exception as e:
        print(f"Error extracting Lambda docs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
