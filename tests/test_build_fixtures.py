"""Tests for build_fixtures script."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_build_fixtures_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_fixtures", os.path.join(REPO_ROOT, "scripts", "build_fixtures.py"))
    assert spec is not None
