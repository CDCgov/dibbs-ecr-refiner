import json
import sys
from pathlib import Path
from griffe import load

import ast

def extract_python_docs(package_path: str):
    # TODO: Investigate why griffe.load() crashes on FastAPI aliases.
    # If possible, find a way to use griffe's more powerful resolution in the future.
    # Currently using AST for a crash-proof, portable extraction of docstrings.

    api_data = {
        "modules": []
    }

    base_path = Path(package_path)
    for py_file in base_path.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.relative_to(base_path).with_suffix("").as_posix().replace("/", ".")

        try:
            tree = ast.parse(py_file.read_text())
        except Exception as e:
            print(f"Warning: Could not parse {py_file}: {e}", file=sys.stderr)
            continue

        module_doc = ast.get_docstring(tree)
        module_info = {
            "name": module_name,
            "docstring": module_doc or "",
            "members": []
        }

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                module_info["members"].append({
                    "name": node.name,
                    "type": "Function",
                    "docstring": ast.get_docstring(node) or "",
                    "lineno": node.lineno
                })
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue

                class_doc = ast.get_docstring(node)
                methods = []
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if subnode.name.startswith("_") and subnode.name != "__init__":
                            continue
                        methods.append({
                            "name": subnode.name,
                            "docstring": ast.get_docstring(subnode) or "",
                            "lineno": subnode.lineno
                        })

                module_info["members"].append({
                    "name": node.name,
                    "type": "Class",
                    "docstring": class_doc or "",
                    "lineno": node.lineno,
                    "methods": methods
                })

        api_data["modules"].append(module_info)

    return api_data

def main():
    print("Extracting Python API documentation...")
    # Path to the refiner app source
    package_path = "refiner/app"
    output_dir = Path("docs/_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        data = extract_python_docs(package_path)
        module_count = len(data["modules"])
        with open(output_dir / "python-api.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote {module_count} Python modules to {output_dir / 'python-api.json'}")
    except Exception as e:
        print(f"Error extracting Python docs: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
