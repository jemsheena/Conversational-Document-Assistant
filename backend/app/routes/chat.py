import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.config import settings
from app.deps import get_current_user
from app.dto.chat import ChatRequest
from app.rate_limiter import check_rate_limit, track_token_usage
from rag.agent import run_gemini_agent
from rag.cache import get_cached_retrieval, set_cached_retrieval
from rag.embed import get_embeddings
from rag.generate import stream_llm_response
from rag.prompt import build_prompt
from rag.rerank import Reranker
from rag.store import get_or_create_store
from rag.utils import diversify_passages, hash_query, validate_citations

logger = logging.getLogger(__name__)

router = APIRouter()

reranker = Reranker()


@router.post("")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """Stream chat response with SSE."""

    async def generate_stream():
        user_id = user.get("sub", "unknown")

        # Rate limit check: per-user, per-minute
        allowed, msg = check_rate_limit(user_id, limit_per_minute=settings.CHAT_RATE_LIMIT)
        if not allowed:
            logger.warning(f"⚠️  Rate limit blocked - {user_id}: {msg}")
            yield f"data: {json.dumps({'token': f'Rate limit exceeded. Max {settings.CHAT_RATE_LIMIT} requests per minute.', 'done': True})}\n\n"
            return

        logger.info(
            f"💬 Chat request - Query: {req.query[:100]}..., Collection: {req.collection}, Model: {req.model or 'default'}"
        )
        try:
            # Check cache (Pipeline Stage 9)
            query_hash = hash_query(req.query, req.collection)
            cached_passages = get_cached_retrieval(query_hash)

            if cached_passages:
                reranked = cached_passages
            else:
                # Retrieve (Pipeline Stage 5)
                if not req.collection:
                    req.collection = "default"

                store = get_or_create_store(req.collection, dim=settings.EMBED_DIM)
                query_embed = get_embeddings([req.query], model_name=settings.EMBED_MODEL)[0]
                retrieved = store.search(query_embed, k=req.k)

                if not retrieved:
                    yield f"data: {json.dumps({'token': 'No relevant sources found. Please upload documents to this collection first.', 'done': True})}\n\n"
                    return

                # Re-rank (Pipeline Stage 5)
                passages = [
                    {
                        "text": meta["text"],
                        "doc": meta.get("doc", ""),
                        "page": meta.get("page", 0),
                        "score": float(score),
                    }
                    for meta, score in retrieved
                ]
                reranked = reranker.rerank(req.query, passages, top_k=req.rerank_k)

                # Dedupe/diversify across pages/docs (Pipeline Stage 5)
                reranked = diversify_passages(reranked, max_per_doc=3, max_per_page=2)

                # Cache results
                set_cached_retrieval(query_hash, reranked)

            # Only refuse if no passages were retrieved at all
            # Let the LLM decide if it can answer based on the retrieved sources
            # The reranker scores vary by model and shouldn't be used as strict thresholds
            if not reranked:
                refusal_msg = "I couldn't find any relevant sources for this query. Please try rephrasing or upload more documents."
                yield f"data: {json.dumps({'token': refusal_msg, 'done': True})}\n\n"
                return

            # Build prompt (Pipeline Stage 6)
            system_msg, user_msg = build_prompt(
                req.query, reranked, max_context_tokens=settings.MAX_CONTEXT_TOKENS
            )

            # Stream generation (Pipeline Stage 7)
            sources = [
                {
                    "doc": r.get("doc", ""),
                    "page": r.get("page", 0),
                    "score": r.get("score", 0),
                    "snippet": r.get("text", "")[:200],
                }
                for r in reranked
            ]

            # Check if API key is configured (only required for OpenAI, not for local LLMs)
            if (
                settings.LLM_PROVIDER.lower() == "openai"
                and not settings.OPENAI_API_KEY
                and "localhost" not in settings.OPENAI_BASE_URL
            ):
                yield f"data: {json.dumps({'error': 'OPENAI_API_KEY not configured. Please set it in .env, use LLM_PROVIDER=local for local LLM, or use LLM_PROVIDER=huggingface for free alternative.', 'done': True})}\n\n"
                return

            # Select model based on provider.
            # The frontend currently sends OpenAI-style model names by default; for non-OpenAI providers
            # we should use the provider-specific configured model to avoid invalid routing errors.
            provider = settings.LLM_PROVIDER.lower()
            if provider == "huggingface":
                model = settings.HUGGINGFACE_MODEL
            elif provider == "local":
                model = settings.LOCAL_LLM_MODEL
            elif provider == "gemini":
                model = settings.GEMINI_MODEL
            else:
                model = req.model or settings.DEFAULT_LLM_MODEL

            if provider == "gemini" and settings.GEMINI_AGENT_MODE:
                final_response, sources, cited_sources = await run_gemini_agent(
                    query=req.query,
                    collection=req.collection or "default",
                    model=model,
                    max_tokens=req.max_tokens,
                    max_steps=settings.GEMINI_AGENT_MAX_STEPS,
                )

                if final_response:
                    for token in final_response.split():
                        yield f"data: {json.dumps({'token': token + ' ', 'done': False})}\n\n"

                citation_valid = True
                if sources:
                    citation_valid, cited_sources = validate_citations(final_response, len(sources))

                yield f"data: {json.dumps({'done': True, 'sources': sources, 'citation_valid': citation_valid, 'cited_sources': cited_sources})}\n\n"
                return

            full_response = ""
            async for token in stream_llm_response(
                system_msg, user_msg, model, max_tokens=req.max_tokens
            ):
                full_response += token
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            # Citation validation (Pipeline Stage 8)
            citation_valid, cited_sources = validate_citations(full_response, len(reranked))

            # Track token usage (rough estimate: 1 token ≈ 4 chars)
            tokens_in = len(system_msg + user_msg) // 4
            tokens_out = len(full_response) // 4
            usage_allowed, usage_msg, usage_stats = track_token_usage(
                user_id, tokens_in, tokens_out
            )

            if not usage_allowed:
                logger.warning(f"⚠️  Daily token limit - {user_id}: {usage_msg}")
            elif usage_msg != "OK":
                logger.warning(f"💡 {usage_msg}")

            # Final response with sources
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'citation_valid': citation_valid, 'cited_sources': cited_sources})}\n\n"

        except Exception as e:
            import traceback

            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"❌ Chat error: {error_msg}")
            print(f"Traceback: {error_trace}")
            yield f"data: {json.dumps({'error': error_msg, 'done': True})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")
