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

set dotenv-load := true

_venv:
    [ -d .venv ] || python3 -m venv .venv

[doc('Run pytest suite')]
[group('test')]
test: _venv
    .venv/bin/pytest tests

[doc('Run Ruff checker, fix things, and formatter')]
fix: _venv
    .venv/bin/ruff check --fix
    .venv/bin/ruff format

[doc('Run Ruff checker and formatter')]
lint: _venv
    .venv/bin/ruff check
    .venv/bin/ruff format

[doc('Run mypy type checks')]
check: _venv
    .venv/bin/mypy

[doc('Install dependencies locally')]
[group('dependencies')]
install: _venv
    .venv/bin/pip install -r requirements.txt

[doc('Install all dependencies locally')]
[group('dependencies')]
install-dev: _venv
    .venv/bin/pip install -r requirements-dev.txt -r requirements.txt

[doc('Seed Localstack with the infra needed for manual tests')]
[group('localstack')]
seed-localstack:
    python ./tests/localstack/seed.py
