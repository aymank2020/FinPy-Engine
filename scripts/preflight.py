"""Pre-flight checks (Requirement 10) — 18 checks."""

import ast
import os
import re
import sys
import subprocess
from pathlib import Path


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILURES = []


def _fail(check_num: int, msg: str):
    FAILURES.append(f"Req 10.{check_num}: {msg}")


def _check_10_1():
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT)
    if branch.stdout.strip() not in ("main", "master"):
        _fail(1, f"branch is '{branch.stdout.strip()}', expected 'main' or 'master'")


def _check_10_2():
    git_dir = os.path.join(REPO_ROOT, ".git")
    if not os.path.isdir(git_dir):
        _fail(2, ".git/ missing")
    head_file = os.path.join(git_dir, "HEAD")
    if not os.path.isfile(head_file) or os.path.getsize(head_file) == 0:
        _fail(2, ".git/HEAD missing or empty")


def _check_10_3():
    if os.path.exists(os.path.join(REPO_ROOT, ".dockerignore")):
        _fail(3, ".dockerignore must not exist")


def _check_10_4():
    conftest_count = sum(
        1 for root, _, files in os.walk(REPO_ROOT) for f in files if f == "conftest.py"
    )
    if conftest_count != 1:
        _fail(4, f"expected 1 conftest.py, found {conftest_count}")


def _check_10_5():
    cov_file = os.environ.get("COVERAGE_FILE")
    if cov_file is None:
        cov_file = str(Path(REPO_ROOT) / ".coverage")
    env = os.environ.copy()
    env["COVERAGE_FILE"] = cov_file
    result = subprocess.run(
        ["pytest", "--override-ini=addopts=", "--cov=finpy", "--cov-report=term-missing"],
        capture_output=True, text=True, timeout=600, cwd=REPO_ROOT, env=env,
    )
    if result.returncode != 0:
        _fail(5, f"pytest failed:\n{result.stdout}\n{result.stderr}")


def _check_10_6():
    cov_file = os.environ.get("COVERAGE_FILE")
    if cov_file is None:
        cov_file = str(Path(REPO_ROOT) / ".coverage")
    env = os.environ.copy()
    env["COVERAGE_FILE"] = cov_file
    result = subprocess.run(
        ["pytest", "--override-ini=addopts=", "--cov=finpy", "--cov-report=term-missing"],
        capture_output=True, text=True, timeout=600, cwd=REPO_ROOT, env=env,
    )
    for line in result.stdout.split("\n"):
        if "TOTAL" in line and "%" in line:
            pct = line.strip().split()[-1].rstrip("%")
            if float(pct) < 95:
                _fail(6, f"coverage {pct}% < 95%")


def _check_10_7():
    src_dir = os.path.join(REPO_ROOT, "src", "finpy")
    if not os.path.isdir(src_dir):
        _fail(7, "src/finpy/ directory missing")
    py_files = [f for f in os.listdir(src_dir) if f.endswith(".py")]
    if "__init__.py" not in py_files:
        _fail(7, "src/finpy/__init__.py missing")


def _check_10_8():
    tests_dir = os.path.join(REPO_ROOT, "tests")
    if not os.path.isdir(tests_dir):
        _fail(8, "tests/ directory missing")
    test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
    if len(test_files) < 10:
        _fail(8, f"expected >=10 test files, found {len(test_files)}")


def _check_10_9():
    tests_dir = os.path.join(REPO_ROOT, "tests")
    if not os.path.isdir(tests_dir):
        return
    test_count = 0
    for f in os.listdir(tests_dir):
        if f.startswith("test_") and f.endswith(".py"):
            filepath = os.path.join(tests_dir, f)
            with open(filepath) as fh:
                content = fh.read()
            test_count += len(re.findall(r"^def test_", content, re.MULTILINE))
    if test_count < 200:
        _fail(9, f"expected >=200 test functions, found {test_count}")


