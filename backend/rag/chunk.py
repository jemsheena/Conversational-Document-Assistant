from typing import List

import tiktoken


def chunk_text(text: str, max_tokens: int = 900, overlap: int = 120) -> List[str]:
    """
    Token-aware text splitter with overlap.
    Uses tiktoken with cl100k_base encoding (GPT-4 compatible).
    """
    enc = tiktoken.get_encoding("cl100k_base")

    # Encode text to token IDs
    token_ids = enc.encode(text)

    chunks = []
    i = 0

    while i < len(token_ids):
        # Take up to max_tokens
        end_idx = min(i + max_tokens, len(token_ids))
        chunk_ids = token_ids[i:end_idx]

        # Decode back to text
        chunk_text = enc.decode(chunk_ids)
        chunks.append(chunk_text)

        # If we've reached the end, break
        if end_idx >= len(token_ids):
            break

        # Move forward by max_tokens - overlap
        i = end_idx - overlap

    return chunks


def merge_chunks_by_heading(chunks: List[str], min_tokens: int = 200) -> List[str]:
    """
    Merge small chunks that appear to be part of a larger section.
    Basic heuristic: if chunk is too small and next chunk doesn't start with heading,
    merge them.
    """
    if not chunks:
        return []

    enc = tiktoken.get_encoding("cl100k_base")
    merged = []
    current = chunks[0]

    for i in range(1, len(chunks)):
        current_tokens = len(enc.encode(current))

        # Check if current chunk is small
        if current_tokens < min_tokens:
            # Check if next chunk doesn't start with a heading pattern
            next_chunk = chunks[i]
            is_heading = next_chunk.strip().startswith(("#", "##", "###")) or any(
                next_chunk.strip().startswith(f"{n}.") for n in range(1, 10)
            )

            if not is_heading:
                # Merge
                current += "\n\n" + next_chunk
                continue

        merged.append(current)
        current = chunks[i]

    merged.append(current)
    return merged
