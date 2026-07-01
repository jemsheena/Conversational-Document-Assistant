import asyncio
import logging
from typing import AsyncIterator

import httpx
import openai

from app.config import settings

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


async def stream_llm_response(
    system_message: str, user_message: str, model: str = None, max_tokens: int = 600
) -> AsyncIterator[str]:
    """
    Stream LLM response tokens.
    Supports Groq, OpenAI API, Hugging Face Inference API, and Local LLMs (Ollama, LM Studio).
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        async for token in _stream_groq(system_message, user_message, model, max_tokens):
            yield token
    elif provider == "huggingface":
        async for token in _stream_huggingface(system_message, user_message, model, max_tokens):
            yield token
    elif provider == "local":
        async for token in _stream_local_llm(system_message, user_message, model, max_tokens):
            yield token
    else:
        # Default to OpenAI (or local if LOCAL_LLM_URL is set and provider is openai)
        if (
            provider == "openai"
            and settings.LOCAL_LLM_URL
            and "localhost" in settings.LOCAL_LLM_URL
        ):
            # Auto-detect local LLM if URL points to localhost
            async for token in _stream_local_llm(system_message, user_message, model, max_tokens):
                yield token
        else:
            async for token in _stream_openai(system_message, user_message, model, max_tokens):
                yield token


async def _stream_groq(
    system_message: str, user_message: str, model: str = None, max_tokens: int = 600
) -> AsyncIterator[str]:
    """Stream response from Groq API (ultra-fast inference)."""
    model = model or settings.GROQ_MODEL

    if not settings.GROQ_API_KEY:
        yield "\n\n[Error: GROQ_API_KEY not set. Set it in .env file or environment variables.\n\nGet your free API key at: https://console.groq.com/keys]"
        return

    logger.info(f"⚡ Groq Request - Model: {model}, Base URL: {settings.GROQ_BASE_URL}")
    logger.info(
        f"📝 Prompt length: {len(system_message)} chars (system) + {len(user_message)} chars (user)"
    )

    client = openai.AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            stream=True,
            temperature=0.7,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Groq Error: {type(e).__name__}: {error_msg}", exc_info=True)

        if "401" in error_msg or "authentication" in error_msg.lower():
            yield "\n\n[Error: Invalid Groq API key. Please check your GROQ_API_KEY in .env file.\n\nGet a valid key at: https://console.groq.com/keys]"
        elif "404" in error_msg or "not found" in error_msg.lower():
            yield f"\n\n[Error: Model '{model}' not found. Available Groq models:\n- llama-3.3-70b-versatile (recommended)\n- llama-3.1-70b-versatile\n- mixtral-8x7b-32768\n- gemma2-9b-it\n\nUpdate GROQ_MODEL in .env]"
        elif "rate" in error_msg.lower() or "429" in error_msg:
            yield "\n\n[Error: Rate limit exceeded. Please wait a moment and try again.]"
        else:
            yield f"\n\n[Error: {error_msg}]"


async def _stream_openai(
    system_message: str, user_message: str, model: str = None, max_tokens: int = 600
) -> AsyncIterator[str]:
    """Stream response from OpenAI API."""
    model = model or settings.DEFAULT_LLM_MODEL

    if not settings.OPENAI_API_KEY:
        yield "\n\n[Error: OPENAI_API_KEY not set. Set it in .env or use LLM_PROVIDER=groq for fast inference]"
        return

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            stream=True,
            temperature=0.7,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"


async def _stream_local_llm(
    system_message: str, user_message: str, model: str = None, max_tokens: int = 600
) -> AsyncIterator[str]:
    """Stream response from local LLM (Ollama, LM Studio, etc.) using OpenAI-compatible API."""
    model = model or settings.LOCAL_LLM_MODEL
    base_url = settings.LOCAL_LLM_URL

    logger.info(f"🖥️  Local LLM Request - Model: {model}, URL: {base_url}")
    logger.info(
        f"📝 Prompt length: {len(system_message)} chars (system) + {len(user_message)} chars (user)"
    )

    # Local LLMs typically use OpenAI-compatible API
    # No API key needed for local models
    try:
        client = openai.AsyncOpenAI(
            api_key="not-needed",  # Local LLMs don't need API keys
            base_url=base_url,
        )

        logger.info(f"🚀 Sending request to local LLM at {base_url}...")
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            stream=True,
            temperature=0.7,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Local LLM Error: {type(e).__name__}: {error_msg}", exc_info=True)

        if "Connection" in error_msg or "refused" in error_msg.lower():
            yield f"\n\n[Error: Cannot connect to local LLM at {base_url}.\n\nPlease ensure:\n1. Ollama is installed and running: https://ollama.ai\n2. Or LM Studio is running with server enabled\n3. Model '{model}' is downloaded\n4. Server is running on the configured URL]\n\nQuick start with Ollama:\n1. Install: https://ollama.ai/download\n2. Run: ollama pull {model}\n3. Ensure Ollama is running"
        else:
            yield f"\n\n[Error: {error_msg}]"


async def _stream_huggingface(
    system_message: str, user_message: str, model: str = None, max_tokens: int = 600
) -> AsyncIterator[str]:
    """Stream response from Hugging Face Inference API (free tier)."""
    model = model or settings.HUGGINGFACE_MODEL

    # Log initial request info
    logger.info(f"🤗 Hugging Face Request - Model: {model}, Provider: {settings.LLM_PROVIDER}")
    logger.info(
        f"📝 Prompt length: {len(system_message)} chars (system) + {len(user_message)} chars (user)"
    )

    # Combine system and user message
    # For GPT-2 style models, use simple concatenation
    prompt = f"{system_message}\n\n{user_message}"

    try:
        # NOTE: We intentionally avoid `huggingface_hub.AsyncInferenceClient.chat_completion()`.
        # Recent versions may route through "Inference Providers" auto-router and error with:
        # "Cannot select auto-router when using non-Hugging Face API key."
        #
        # Instead, call the classic Inference API endpoint directly.
        headers = {"Content-Type": "application/json"}
        if settings.HUGGINGFACE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_API_KEY}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }

        url = f"https://api-inference.huggingface.co/models/{model}"
        logger.info(f"🚀 Sending request to Hugging Face Inference API: {url}")
        logger.info(f"🔑 Token: {'Provided' if settings.HUGGINGFACE_API_KEY else 'Not provided'}")

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
            # HF may return 503 while loading model
            if resp.status_code >= 400:
                raise RuntimeError(f"Hugging Face API error {resp.status_code}: {resp.text[:500]}")

            data = resp.json()

        # Typical response: [{"generated_text": "..."}]
        if (
            isinstance(data, list)
            and data
            and isinstance(data[0], dict)
            and "generated_text" in data[0]
        ):
            generated_text = data[0]["generated_text"]
        # Sometimes: {"generated_text": "..."} (less common)
        elif isinstance(data, dict) and "generated_text" in data:
            generated_text = data["generated_text"]
        else:
            raise RuntimeError(f"Unexpected Hugging Face response shape: {str(data)[:500]}")

        logger.info(f"✅ Generated text length: {len(generated_text)} characters")

        # Yield word by word for streaming effect
        words = generated_text.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)

    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ Error: {error_type}: {error_msg}", exc_info=True)

        # Provide helpful error messages
        if "404" in error_msg or "not found" in error_msg.lower() or "StopIteration" in error_type:
            yield f"\n\n[Error: Model '{model}' may not be available for text generation via Inference API. Try:\n1. Check if model supports text-generation: https://huggingface.co/{model}\n2. Use a different model like 'gpt2' or 'distilgpt2' for simpler text generation\n3. Update HUGGINGFACE_MODEL in .env]\n\nNote: Some models require specific inference endpoints or may not be available on the free tier."
        elif "403" in error_msg or "permission" in error_msg.lower():
            yield "\n\n[Error: Permission denied. Your API token may need 'Inference Providers' permission. Enable it at https://huggingface.co/settings/tokens, or remove HUGGINGFACE_API_KEY from .env]"
        elif "timeout" in error_msg.lower():
            yield "\n\n[Error: Request timed out. The model may be loading. Please try again in a few moments.]"
        else:
            yield f"\n\n[Error: {error_msg}]"
