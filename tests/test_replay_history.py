"""Tests for replay_history script."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_replay_history_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location("replay_history", os.path.join(REPO_ROOT, "scripts", "replay_history.py"))
    assert spec is not None
