import json
from pathlib import Path


def get_asset_path(*paths: str) -> Path:
    """
    Get the full path to an asset file or directory.

    Args:
        *paths: Variable number of path segments to join after 'assets'
               e.g., get_asset_path('demo', 'monmothma.zip')
               or get_asset_path('refiner_details.json')

    Returns:
        Path: Full path to the requested asset

    Example:
        >>> get_asset_path('demo', 'monmothma.zip')
        Path('/path/to/project/assets/demo/monmothma.zip')
        >>> get_asset_path('refiner_details.json')
        Path('/path/to/project/assets/refiner_details.json')
    """

    base_path = Path(__file__).parent.parent.parent / "assets"
    return base_path.joinpath(*paths)


def read_json_asset(filename: str) -> dict:
    """
    Read and parse a JSON file from the assets directory.
    """

    with get_asset_path(filename).open() as f:
        return json.load(f)
