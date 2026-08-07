set working-directory := "../../"

npm := require('npm')

alias h := _default
alias help := _default

@_default:
    just --list docs

_venv:
    [ -d refiner/.venv ] || python3 -m venv refiner/.venv

[doc('Install documentation site dependencies (11ty)')]
[group('dependencies')]
install:
    {{ npm }} --prefix docs install
    {{ npm }} --prefix docs run build:css
    just server::install-dev

[doc('Extract Python API docs using griffe')]
[group('extraction')]
sync: install _venv
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_python.py
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_lambda.py
    refiner/.venv/bin/python3 .justscripts/py/docs/validate_lambda_docs.py

[doc('Build the documentation site')]
[group('build')]
build: sync
    {{ npm }} --prefix docs run build -- --quiet

[doc('Launch local docs preview server on port 9091 with auto-sync')]
[group('serve')]
serve: sync _venv
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🚀 Starting docs server with auto-sync..."
    echo ""

    # Start Python watcher in background
    refiner/.venv/bin/python3 .justscripts/py/docs/watch.py &
    WATCHER_PID=$!

    # Trap to kill watcher on exit
    trap "echo ''; echo '🛑 Stopping watcher...'; kill $WATCHER_PID 2>/dev/null || true; wait $WATCHER_PID 2>/dev/null || true" EXIT INT TERM

    # Start eleventy server (foreground)
    {{ npm }} --prefix docs run serve -- --port 9091

[doc('Debug manual sync issues with detailed diagnostics')]
[group('debug')]
debug-sync: _venv
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🔍 Debugging docs sync process..."
    echo ""

    # 1. Environment validation
    echo "📋 Environment Check:"
    echo "Working directory: $(pwd)"
    echo "Virtual env: $(ls -la refiner/.venv/bin/python3 2>/dev/null || echo 'MISSING')"
    echo ""

    # 2. Dependency verification
    echo "📦 Testing Python imports:"
    refiner/.venv/bin/python3 -c "import griffe, docstring_parser, watchdog; print('✅ All imports successful')" || echo "❌ Import failure"
    echo ""

    # 3. Pre-sync file state
    echo "📊 Current JSON file state:"
    ls -la docs/_data/*.json 2>/dev/null || echo "No JSON files found"
    echo ""

    # 4. Test griffe module loading
    echo "🔍 Testing griffe module loading:"
    refiner/.venv/bin/python3 -c "import griffe; pkg = griffe.load('app', search_paths=['refiner'], resolve_aliases=False); print(f'✅ Loaded app module with {len(pkg.members)} members')" || echo "❌ Module loading failed"
    echo ""

    # 5. Run extraction with detailed output
    echo "🚀 Running extraction scripts with full output:"
    echo "--- extract_python.py ---"
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_python.py || echo "❌ Python extraction failed"
    echo ""
    echo "--- extract_lambda.py ---"
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_lambda.py || echo "❌ Lambda extraction failed"
    echo ""
    echo "--- validate_lambda_docs.py ---"
    refiner/.venv/bin/python3 .justscripts/py/docs/validate_lambda_docs.py || echo "❌ Lambda validation failed"
    echo ""

    # 6. Post-sync file state
    echo "📊 Updated JSON file state:"
    ls -la docs/_data/*.json 2>/dev/null || echo "No JSON files found"
    echo ""

    # 7. Content verification
    echo "🔢 Module counts:"
    python3 -c "
    import json
    try:
        with open('docs/_data/python-api.json') as f:
            data = json.load(f)
            print(f'Python modules: {len(data.get(\"modules\", []))}')
    except: print('Python API: Error reading')
    try:
        with open('docs/_data/lambda-api.json') as f:
            data = json.load(f)
            print(f'Lambda modules: {len(data.get(\"modules\", []))}')
    except: print('Lambda API: Error reading')
    "
