"""Smoke tests for the installed package."""

import subprocess
import sys
from pathlib import Path


def test_import_outside_source_directory(tmp_path: Path) -> None:
    """Import the installed package without the checkout or PYTHONPATH."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", "import dibbs_ecr"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
