import subprocess
import json
import re
import sys
from pathlib import Path


def get_just_json():
    try:
        result = subprocess.run(
            ["just", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running just --json: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing just --json output: {e}", file=sys.stderr)
        sys.exit(1)


def get_full_to_short_module_map(just_json):
    full_to_short = {}

    for module_name, module_data in just_json.get("modules", {}).items():
        doc = module_data.get("doc", "")
        alias_match = re.match(r"Alias for `(\w+)`", doc)
        if alias_match:
            target_module = alias_match.group(1)
            full_to_short[target_module] = module_name

    return full_to_short


def is_alias_module(module_data):
    doc = module_data.get("doc", "")
    return bool(re.match(r"Alias for `", doc))


def extract_recipes_from_module(module_data, module_aliases, module_name):
    recipes = []
    for recipe_name, recipe_data in module_data.get("recipes", {}).items():
        namepath = recipe_data.get("namepath", "")
        doc = recipe_data.get("doc", "")
        is_private = recipe_data.get("private", False)

        if is_private:
            continue

        # Find recipe-level aliases (used only for composite aliases)
        recipe_aliases = []
        for alias_name, alias_data in module_aliases.items():
            if alias_data.get("target") == recipe_name:
                recipe_aliases.append(alias_name)

        recipes.append({
            "name": namepath,
            "description": doc if doc else "",
            "recipe_aliases": sorted(recipe_aliases),
            "module_name": module_name,
        })

    # Recurse into nested modules
    nested = module_data.get("modules", {})
    for nested_name, nested_data in nested.items():
        nested_aliases = nested_data.get("aliases", {})
        recipes.extend(extract_recipes_from_module(nested_data, nested_aliases, nested_name))

    return recipes


def extract_top_level_recipes(just_json):
    recipes = []
    for recipe_name, recipe_data in just_json.get("recipes", {}).items():
        namepath = recipe_data.get("namepath", "")
        doc = recipe_data.get("doc", "")
        is_private = recipe_data.get("private", False)

        if is_private:
            continue

        recipes.append({
            "name": namepath,
            "description": doc if doc else "",
            "recipe_aliases": [],
            "module_name": None,
        })

    return recipes


def build_composite_aliases(cmd, full_to_short):
    module_name = cmd["module_name"]
    if not module_name:
        return []

    recipe_name = cmd["name"].split("::")[-1]
    recipe_aliases = cmd["recipe_aliases"]

    # Find the short alias for this module
    short_module_alias = full_to_short.get(module_name)

    aliases = []

    if recipe_aliases and short_module_alias:
        # Keep only true shorthand aliases, not the canonical long form.
        for ra in recipe_aliases:
            aliases.append(f"{short_module_alias} {ra}")

    return aliases


def main():
    print("Extracting Just commands...")
    output_dir = Path("docs/_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    just_json = get_just_json()
    full_to_short = get_full_to_short_module_map(just_json)

    print(f"Found {len(just_json.get('modules', {}))} modules and {len(just_json.get('aliases', {}))} aliases")

    # Extract top-level recipes
    commands = extract_top_level_recipes(just_json)
    print(f"Extracted {len(commands)} top-level recipes")

    # Extract recipes from all non-alias modules
    for module_name, module_data in just_json.get("modules", {}).items():
        if is_alias_module(module_data):
            continue
        module_aliases = module_data.get("aliases", {})
        commands.extend(extract_recipes_from_module(module_data, module_aliases, module_name))

    print(f"Total recipes extracted: {len(commands)}")

    # Build alias-to-recipe mapping from top-level aliases
    alias_map = {}
    for alias_name, alias_data in just_json.get("aliases", {}).items():
        target = alias_data.get("target", "")
        alias_map[alias_name] = target

    # Link top-level aliases to their target recipes
    for cmd in commands:
        for alias_name, target in alias_map.items():
            if cmd["name"] == target:
                cmd.setdefault("aliases", []).append(alias_name)

    # Add composite aliases for module recipes
    for cmd in commands:
        composite = build_composite_aliases(cmd, full_to_short)
        if composite:
            cmd.setdefault("aliases", []).extend(composite)

    # Sort aliases and clean up
    for cmd in commands:
        cmd["aliases"] = sorted(set(cmd.get("aliases", [])))
        canonical_alias = None
        if cmd["module_name"] is not None:
            canonical_alias = f"{cmd['module_name']} {cmd['name'].split('::')[-1]}"
        else:
            canonical_alias = cmd["name"].replace("::", " ")

        cmd["aliases"] = [alias for alias in cmd["aliases"] if alias != canonical_alias]

        if cmd["module_name"] is not None:
            del cmd["module_name"]
        if cmd.get("recipe_aliases"):
            del cmd["recipe_aliases"]

    # Deduplicate by name
    seen = set()
    unique_commands = []
    for cmd in commands:
        if cmd["name"] not in seen:
            seen.add(cmd["name"])
            unique_commands.append(cmd)

    # Sort by name
    unique_commands.sort(key=lambda x: x["name"])

    with open(output_dir / "just-commands.json", "w") as f:
        json.dump(unique_commands, f, indent=2)

    print(f"Wrote {len(unique_commands)} commands to {output_dir / 'just-commands.json'}")


if __name__ == "__main__":
    main()
