#!/usr/bin/env python3
"""Watch Python source files and auto-sync docs when changes detected."""
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class PythonDocsHandler(FileSystemEventHandler):
    """Handle Python file changes by re-running extraction scripts."""

    def __init__(self, debounce_seconds: float = 1.0):
        super().__init__()
        self.debounce_seconds = debounce_seconds
        self.last_sync = 0
        self.pending_sync = False

    def on_modified(self, event: FileSystemEvent):
        """Trigger sync when Python files are modified."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix != ".py":
            return

        # Debounce rapid successive changes
        now = time.time()
        if now - self.last_sync < self.debounce_seconds:
            self.pending_sync = True
            return

        self._sync_docs(path)

    def _sync_docs(self, changed_file: Path):
        """Run extraction scripts."""
        try:
            display_path = changed_file.relative_to(Path.cwd())
        except ValueError:
            # Path is already relative
            display_path = changed_file
        print(f"\n🔄 Detected change in {display_path}")
        print("📚 Re-extracting Python API docs...")

        venv_python = Path("refiner/.venv/bin/python3")

        try:
            # Run Python API extraction
            result = subprocess.run(
                [str(venv_python), ".justscripts/py/docs/extract_python.py"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(result.stdout, end="")

            # Run Lambda extraction
            result = subprocess.run(
                [str(venv_python), ".justscripts/py/docs/extract_lambda.py"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(result.stdout, end="")

            print("✅ Docs synced successfully\n")
            self.last_sync = time.time()
            self.pending_sync = False

        except subprocess.CalledProcessError as e:
            print(f"❌ Extraction failed: {e}", file=sys.stderr)
            if e.stdout:
                print(e.stdout, file=sys.stderr)
            if e.stderr:
                print(e.stderr, file=sys.stderr)


def main():
    """Watch Python source files for changes."""
    watch_paths = [
        Path("refiner/app/services"),
        Path("refiner/app/api"),
        Path("refiner/app/core"),
        Path("refiner/app/lambda"),
    ]

    # Verify paths exist
    for path in watch_paths:
        if not path.exists():
            print(f"Warning: {path} does not exist, skipping watch", file=sys.stderr)

    existing_paths = [p for p in watch_paths if p.exists()]

    if not existing_paths:
        print("Error: No valid watch paths found", file=sys.stderr)
        sys.exit(1)

    print("👀 Watching Python source files for changes...")
    for path in existing_paths:
        print(f"   📂 {path}")
    print("\nPress Ctrl+C to stop\n")

    handler = PythonDocsHandler(debounce_seconds=1.0)
    observer = Observer()

    for path in existing_paths:
        observer.schedule(handler, str(path), recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(1)
            # Check for pending syncs after debounce period
            if handler.pending_sync and time.time() - handler.last_sync >= handler.debounce_seconds:
                handler._sync_docs(Path("refiner/app"))
    except KeyboardInterrupt:
        print("\n👋 Stopping watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
