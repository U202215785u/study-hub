import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import database


@pytest.fixture(scope="session", autouse=True)
def isolated_test_database(tmp_path_factory):
    """Run backend tests against an initialized disposable database."""
    original_dir = database.DB_DIR
    original_path = database.DB_PATH
    test_dir = tmp_path_factory.mktemp("study-hub-db")
    database.DB_DIR = str(test_dir)
    database.DB_PATH = str(test_dir / "study_hub.db")
    database.init_db()
    try:
        yield
    finally:
        database.DB_DIR = original_dir
        database.DB_PATH = original_path
