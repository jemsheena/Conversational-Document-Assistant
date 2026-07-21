from rag.utils import diversify_passages, validate_citations


def test_validate_citations_accepts_in_range_citations():
    known_sources = [
        {"doc": "report-a.pdf", "page": 1},
        {"doc": "report-b.pdf", "page": 2},
        {"doc": "report-c.pdf", "page": 3},
    ]
    answer_text = "The answer is supported by [1] and [2]."

    is_valid, cited_sources = validate_citations(answer_text, len(known_sources))

    assert is_valid is True
    assert cited_sources == [1, 2]


def test_validate_citations_flags_out_of_range_citations():
    answer_text = "This claim is unsupported and cites [5]."

    is_valid, cited_sources = validate_citations(answer_text, num_sources=3)

    assert is_valid is False
    assert cited_sources == []


def test_diversify_passages_limits_per_document_and_page():
    passages = [
        {"doc": "doc-a", "page": 1, "score": 0.95, "text": "a1"},
        {"doc": "doc-a", "page": 1, "score": 0.90, "text": "a2"},
        {"doc": "doc-a", "page": 2, "score": 0.93, "text": "a3"},
        {"doc": "doc-a", "page": 2, "score": 0.80, "text": "a4"},
        {"doc": "doc-a", "page": 3, "score": 0.70, "text": "a5"},
        {"doc": "doc-b", "page": 1, "score": 0.99, "text": "b1"},
        {"doc": "doc-b", "page": 1, "score": 0.50, "text": "b2"},
    ]

    diversified = diversify_passages(passages, max_per_doc=2, max_per_page=1)

    assert [item["text"] for item in diversified] == ["b1", "a1", "a3"]
    assert sum(1 for item in diversified if item["doc"] == "doc-a") == 2
    assert sum(1 for item in diversified if item["doc"] == "doc-b") == 1
    assert len({(item["doc"], item["page"]) for item in diversified}) == len(diversified)
