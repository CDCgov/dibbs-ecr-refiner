set working-directory := '../../refiner'

alias h := _default
alias help := _default

alias t := test
alias l := lint
alias c := check
alias i := install
alias id := install-dev

@_default:
    just --list server

set dotenv-load

_venv:
    [ -d .venv ] || python3 -m venv .venv

[group('test')]
[doc('Run pytest suite')]
test: _venv
    .venv/bin/pytest tests

[doc('Run Ruff checker and formatter')]
lint: _venv
    .venv/bin/ruff check
    .venv/bin/ruff format

[doc('Run mypy type checks')]
check: _venv
    .venv/bin/mypy

[group('dependencies')]
[doc('Install dependencies locally')]
install: _venv
      .venv/bin/pip install -r requirements.txt

[group('dependencies')]
[doc('Install all dependencies locally')]
install-dev: _venv
      .venv/bin/pip install -r requirements-dev.txt -r requirements.txt
