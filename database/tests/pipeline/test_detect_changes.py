from pathlib import Path

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

    # 3. Calculate the hash using the function
    actual_hash = calculate_sha256(test_file)

    # 4. Assert that they are equal
    assert actual_hash == expected_hash
