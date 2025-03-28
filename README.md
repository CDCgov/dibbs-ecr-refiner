# DIBBs eCR Refiner

🚧 The DIBBs eCR Refiner is under construction 🚧

## Running the linter

The linter can be run two different ways: either manually via the `ruff` command or automatically when you go to create a new commit, which is powered by `pre-commit`.

### Manually

1. Activate the `refiner` virtual environment (steps listed [here](./api/refiner/README.md#running-from-python-source-code))
2. Install dev dependencies with `pip install -r dev-requirements.txt`
3. Run any `ruff` command you'd like (see [here](https://docs.astral.sh/ruff/linter/))

### Pre-commit

1. Install [pre-commit](https://pre-commit.com/)
2. Run `pre-commit install`
3. Run `pre-commit run --all-files` to check that the tool is working properly

The `pre-commit` hook will automatically fix any linter issues and will also format the code.

## Running the eCR Refiner with Docker

The project can be run from the top-level directory with `docker compose up`.
