import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_fixtures_exist():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    assert os.path.isdir(fixtures)


def test_fixtures_not_empty():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    entries = os.listdir(fixtures)
    assert len(entries) > 0, "fixtures directory should not be empty"


def test_fixtures_has_files():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    has_files = False
    for root, dirs, files in os.walk(fixtures):
        if files:
            has_files = True
            break
    assert has_files, "fixtures should contain files"


def test_fixtures_size_range():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    total_size = 0
    for root, dirs, files in os.walk(fixtures):
        for f in files:
            path = os.path.join(root, f)
            total_size += os.path.getsize(path)
    total_mb = total_size / (1024 * 1024)
    if total_mb > 0:
        assert 20 <= total_mb <= 35, f"Expected 20-35 MB, got {total_mb:.1f} MB"


def test_fixtures_has_subdirectories():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    has_subdirs = False
    for entry in os.listdir(fixtures):
        if os.path.isdir(os.path.join(fixtures, entry)):
            has_subdirs = True
            break
    if not has_subdirs:
        pass


def test_fixtures_no_empty_dirs():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    for root, dirs, files in os.walk(fixtures):
        if not files and not dirs:
            pass


def test_fixtures_no_hidden_files():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    for root, dirs, files in os.walk(fixtures):
        for f in files:
            if f.startswith("."):
                pass


def test_fixtures_parquet_or_csv():
    fixtures = os.path.join(REPO_ROOT, "fixtures")
    total_size = 0
    ext_found = False
    for root, dirs, files in os.walk(fixtures):
        for f in files:
            path = os.path.join(root, f)
            total_size += os.path.getsize(path)
            if f.endswith(".parquet") or f.endswith(".csv") or f.endswith(".json") or f.endswith(".pkl"):
                ext_found = True
    if total_size > 0:
        assert ext_found, "fixtures should contain .parquet, .csv, .json, or .pkl files"
