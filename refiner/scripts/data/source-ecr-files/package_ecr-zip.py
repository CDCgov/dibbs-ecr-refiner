import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

SOURCE_DIR: Path = Path(__file__).parent.resolve()
PACKAGE_DIR: Path = SOURCE_DIR / "packaged"


def select_file(prompt: str) -> Path | None:
    """
    Interactive selection of a file using fzf, returns the selected Path or None if cancelled.
    """

    try:
        result = subprocess.run(
            [
                "fzf",
                f"--prompt={prompt}",
                "--height=40%",
                "--layout=reverse",
            ],
            cwd=SOURCE_DIR,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        selection = result.stdout.strip()
        if not selection:
            print("No file selected.")
            return None
        return SOURCE_DIR / selection
    except subprocess.CalledProcessError:
        print("fzf was exited without a selection.")
        return None
    except FileNotFoundError:
        print("Error: fzf not found in path.")
        return None


def make_packaged_zip(eicr_path: Path, rr_path: Path, zip_name: str) -> bool:
    """
    Create a zip with CDA_eICR.xml and CDA_RR.xml, returns True if successful.
    """

    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = PACKAGE_DIR / zip_name
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_eicr = Path(tmpdir) / "CDA_eICR.xml"
            tmp_rr = Path(tmpdir) / "CDA_RR.xml"
            shutil.copyfile(eicr_path, tmp_eicr)
            shutil.copyfile(rr_path, tmp_rr)
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(tmp_eicr, "CDA_eICR.xml")
                zf.write(tmp_rr, "CDA_RR.xml")
        print(f"✅ Created {zip_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create zip: {e}")
        return False


def main() -> None:
    """
    The main function.
    """

    print("Pick the eICR file:")
    eicr = select_file("Select eICR (will be CDA_eICR.xml): ")
    if not eicr:
        return

    print("Pick the RR file:")
    rr = select_file("Select RR (will be CDA_RR.xml): ")
    if not rr:
        return

    zip_name = input("Enter name for the zip archive (e.g., mytest.zip): ")
    if not zip_name.endswith(".zip"):
        zip_name += ".zip"
    success = make_packaged_zip(eicr, rr, zip_name)
    if success:
        print(f"Ready for upload: {PACKAGE_DIR / zip_name}")


if __name__ == "__main__":
    main()
