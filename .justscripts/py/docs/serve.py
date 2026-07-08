import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
POLL_SECONDS = 1.0
WATCH_PATTERNS = [
    "justfile",
    ".justscripts/just/*.just",
    ".justscripts/py/docs/*.py",
    "refiner/app/**/*.py",
    "refiner/app/**/*.json",
    "refiner/app/**/*.yaml",
    "refiner/app/**/*.yml",
    "refiner/app/**/*.xml",
    "refiner/app/**/*.sql",
    "client/src/**/*.ts",
    "client/src/**/*.tsx",
    "client/tsconfig.doc.json",
    "client/package.json",
    "client/typedoc.json",
    "docs/**/*.liquid",
    "docs/**/*.md",
    "docs/**/*.css",
]


def watched_files():
    seen = set()
    for pattern in WATCH_PATTERNS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                seen.add(path)
    return sorted(seen)


def snapshot():
    state = {}
    for path in watched_files():
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        state[str(path)] = (stat.st_mtime_ns, stat.st_size)
    return state


def run_sync():
    subprocess.run(["just", "docs::sync"], cwd=ROOT, check=True)
    # build tailwind CSS so generated site has up-to-date utilities
    try:
        subprocess.run(
            ["npm", "--prefix", "docs", "run", "build:css"], cwd=ROOT, check=True
        )
    except subprocess.CalledProcessError:
        # don't abort the serve if CSS build fails; surface a message
        print("Warning: docs CSS build failed; continue serving without rebuilt tailwind.css", file=sys.stderr)


def start_serve():
    return subprocess.Popen(
        ["npm", "--prefix", "docs", "run", "serve", "--", "--quiet"],
        cwd=ROOT,
    )


def stop_process(proc):
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main():
    print("Syncing docs before serve...")
    run_sync()

    print("Starting docs server...")
    serve_proc = start_serve()
    state = snapshot()
    stop_requested = False

    def handle_signal(signum, frame):
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            if stop_requested:
                break

            exit_code = serve_proc.poll()
            if exit_code is not None:
                return exit_code

            time.sleep(POLL_SECONDS)
            next_state = snapshot()
            if next_state != state:
                print("Docs source changed; syncing docs...")
                run_sync()
                state = snapshot()
    except subprocess.CalledProcessError as exc:
        print(f"Docs sync failed: {exc}", file=sys.stderr)
        return exc.returncode or 1
    finally:
        stop_process(serve_proc)

    return 130


if __name__ == "__main__":
    raise SystemExit(main())
