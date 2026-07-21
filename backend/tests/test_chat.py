import json

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
