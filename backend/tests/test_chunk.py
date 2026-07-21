from app.config import settings
from rag.chunk import chunk_text


def test_chunk_handles_empty_input(fake_cl100k_encoding):
    assert chunk_text("") == []


def test_chunk_handles_short_input_without_splitting(fake_cl100k_encoding):
    text = "x" * 120

    chunks = chunk_text(text)

    assert chunks == [text]


def test_chunking_is_deterministic_and_respects_overlap(fake_cl100k_encoding):
    text = "x" * 1700

    first_run = chunk_text(text)
    second_run = chunk_text(text)

    assert first_run == second_run
    assert len(first_run) == 3
    assert [len(chunk) for chunk in first_run] == [900, 900, 140]
    assert all(len(chunk) <= settings.DEFAULT_CHUNK_SIZE for chunk in first_run)
    assert first_run[0][-settings.DEFAULT_CHUNK_OVERLAP :] == first_run[1][
        : settings.DEFAULT_CHUNK_OVERLAP
    ]
    assert first_run[1][-settings.DEFAULT_CHUNK_OVERLAP :] == first_run[2][
        : settings.DEFAULT_CHUNK_OVERLAP
    ]


def test_chunk_handles_text_without_natural_break_points(fake_cl100k_encoding):
    text = "z" * 1000

    chunks = chunk_text(text)

    assert len(chunks) == 2
    assert chunks[0] == "z" * 900
    assert chunks[1] == "z" * 220
