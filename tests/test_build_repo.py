"""Tests for build_repo orchestrator."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_build_repo_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_repo", os.path.join(REPO_ROOT, "scripts", "build_repo.py"))
    assert spec is not None
