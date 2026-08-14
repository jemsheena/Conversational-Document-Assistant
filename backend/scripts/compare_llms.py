"""
Quick benchmark for comparing LLM providers on the same prompt.

Examples:
    py -3 backend/scripts/compare_llms.py --query "Summarize the benefits of RAG"
"""

import argparse
import asyncio
import time
from dataclasses import dataclass
from typing import List

from app.config import settings
from rag.generate import stream_llm_response


@dataclass
class BenchmarkResult:
    provider: str
    model: str
    first_token_ms: float
    total_ms: float
    token_count: int
    output_preview: str


def _model_for_provider(provider: str) -> str:
    provider = provider.lower()
    if provider == "groq":
        return settings.GROQ_MODEL
    if provider == "gemini":
        return settings.GEMINI_MODEL
    if provider == "huggingface":
        return settings.HUGGINGFACE_MODEL
    if provider == "local":
        return settings.LOCAL_LLM_MODEL
    return settings.DEFAULT_LLM_MODEL


async def _run_one(
    provider: str, query: str, system_message: str, max_tokens: int
) -> BenchmarkResult:
    original_provider = settings.LLM_PROVIDER
    settings.LLM_PROVIDER = provider
    model = _model_for_provider(provider)

    try:
        started = time.perf_counter()
        first_token_at = None
        tokens: List[str] = []

        async for token in stream_llm_response(
            system_message=system_message,
            user_message=query,
            model=model,
            max_tokens=max_tokens,
        ):
            if first_token_at is None and token:
                first_token_at = time.perf_counter()
            tokens.append(token)

        finished = time.perf_counter()
        total_ms = (finished - started) * 1000
        first_token_ms = ((first_token_at - started) * 1000) if first_token_at else total_ms
        output = "".join(tokens).strip().replace("\n", " ")

        return BenchmarkResult(
            provider=provider,
            model=model,
            first_token_ms=round(first_token_ms, 1),
            total_ms=round(total_ms, 1),
            token_count=len(tokens),
            output_preview=output[:220],
        )
    finally:
        settings.LLM_PROVIDER = original_provider


async def main():
    parser = argparse.ArgumentParser(description="Compare LLM providers on one prompt")
    parser.add_argument(
        "--providers",
        default="groq,gemini",
        help="Comma-separated providers to compare",
    )
    parser.add_argument(
        "--query",
        default="Explain retrieval augmented generation in one concise paragraph.",
        help="Prompt to benchmark",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=160,
        help="Maximum tokens per provider",
    )
    args = parser.parse_args()

    results = []
    for provider in [p.strip() for p in args.providers.split(",") if p.strip()]:
        results.append(
            await _run_one(
                provider=provider,
                query=args.query,
                system_message="You are a concise assistant.",
                max_tokens=args.max_tokens,
            )
        )

    print("\nLLM Benchmark")
    print("=" * 80)
    for result in results:
        print(f"Provider: {result.provider}")
        print(f"Model: {result.model}")
        print(f"First token: {result.first_token_ms} ms")
        print(f"Total time: {result.total_ms} ms")
        print(f"Token chunks: {result.token_count}")
        print(f"Preview: {result.output_preview}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
