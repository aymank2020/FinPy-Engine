"""CI workflow smoke check."""

import os
import yaml


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_ci_workflow_exists():
    path = os.path.join(REPO_ROOT, ".github", "workflows", "ci.yml")
    assert os.path.isfile(path)


def test_ci_workflow_steps():
    path = os.path.join(REPO_ROOT, ".github", "workflows", "ci.yml")
    with open(path) as f:
        workflow = yaml.safe_load(f)
    steps = workflow["jobs"]["test"]["steps"]
    assert len(steps) > 0
