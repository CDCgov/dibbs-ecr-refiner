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
