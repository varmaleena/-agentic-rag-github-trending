import sys
import os

# Add backend root directory to sys.path so tests can import app modules cleanly
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest


@pytest.fixture(autouse=True)
def history_database(monkeypatch, tmp_path):
    from app.config import settings

    monkeypatch.setattr(settings, "HISTORY_DB_PATH", str(tmp_path / "history.sqlite3"))
