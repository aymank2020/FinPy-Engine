import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_source_to_test_mapping():
    src = os.path.join(REPO_ROOT, "src", "finpy")
    tests = os.path.join(REPO_ROOT, "tests")
    source_basenames = set()
    for root, dirs, files in os.walk(src):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                source_basenames.add(f.replace(".py", ""))
    test_basenames = set()
    for f in os.listdir(tests):
        if f.startswith("test_") and f.endswith(".py"):
            test_basenames.add(f.replace("test_", "").replace(".py", ""))
    for s in source_basenames:
        assert s in test_basenames or s == "__init__" or s[0].isdigit(), f"No test for {s}"


def test_test_files_exist():
    tests = os.path.join(REPO_ROOT, "tests")
    required_tests = [
        "test_cashflow_schema.py",
        "test_instrument_schema.py",
        "test_result_schema.py",
        "test_main.py",
        "test_commands.py",
        "test_formatters.py",
        "test_human_style.py",
        "test_pyproject_consistency.py",
    ]
    for t in required_tests:
        assert os.path.isfile(os.path.join(tests, t)), f"Missing test: {t}"


def test_no_orphan_test_files():
    src = os.path.join(REPO_ROOT, "src", "finpy")
    tests = os.path.join(REPO_ROOT, "tests")
    source_basenames = set()
    for root, dirs, files in os.walk(src):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                source_basenames.add(f.replace(".py", ""))
    test_basenames = set()
    for f in os.listdir(tests):
        if f.startswith("test_") and f.endswith(".py"):
            test_basenames.add(f.replace("test_", "").replace(".py", ""))
    extra = test_basenames - source_basenames - {"accrued", "discount", "types", "errors"}
    for t in extra:
        corresponding_source = [s for s in source_basenames if s in t or t in s]
        assert corresponding_source or t in {"cli_runtime", "numerical_contract", "ci_workflow", "dockerfile_contract", "out_of_scope", "anti_similarity", "human_style", "package_layout", "pyproject_consistency", "fixture_layout", "build_repo", "build_fixtures", "replay_history", "archive_contract", "preflight", "compounding", "utils", "portfolio_schema"}, f"Potentially orphaned test: test_{t}.py"


def test_test_init_exists():
    init_path = os.path.join(REPO_ROOT, "tests", "__init__.py")
    assert os.path.isfile(init_path)


def test_conftest_exists():
    conftest_path = os.path.join(REPO_ROOT, "tests", "conftest.py")
    assert os.path.isfile(conftest_path)
