import numpy as np
import pytest

from rag.store import FaissStore, get_or_create_store


def test_add_and_query_round_trip(isolated_faiss_index_dir):
    store = FaissStore("collection-a", dim=2)
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    metas = [
        {"doc": "alpha.pdf", "page": 1, "text": "alpha"},
        {"doc": "beta.pdf", "page": 2, "text": "beta"},
    ]

    store.add(vectors, metas)
    results = store.search(np.array([1.0, 0.0], dtype=np.float32), k=2)

    assert [meta["doc"] for meta, _score in results] == ["alpha.pdf", "beta.pdf"]
    assert results[0][1] == pytest.approx(1.0, abs=1e-6)
    assert results[1][1] == pytest.approx(0.0, abs=1e-6)


def test_cosine_similarity_ranking_order_is_correct(isolated_faiss_index_dir):
    store = FaissStore("collection-b", dim=2)
    vectors = np.array(
        [
            [1.0, 0.0],
            [0.70710677, 0.70710677],
            [0.0, 1.0],
        ],
        dtype=np.float32,
    )
    metas = [
        {"doc": "east", "page": 1, "text": "east"},
        {"doc": "northeast", "page": 1, "text": "northeast"},
        {"doc": "north", "page": 1, "text": "north"},
    ]

    store.add(vectors, metas)
    results = store.search(np.array([0.9, 0.1], dtype=np.float32), k=3)

    assert [meta["doc"] for meta, _score in results] == [
        "east",
        "northeast",
        "north",
    ]
    assert results[0][1] > results[1][1] > results[2][1]


def test_per_collection_isolation_keeps_search_results_separate(isolated_faiss_index_dir):
    store_a = get_or_create_store("collection-a", dim=2)
    store_b = get_or_create_store("collection-b", dim=2)

    store_a.add(
        np.array([[1.0, 0.0]], dtype=np.float32),
        [{"doc": "alpha.pdf", "page": 1, "text": "alpha"}],
    )
    store_b.add(
        np.array([[0.0, 1.0]], dtype=np.float32),
        [{"doc": "beta.pdf", "page": 2, "text": "beta"}],
    )

    results_a = store_a.search(np.array([1.0, 0.0], dtype=np.float32), k=1)
    results_b = store_b.search(np.array([0.0, 1.0], dtype=np.float32), k=1)

    assert [meta["doc"] for meta, _score in results_a] == ["alpha.pdf"]
    assert [meta["doc"] for meta, _score in results_b] == ["beta.pdf"]
    assert store_a is not store_b
