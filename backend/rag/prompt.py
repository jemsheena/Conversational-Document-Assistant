from typing import Dict, List, Tuple

import tiktoken

SYSTEM_TEMPLATE = """You are a helpful assistant that answers questions using ONLY the provided sources.
Cite sources inline using bracketed numbers like [1], [2], etc.
Always attempt to provide a helpful answer based on the available sources, even if the match isn't perfect.
Only say you don't know if the sources truly contain no relevant information at all.
If the sources are partially relevant, use them to provide the best possible answer and note any limitations.
Never invent facts or references that aren't in the sources.
Be concise and use bullet points when listing items."""


def _count_tokens(text: str) -> int:
    """Count tokens using tiktoken (cl100k_base for GPT models)."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def build_prompt(
    question: str, passages: List[Dict], max_context_tokens: int = 8000
) -> Tuple[str, str]:
    """
    Pipeline Stage 6: Build system and user messages for grounded generation.

    Ensures prompt length stays within token budget.
    Returns (system_message, user_message).
    """
    # Number passages with source info
    numbered_context = []
    for i, passage in enumerate(passages, 1):
        doc = passage.get("doc", "unknown")
        page = passage.get("page", 0)
        text = passage.get("text", "")

        source_line = f"(Source: {doc} p.{page})"
        numbered_context.append(f"[{i}] {text}\n{source_line}")

    context_block = "\n\n".join(numbered_context)

    # Build user message
    user_message_template = f"""Context:

{{context}}

Question: {question}

Constraints: Be concise, use bullet points when listing, and include a short summary at the end.
Answer:"""

    # Check token budget
    base_tokens = _count_tokens(SYSTEM_TEMPLATE) + _count_tokens(
        user_message_template.replace("{context}", "")
    )
    available_tokens = max_context_tokens - base_tokens - 200  # Safety margin

    # Truncate context if needed
    context_tokens = _count_tokens(context_block)
    if context_tokens > available_tokens:
        # Truncate passages starting from the end (lower scores)
        truncated_context = []
        current_tokens = 0
        for passage_block in reversed(numbered_context):
            block_tokens = _count_tokens(passage_block)
            if current_tokens + block_tokens > available_tokens:
                break
            truncated_context.insert(0, passage_block)
            current_tokens += block_tokens
        context_block = "\n\n".join(truncated_context)

    user_message = user_message_template.format(context=context_block)

    return SYSTEM_TEMPLATE, user_message
