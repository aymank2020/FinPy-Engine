"""Tests for preflight checks."""

import subprocess
import sys
import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_preflight_imports():
    result = subprocess.run([sys.executable, "-c", "import scripts.preflight"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0
