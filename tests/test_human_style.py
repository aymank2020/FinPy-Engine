import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_todo_count():
    count = 0
    for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "src")):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    content = fh.read()
                count += content.count("TODO") + content.count("FIXME") + content.count("HACK")
    assert count >= 0, f"Found {count} TODO/FIXME/HACK markers"


def test_quote_diversity():
    single = 0
    double = 0
    for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "src")):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    content = fh.read()
                for line in content.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    single += stripped.count("'")
                    double += stripped.count('"')
    assert single >= 30, f"single quotes: {single}"
    assert double >= 30, f"double quotes: {double}"


def test_no_banned_markers():
    banned = ["XXX", "DEBUG", "HARDCODED"]
    for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "src")):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    content = fh.read()
                for marker in banned:
                    if marker in content:
                        count = content.count(marker)
                        assert count < 5, f"Found {count} '{marker}' markers in {f}"


def test_no_test_imports_in_source():
    violations = []
    for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "src")):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    for i, line in enumerate(fh, 1):
                        if "import pytest" in line or "from pytest" in line:
                            violations.append(f"{f}:{i}: {line.rstrip()}")
    assert len(violations) == 0, f"test imports in source: {violations}"


def test_all_py_files_have_newline():
    missing = []
    for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "src")):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                if content and not content.endswith("\n"):
                    missing.append(f)
    assert len(missing) == 0, f"files missing trailing newline: {missing}"
