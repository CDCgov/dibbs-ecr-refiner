set working-directory := '../../refiner'

alias h := _default
alias help := _default
alias t := test
alias ti := test-integration
alias tl := test-lambda
alias ts := test-scenarios
alias us := update-snapshots
alias tu := test-unit
alias ta := test-all
alias f := fix
alias l := lint
alias c := check
alias sl := seed-localstack
alias i := install
alias ia := install-all
alias id := install-dev
alias il := install-lambda
alias ild := install-lambda-dev

@_default:
    just --list server

set dotenv-load

_venv:
    [ -d .venv ] || python3 -m venv .venv

[doc('Run pytest wrapper. Must include arguments.')]
[group('test')]
test +ARGS: _venv
    .venv/bin/python3 -m pytest {{ ARGS }}

[doc('Run Unit tests')]
[group('test')]
test-unit: _venv
    .venv/bin/python3 -m pytest tests/unit

[doc('Run Integration tests')]
[group('test')]
test-integration: _venv
    .venv/bin/python3 -m pytest tests/integration --ignore=tests/integration/scenarios

[doc('Run Scenarios tests')]
[group('test')]
test-scenarios: _venv
    .venv/bin/python3 -m pytest tests/integration/scenarios

[doc('Update Scenarios tests snapshots.')]
[group('test')]
update-snapshots: _venv
    .venv/bin/pytest -vvv tests/integration/scenarios --update-snapshots

[doc('Run Lambda tests')]
[group('test')]
test-lambda: _venv
    .venv/bin/python3 -m pytest app/lambda

[doc('Run all tests')]
[group('test')]
test-all: _venv
    just server test-integration
    just server test-lambda
    just server test-scenarios
    just server test-unit

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

[doc('Install all depenencies e.g Refiner and Lambda')]
[group('dependencies')]
install-all: _venv
    just server install-dev
    just server install-lambda-dev

[doc('Install dependencies locally')]
[group('dependencies')]
install: _venv
    .venv/bin/pip install -r ./requirements.txt

[doc('Install all dependencies locally')]
[group('dependencies')]
install-dev: _venv
    .venv/bin/pip install -r ./dev-requirements.txt -r ./requirements.txt

[doc('Install Lambda dependencies locally')]
[group('dependencies')]
install-lambda: _venv
    .venv/bin/pip install -r ./requirements.txt -r ./app/lambda/requirements.txt

[doc('Install all Lambda dependencies locally')]
[group('dependencies')]
install-lambda-dev: _venv
    .venv/bin/pip install -r ./dev-requirements.txt -r ./app/lambda/dev-requirements.txt -r ./app/lambda/requirements.txt

[doc('Seed Localstack with the infra needed for manual tests')]
[group('localstack')]
seed-localstack: _venv
    .venv/bin/python ./tests/localstack/seed.py
