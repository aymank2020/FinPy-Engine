import tomllib
import os
from finpy import __version__


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_version_consistency():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == __version__


def test_console_script():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    scripts = data["project"]["scripts"]
    assert "finpy" in scripts
    assert scripts["finpy"] == "finpy.cli.main:main"


def test_src_layout():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert data["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]


def test_project_name():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert "finpy" in data["project"]["name"]


def test_python_requirement():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    requires_python = data["project"].get("requires-python", "")
    assert requires_python, "requires-python must be specified"


def test_license_field():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert "license" in data["project"] or "License" in str(data["project"])


def test_description_not_empty():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    desc = data["project"].get("description", "")
    assert len(desc) > 0


def test_authors_field():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    assert "authors" in data["project"]
    assert len(data["project"]["authors"]) > 0


def test_version_is_semver():
    parts = __version__.split(".")
    assert len(parts) == 3, f"Expected semver, got {__version__}"
    for p in parts:
        assert p.isdigit() or (p[0].isdigit() and p[1:].isalpha())


def test_dependencies_listed():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    deps = data["project"].get("dependencies", [])
    assert isinstance(deps, list)
