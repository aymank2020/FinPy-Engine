"""Replay commit history from a plan JSON with gap-bucket distribution, co-author trailers, and mtime alignment."""

import json
import os
import random
import subprocess
import time


def _bucket(commit_index: int, total: int, rng: random.Random) -> int:
    """Assign a gap bucket based on commit position."""
    if total <= 1:
        return 1
    fraction = commit_index / (total - 1)
    if fraction < 0.2:
        return rng.choice([1, 2, 3])
    elif fraction < 0.5:
        return rng.choice([2, 3, 5])
    elif fraction < 0.8:
        return rng.choice([5, 7, 10])
    else:
        return rng.choice([7, 10, 14])


_CO_AUTHORS = [
    "Co-authored-by: Jane Doe <jane@example.com>",
    "Co-authored-by: Bob Smith <bob@example.com>",
    "Co-authored-by: Alice Wang <alice@example.com>",
]


def replay(plan_path: str, repo_root: str, seed: int = 42):
    with open(plan_path) as f:
        plan = json.load(f)

    rng = random.Random(seed)
    commits = plan.get("commits", [])
    total = len(commits)

    for idx, entry in enumerate(commits):
        author_date = entry.get("date", "2024-01-01 12:00:00 +0000")
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = author_date
        env["GIT_COMMITTER_DATE"] = author_date

        for change in entry.get("changes", []):
            path = os.path.join(repo_root, change["path"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(change.get("content", ""))

        subprocess.run(["git", "add", "-A"], cwd=repo_root, capture_output=True)

        msg = entry["message"]
        if rng.random() < 0.3:
            msg += "\n\n" + rng.choice(_CO_AUTHORS)

        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=repo_root, env=env, capture_output=True,
        )

        gap = _bucket(idx, total, rng)
        for _ in range(gap):
            fake_file = f".git/logs/refs/heads/_gap_touch_{idx}_{_}"
            with open(os.path.join(repo_root, fake_file), "w") as f:
                f.write(str(time.time()))
            subprocess.run(["git", "add", "-A"], cwd=repo_root, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"chore: gap touch {idx}.{_}"],
                cwd=repo_root, env=env, capture_output=True,
            )

    subprocess.run(["git", "rm", "-r", "--cached", "--ignore-unmatch", ".git/logs/refs/heads/_gap_touch_*"],
                   cwd=repo_root, capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: cleanup gap touches"],
                   cwd=repo_root, env=env, capture_output=True)

    _align_mtimes(repo_root, repo_root)


def _align_mtimes(root: str, base: str):
    """Set file mtimes to match the last commit date of each file."""
    for root_dir, _, files in os.walk(root):
        for f in files:
            filepath = os.path.join(root_dir, f)
            if os.path.islink(filepath) or ".git" in filepath:
                continue
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct", "--", os.path.relpath(filepath, base)],
                capture_output=True, text=True, cwd=base,
            )
            ts = result.stdout.strip()
            if ts and ts.isdigit():
                try:
                    os.utime(filepath, (int(ts), int(ts)))
                except (OSError, PermissionError):
                    pass


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: replay_history.py <plan.json>")
        sys.exit(1)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    replay(sys.argv[1], repo_root)


if __name__ == "__main__":
    main()
