"""Create ZIP archive of the repository with proper FinPy-Engine/ top-level structure."""

import os
import sys
import zipfile


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_PATTERNS = {
    "__pycache__", ".pytest_cache", "htmlcov", ".ruff_cache",
    ".mypy_cache", "build", "dist", "*.egg-info", ".coverage",
    "*.pyc", ".kiro", ".cursor", ".idea", ".vscode",
    ".venv", "venv", "node_modules", ".env",
}


def _should_exclude(name: str) -> bool:
    parts = name.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDE_PATTERNS:
            return True
        for pat in EXCLUDE_PATTERNS:
            if pat.startswith("*") and part.endswith(pat[1:]):
                return True
    return False


def main():
    parent = os.path.dirname(REPO_ROOT)
    archive_name = os.path.join(parent, "FinPy-Engine.zip")
    top_dir = "FinPy-Engine"

    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(REPO_ROOT):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, REPO_ROOT).replace("\\", "/")
                if _should_exclude(rel):
                    continue
                arcname = f"{top_dir}/{rel}"
                zf.write(full, arcname)

    required = [
        f"{top_dir}/.git/HEAD", f"{top_dir}/.git/refs/heads/main",
        f"{top_dir}/tests/conftest.py", f"{top_dir}/Dockerfile",
        f"{top_dir}/README.md", f"{top_dir}/pyproject.toml",
        f"{top_dir}/src/finpy/__init__.py",
    ]
    with zipfile.ZipFile(archive_name, "r") as zf:
        namelist = zf.namelist()
        missing = [r for r in required if r not in namelist]

    if missing:
        print(f"Missing required entries: {missing}", file=sys.stderr)
        os.remove(archive_name)
        sys.exit(1)

    size = os.path.getsize(archive_name)
    print(f"Archive: {archive_name} ({size} bytes)")


if __name__ == "__main__":
    main()
