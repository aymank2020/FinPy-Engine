"""Orchestrate the full build pipeline."""

import subprocess
import sys
import os


SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def run_step(name: str, script: str, *args: str) -> None:
    print(f"[{name}] Running...")
    result = subprocess.run([sys.executable, os.path.join(SCRIPTS_DIR, script), *args])
    if result.returncode != 0:
        print(f"[{name}] FAILED (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"[{name}] OK")


def main():
    run_step("build_fixtures", "build_fixtures.py")
    run_step("replay_history", "replay_history.py", "scripts/commit_plan.json")
    run_step("preflight", "preflight.py")
    run_step("make_zip", "make_zip.py")


if __name__ == "__main__":
    main()
