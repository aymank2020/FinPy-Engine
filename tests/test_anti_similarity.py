"""Anti-similarity checks."""

import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNED_TOKENS = ["Aqar", "Diar", "AfterQuery", "Silver"]


def test_no_banned_tokens_in_source():
    exts = (".py", ".md")
    for root, dirs, files in os.walk(REPO_ROOT):
        if ".git" in root or ".kiro" in root:
            continue
        for f in files:
            if f.endswith(exts):
                # skip self-check to avoid false positive
                if f == "test_anti_similarity.py":
                    continue
                path = os.path.join(root, f)
                with open(path) as fh:
                    content = fh.read()
                for token in BANNED_TOKENS:
                    assert token not in content, f"Banned token '{token}' found in {path}"
