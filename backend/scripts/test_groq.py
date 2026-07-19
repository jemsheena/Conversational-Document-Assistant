"""
Quick test script to verify Groq integration
"""

import asyncio
import sys

sys.path.insert(0, ".")

from app.config import settings
from rag.generate import stream_llm_response


async def test_groq():
    print("=" * 60)
    print("Testing Groq Integration")
    print("=" * 60)
    print(f"Provider: {settings.LLM_PROVIDER}")
    print(f"Model: {settings.GROQ_MODEL}")
    print(f"API Key: {settings.GROQ_API_KEY[:20]}..." if settings.GROQ_API_KEY else "Not set")
    print("=" * 60)
    print("\nSending test query to Groq...\n")

    tokens = []
    try:
        async for token in stream_llm_response(
            system_message="You are a helpful assistant.",
            user_message="Say hello in one sentence.",
            max_tokens=50,
        ):
            tokens.append(token)
            print(token, end="", flush=True)

        print("\n")
        print("=" * 60)
        print("✅ Groq integration test successful!")
        print(f"Response length: {len(''.join(tokens))} characters")
        print("=" * 60)

    except Exception as e:
        print("\n")
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_groq())

# Made with Bob
