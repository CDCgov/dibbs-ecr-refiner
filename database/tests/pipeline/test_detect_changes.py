import os
from pathlib import Path

from pipeline import detect_changes
from pipeline.detect_changes import calculate_sha256


def test_calculate_sha256(tmp_path: Path):
    """
    Tests that the calculate_sha256 function correctly computes the hash for a file with known content.
    """

    # 1: create a temporary file with known content
    test_file = tmp_path / "test.txt"
    content = "hello world"
    test_file.write_text(content)

    # 2: define the known, correct SHA256 hash for the content
    #    (calculated using `echo -n "hello world" | sha256sum`)
    expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    # 3. calculate the hash using the function
    actual_hash = calculate_sha256(test_file)

    # 4. assert that they are equal
    assert actual_hash == expected_hash


def test_main_runs(mocker, tmp_path) -> None:
    """
    Tes the main() function run.
    """

    # setup environment variables
    mocker.patch.dict(
        os.environ, {"TES_API_KEY": "fakekey", "API_SLEEP_INTERVAL": "0.0"}
    )

    # patch all path constants to be under tmp_path
    mocker.patch.object(detect_changes, "DATABASE_DIR", tmp_path)
    mocker.patch.object(detect_changes, "STAGING_DIR", tmp_path / "staging")
    mocker.patch.object(detect_changes, "DATA_DIR", tmp_path / "data")
    mocker.patch.object(detect_changes, "MANIFEST_PATH", tmp_path / "manifest.json")

    (tmp_path / "staging").mkdir(parents=True)
    (tmp_path / "data").mkdir(parents=True)

    # mock the fetch pipeline so nothing happens
    mocker.patch.object(detect_changes, "run_fetch_pipeline", return_value={})

    # should not raise
    detect_changes.main()
