import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Update the snapshot files we check against.
    """

    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help=(
            "Regenerate scenario snapshots from current refinement output "
            "instead of comparing against committed files. Use when "
            "refinement behavior legitimately changes."
        ),
    )


@pytest.fixture
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    """
    Whether the test run requested snapshot regeneration.
    """

    return bool(request.config.getoption("--update-snapshots"))