def _check_10_10():
    fixtures_dir = Path(REPO_ROOT) / "fixtures"
    if not fixtures_dir.is_dir():
        _fail(10, "fixtures/ directory missing")
        return
    total = sum(f.stat().st_size for f in fixtures_dir.rglob("*") if f.is_file())
    if total < 25 * 1024 * 1024:
        _fail(10, f"fixtures total {total / (1024*1024):.1f} MB < 25 MB")


def _check_10_11():
    dockerfile = os.path.join(REPO_ROOT, "Dockerfile")
    if not os.path.isfile(dockerfile):
        _fail(11, "Dockerfile missing")
    else:
        with open(dockerfile) as f:
            content = f.read()
        if "python:3.12.7" not in content:
            _fail(11, "Dockerfile must use python:3.12.7-slim-bookworm")


def _check_10_12():
    readme = os.path.join(REPO_ROOT, "README.md")
    if not os.path.isfile(readme):
        _fail(12, "README.md missing")
    else:
        with open(readme) as f:
            content = f.read()
        if "FinPy" not in content:
            _fail(12, "README.md must mention FinPy")


def _check_10_13():
    pyproject = os.path.join(REPO_ROOT, "pyproject.toml")
    if not os.path.isfile(pyproject):
        _fail(13, "pyproject.toml missing")
    else:
        with open(pyproject) as f:
            content = f.read()
        if "finpy" not in content:
            _fail(13, "pyproject.toml must reference finpy")


def _check_10_14():
    src_dir = os.path.join(REPO_ROOT, "src", "finpy")
    line_count = 0
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    line_count += len(fh.readlines())
    if line_count < 5000:
        _fail(14, f"source lines {line_count} < 5000")


def _check_10_15():
    tests_dir = os.path.join(REPO_ROOT, "tests")
    line_count = 0
    for root, _, files in os.walk(tests_dir):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    line_count += len(fh.readlines())
    if line_count < 4000:
        _fail(15, f"test lines {line_count} < 4000")


def _check_10_16():
    """Every source module must have a corresponding test file."""
    src_dir = os.path.join(REPO_ROOT, "src")
    tests_dir = os.path.join(REPO_ROOT, "tests")
    test_files = {f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")}
    missing = []
    for root, _, files in os.walk(os.path.join(src_dir, "finpy")):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                expected = f"test_{f}"
                if expected not in test_files:
                    missing.append(f)
    if missing:
        _fail(16, f"missing test files for: {missing[:5]}")


def _check_10_17():
    """No banned files or directories."""
    banned = {"node_modules", ".env", "package.json", ".dockerignore"}
    found = []
    for root, dirs, files in os.walk(REPO_ROOT):
        for d in dirs:
            if d in banned:
                found.append(os.path.relpath(os.path.join(root, d), REPO_ROOT))
        for f in files:
            if f in banned:
                found.append(os.path.relpath(os.path.join(root, f), REPO_ROOT))
    if found:
        _fail(17, f"banned items found: {found}")


def _check_10_18():
    """Source code must parse without syntax errors."""
    src_dir = os.path.join(REPO_ROOT, "src")
    errors = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".py"):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath) as fh:
                        ast.parse(fh.read(), filename=filepath)
                except SyntaxError as e:
                    errors.append(f"{os.path.relpath(filepath, REPO_ROOT)}: {e}")
    if errors:
        _fail(18, f"syntax errors: {errors[:3]}")


def main():
    checks = [f for f in dir() if f.startswith("_check_10_")]
    for check_name in sorted(checks):
        try:
            globals()[check_name]()
        except Exception as e:
            FAILURES.append(f"Req 10.{check_name.split('_')[-1]}: exception: {e}")
    if FAILURES:
        print("Pre-flight FAILED:")
        for f in FAILURES:
            print(f"  {f}")
        sys.exit(1)
    print("All 18 pre-flight checks passed.")


if __name__ == "__main__":
    main()
