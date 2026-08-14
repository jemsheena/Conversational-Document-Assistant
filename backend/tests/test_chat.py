import json
from types import SimpleNamespace

import numpy as np


def _parse_sse_events(response_text: str):
    events = []
    for line in response_text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events


def test_chat_streams_grounded_answer_and_final_sources(chat_test_client, monkeypatch):
    import app.routes.chat as chat_route

    class FakeStore:
        def search(self, query_vector, k=12):
            return [
                (
                    {"doc": "report-a.pdf", "page": 1, "text": "source one"},
                    0.94,
                ),
                (
                    {"doc": "report-b.pdf", "page": 2, "text": "source two"},
                    0.88,
                ),
            ]

    class FakeReranker:
        def rerank(self, query, passages, top_k=6):
            return passages[:top_k]

    async def fake_stream_llm_response(*args, **kwargs):
        yield "Grounded answer with [1][2]."

    monkeypatch.setattr(chat_route, "get_or_create_store", lambda *args, **kwargs: FakeStore())
    monkeypatch.setattr(
        chat_route,
        "get_embeddings",
        lambda *args, **kwargs: np.array([[1.0, 0.0]], dtype=np.float32),
    )
    monkeypatch.setattr(chat_route, "reranker", FakeReranker())
    monkeypatch.setattr(chat_route, "stream_llm_response", fake_stream_llm_response)

    response = chat_test_client.post(
        "/api/chat",
        json={
            "collection": "default",
            "query": "What does the document say?",
            "k": 2,
            "rerank_k": 2,
            "max_tokens": 32,
        },
    )

    assert response.status_code == 200

    events = _parse_sse_events(response.text)

    assert len(events) == 2
    assert events[0] == {"token": "Grounded answer with [1][2].", "done": False}
    assert events[1]["done"] is True
    assert events[1]["citation_valid"] is True
    assert events[1]["cited_sources"] == [1, 2]
    assert [source["doc"] for source in events[1]["sources"]] == [
        "report-a.pdf",
        "report-b.pdf",
    ]


def test_chat_refuses_when_no_relevant_sources(chat_test_client, monkeypatch):
    import app.routes.chat as chat_route

    class EmptyStore:
        def search(self, query_vector, k=12):
            return []

    monkeypatch.setattr(chat_route, "get_or_create_store", lambda *args, **kwargs: EmptyStore())
    monkeypatch.setattr(
        chat_route,
        "get_embeddings",
        lambda *args, **kwargs: np.array([[1.0, 0.0]], dtype=np.float32),
    )

    async def should_not_run(*args, **kwargs):
        raise AssertionError("LLM stream should not run when no sources are retrieved")

    monkeypatch.setattr(chat_route, "stream_llm_response", should_not_run)

    response = chat_test_client.post(
        "/api/chat",
        json={
            "collection": "default",
            "query": "What does the document say?",
            "k": 2,
            "rerank_k": 2,
            "max_tokens": 32,
        },
    )

    assert response.status_code == 200

    events = _parse_sse_events(response.text)

    assert len(events) == 1
    assert events[0] == {
        "token": "No relevant sources found. Please upload documents to this collection first.",
        "done": True,
    }


def test_chat_uses_gemini_default_model(chat_test_client, monkeypatch):
    import app.routes.chat as chat_route
    from app.config import settings

    class FakeStore:
        def search(self, query_vector, k=12):
            return [
                (
                    {"doc": "report-a.pdf", "page": 1, "text": "source one"},
                    0.94,
                )
            ]

    class FakeReranker:
        def rerank(self, query, passages, top_k=6):
            return passages[:top_k]

    captured = {}

    async def fake_stream_llm_response(system_message, user_message, model=None, max_tokens=600):
        captured["model"] = model
        captured["system_message"] = system_message
        captured["user_message"] = user_message
        captured["max_tokens"] = max_tokens
        yield "Gemini answer with [1]."

    monkeypatch.setattr(chat_route, "get_or_create_store", lambda *args, **kwargs: FakeStore())
    monkeypatch.setattr(
        chat_route,
        "get_embeddings",
        lambda *args, **kwargs: np.array([[1.0, 0.0]], dtype=np.float32),
    )
    monkeypatch.setattr(chat_route, "reranker", FakeReranker())
    monkeypatch.setattr(chat_route, "stream_llm_response", fake_stream_llm_response)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setattr(settings, "GEMINI_AGENT_MODE", False)

    response = chat_test_client.post(
        "/api/chat",
        json={
            "collection": "default",
            "query": "What does the document say?",
            "k": 1,
            "rerank_k": 1,
            "max_tokens": 24,
        },
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)

    assert captured["model"] == "gemini-test-model"
    assert captured["max_tokens"] == 24
    assert "Gemini answer with [1]." in events[0]["token"]
    assert events[-1]["citation_valid"] is True


def test_chat_uses_gemini_agent_mode(chat_test_client, monkeypatch):
    import app.routes.chat as chat_route
    from app.config import settings

    async def fake_run_gemini_agent(**kwargs):
        assert kwargs["query"] == "What does the document say?"
        assert kwargs["collection"] == "default"
        assert kwargs["model"] == "gemini-test-model"
        assert kwargs["max_tokens"] == 24
        return (
            "Agent answer with [1].",
            [
                {"doc": "report-a.pdf", "page": 1, "text": "source one", "score": 0.94},
            ],
            [],
        )

    monkeypatch.setattr(chat_route, "run_gemini_agent", fake_run_gemini_agent)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setattr(settings, "GEMINI_AGENT_MODE", True)

    response = chat_test_client.post(
        "/api/chat",
        json={
            "collection": "default",
            "query": "What does the document say?",
            "max_tokens": 24,
        },
    )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert any(event.get("token", "").strip() == "Agent answer with [1]." for event in events)
    assert events[-1]["citation_valid"] is True
    assert events[-1]["cited_sources"] == [1]


def test_stream_gemini_uses_system_instruction_and_streams_tokens(monkeypatch):
    from rag import generate

    captured = {}

    class FakeModels:
        async def generate_content_stream(self, model, contents, config):
            captured["model"] = model
            captured["contents"] = contents
            captured["config"] = config

            async def iterator():
                yield SimpleNamespace(text="Hello")
                yield SimpleNamespace(text=" world")

            return iterator()

    class FakeClient:
        def __init__(self):
            self.aio = SimpleNamespace(models=FakeModels())

    monkeypatch.setattr(generate, "_get_gemini_client", lambda: FakeClient())
    monkeypatch.setattr(generate.settings, "GEMINI_MODEL", "gemini-fake")
    monkeypatch.setattr(generate.settings, "GEMINI_USE_VERTEXAI", False)

    async def collect():
        chunks = []
        async for token in generate._stream_gemini(
            "You are helpful.",
            "Say hello.",
            max_tokens=42,
        ):
            chunks.append(token)
        return chunks

    import asyncio

    chunks = asyncio.run(collect())

    assert chunks == ["Hello", " world"]
    assert captured["model"] == "gemini-fake"
    assert captured["contents"] == "Say hello."
    assert captured["config"].system_instruction == "You are helpful."
    assert captured["config"].max_output_tokens == 42
