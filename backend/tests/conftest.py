import os
import tempfile
import warnings

import pytest

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
    require_db = os.getenv("REQUIRE_TEST_DB", "").lower() in {"1", "true", "yes"}
    if not require_db:
        warnings.warn(
            "PostgreSQL bootstrap is disabled for this test run. "
            "Set REQUIRE_TEST_DB=1 to require database initialization.",
            RuntimeWarning,
            stacklevel=2,
        )
        return

    import time

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


@pytest.fixture
def fake_cl100k_encoding(monkeypatch):
    class FakeEncoding:
        def encode(self, text):
            return list(text)

        def decode(self, tokens):
            return "".join(tokens)

    encoding = FakeEncoding()
    monkeypatch.setattr("rag.chunk.tiktoken.get_encoding", lambda _name: encoding)
    return encoding


@pytest.fixture
def isolated_faiss_index_dir(monkeypatch, tmp_path):
    from app.config import settings
    from rag.store import _stores

    monkeypatch.setattr(settings, "INDEX_DIR", str(tmp_path))
    _stores.clear()
    yield tmp_path
    _stores.clear()


@pytest.fixture(autouse=True)
def clear_rag_cache():
    from rag.cache import clear_cache

    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def fake_current_user():
    return {
        "id": "user_1",
        "name": "Test User",
        "email": "user@example.com",
        "role": "user",
    }


@pytest.fixture
def chat_test_client(monkeypatch, fake_current_user):
    from fastapi.testclient import TestClient

    class FakeCrossEncoder:
        def __init__(self, *args, **kwargs):
            pass

        def predict(self, pairs):
            return []

    monkeypatch.setattr("sentence_transformers.CrossEncoder", FakeCrossEncoder)

    from app.deps import get_current_user
    from app.main import app

    monkeypatch.setattr("app.main.init_database", lambda: [])

    original_overrides = app.dependency_overrides.copy()

    def override_get_current_user():
        return fake_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
