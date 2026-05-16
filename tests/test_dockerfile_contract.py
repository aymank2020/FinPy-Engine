"""Dockerfile contract tests."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_dockerfile_exists():
    assert os.path.isfile(os.path.join(REPO_ROOT, "Dockerfile"))


def test_dockerfile_base_image():
    with open(os.path.join(REPO_ROOT, "Dockerfile")) as f:
        content = f.read()
    assert "python:" in content and "slim-bookworm" in content
