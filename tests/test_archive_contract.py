"""Archive contract tests."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_make_zip_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location("make_zip", os.path.join(REPO_ROOT, "scripts", "make_zip.py"))
    assert spec is not None
