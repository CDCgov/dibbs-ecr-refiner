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
    # build tailwind css once so the site has the generated CSS
    {{ npm }} --prefix docs run build:css

[doc('Synchronize distributed markdown files and Just commands')]
sync: install _venv
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_just.py
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_python.py
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_ts.py
    refiner/.venv/bin/python3 .justscripts/py/docs/extract_openapi.py

[doc('Build the documentation site strictly')]
build: sync
    {{ npm }} --prefix docs run build -- --quiet

[doc('Launch local documentation preview server with source watch')]
serve: _venv
    refiner/.venv/bin/python3 .justscripts/py/docs/serve.py
