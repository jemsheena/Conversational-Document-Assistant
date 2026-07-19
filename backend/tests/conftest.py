import os
import tempfile
import time

_test_data_dir = tempfile.mkdtemp(prefix="rag-test-")

# Defaults for local dev — CI sets DATABASE_URL via workflow env (port 5432).
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("DATA_DIR", _test_data_dir)
os.environ.setdefault("DATABASE_URL", "postgresql://rag:rag@127.0.0.1:5433/rag")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ["DATA_DIR"] = _test_data_dir


def pytest_configure(config):
    """Create schema before test modules import the FastAPI app."""
    from scripts.init_db import init_db

    last_error = None
    for _ in range(15):
        try:
            init_db()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(2)

    raise RuntimeError(
        "PostgreSQL is required for tests. Start it with: docker compose up -d postgres"
    ) from last_error
