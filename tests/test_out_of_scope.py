"""Structural tests: out-of-scope artifacts."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNED = {"instruction.md", "solve.sh", "test_patch", "oracle.patch", "null.patch"}


def test_no_banned_files():
    for root, dirs, files in os.walk(REPO_ROOT):
        for f in files:
            assert f not in BANNED, f"Banned file found: {os.path.join(root, f)}"


def test_no_banned_dirs():
    banned_dirs = {"tasks", "frontend", "backend", "venv", ".venv", "env", "node_modules", ".next"}
    for root, dirs, files in os.walk(REPO_ROOT):
        for d in dirs:
            assert d not in banned_dirs, f"Banned dir found: {os.path.join(root, d)}"


def test_no_dockerignore():
    assert not os.path.exists(os.path.join(REPO_ROOT, ".dockerignore"))


def test_no_root_package_json():
    assert not os.path.exists(os.path.join(REPO_ROOT, "package.json"))
