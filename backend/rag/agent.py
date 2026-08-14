import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import httpx

from app.config import settings
from app.routes.metrics import metrics_store
from rag.embed import get_embeddings
from rag.rerank import Reranker
from rag.store import get_or_create_store
from rag.utils import diversify_passages

logger = logging.getLogger(__name__)

_reranker: Optional[Reranker] = None


def _get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker


@dataclass
class ToolResult:
    name: str
    result: Dict[str, Any]
    sources: List[Dict[str, Any]]


def _tool_declarations() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": "search_documents",
            "description": "Search the document corpus for relevant passages in a collection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection ID to search"},
                    "query": {"type": "string", "description": "User question or search query"},
                    "k": {"type": "integer", "description": "Number of passages to retrieve"},
                    "rerank_k": {"type": "integer", "description": "Number of passages to keep after reranking"},
                },
                "required": ["collection", "query"],
            },
        },
        {
            "type": "function",
            "name": "web_search",
            "description": "Search the public web when the document corpus is not enough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results to return"},
                },
                "required": ["query"],
            },
        },
        {
            "type": "function",
            "name": "get_metrics",
            "description": "Get application metrics such as latency, token counts, and retrieval scores.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def _tool_config() -> Any:
    from google.genai import types

    return types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode="AUTO",
            allowed_function_names=["search_documents", "web_search", "get_metrics"],
        )
    )


def _gemini_client():
    from google import genai

    if settings.GEMINI_USE_VERTEXAI:
        if not settings.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT must be set when GEMINI_USE_VERTEXAI=true")
        return genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
        )

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _format_passages(passages: List[Dict[str, Any]], prefix: str = "Source") -> str:
    blocks = []
    for i, passage in enumerate(passages, 1):
        if "url" in passage:
            source_line = f"({prefix}: {passage.get('title', 'web result')} {passage.get('url', '')})"
        else:
            source_line = f"({prefix}: {passage.get('doc', 'unknown')} p.{passage.get('page', 0)})"
        blocks.append(f"[{i}] {passage.get('text', '')}\n{source_line}")
    return "\n\n".join(blocks)


def _to_source_list(passages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sources = []
    for i, passage in enumerate(passages, 1):
        source = dict(passage)
        source["source_num"] = i
        sources.append(source)
    return sources


async def _search_documents(collection: str, query: str, k: int = 12, rerank_k: int = 6) -> ToolResult:
    store = get_or_create_store(collection or "default", dim=settings.EMBED_DIM)
    query_embed = get_embeddings([query], model_name=settings.EMBED_MODEL)[0]
    retrieved = store.search(query_embed, k=k)
    passages = [
        {
            "text": meta.get("text", ""),
            "doc": meta.get("doc", ""),
            "page": meta.get("page", 0),
            "score": float(score),
        }
        for meta, score in retrieved
    ]
    reranked = _get_reranker().rerank(query, passages, top_k=rerank_k)
    reranked = diversify_passages(reranked, max_per_doc=3, max_per_page=2)

    return ToolResult(
        name="search_documents",
        result={
            "tool": "search_documents",
            "collection": collection,
            "query": query,
            "summary": f"Retrieved {len(reranked)} relevant passages from collection '{collection}'.",
            "context": _format_passages(reranked) if reranked else "",
        },
        sources=_to_source_list(reranked),
    )


async def _web_search(query: str, max_results: int = 5) -> ToolResult:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    results: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text

    # Best-effort extraction from DuckDuckGo's HTML search page.
    for match in re.finditer(
        r'<a rel="nofollow" class="result__a" href="(?P<url>[^"]+)">(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet">(?P<snippet>.*?)</a>',
        html,
        flags=re.S,
    ):
        title = re.sub(r"<.*?>", "", match.group("title")).strip()
        snippet = re.sub(r"<.*?>", "", match.group("snippet")).strip()
        result_url = re.sub(r"&amp;", "&", match.group("url")).strip()
        results.append(
            {
                "title": title,
                "url": result_url,
                "text": f"{title}\n{snippet}\n{result_url}",
                "score": 1.0,
            }
        )
        if len(results) >= max_results:
            break

    return ToolResult(
        name="web_search",
        result={
            "tool": "web_search",
            "query": query,
            "summary": f"Found {len(results)} web results for '{query}'.",
            "context": _format_passages(results, prefix="Web"),
        },
        sources=_to_source_list(results),
    )


async def _get_metrics() -> ToolResult:
    metrics = metrics_store
    payload = {
        "latencies": metrics["latencies"],
        "token_counts": metrics["token_counts"],
        "retrieval_scores": metrics["retrieval_scores"],
    }
    return ToolResult(
        name="get_metrics",
        result={
            "tool": "get_metrics",
            "summary": "Returned current application metrics.",
            "metrics": payload,
        },
        sources=[],
    )


async def _execute_tool(name: str, args: Dict[str, Any], query: str, collection: str) -> ToolResult:
    if name == "search_documents":
        return await _search_documents(
            collection=args.get("collection") or collection or "default",
            query=args.get("query") or query,
            k=int(args.get("k") or settings.DEFAULT_K),
            rerank_k=int(args.get("rerank_k") or settings.DEFAULT_RERANK_K),
        )
    if name == "web_search":
        return await _web_search(query=args.get("query") or query, max_results=int(args.get("max_results") or 5))
    if name == "get_metrics":
        return await _get_metrics()
    raise ValueError(f"Unsupported tool: {name}")


def _extract_function_calls(parts) -> List[Any]:
    function_calls = []
    for part in parts:
        call = getattr(part, "function_call", None)
        if call is not None:
            function_calls.append(call)
    return function_calls


async def run_gemini_agent(
    *,
    query: str,
    collection: str,
    model: str,
    max_tokens: int,
    max_steps: Optional[int] = None,
) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    from google.genai import types

    client = _gemini_client()
    max_steps = max_steps or settings.GEMINI_AGENT_MAX_STEPS

    system_message = (
        "You are a grounded document assistant. Use tools when they help answer the user. "
        "If search_documents or web_search returns numbered context, cite the relevant items "
        "with bracketed numbers like [1], [2]. If no tool is needed, answer directly and briefly. "
        "Never invent citations."
    )

    tools = [types.Tool(function_declarations=_tool_declarations())]
    config = types.GenerateContentConfig(
        system_instruction=system_message,
        tools=tools,
        tool_config=_tool_config(),
        max_output_tokens=max_tokens,
        temperature=0.7,
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        f"Collection: {collection or 'default'}\n"
                        f"Question: {query}\n"
                        "Decide whether to answer directly or call a tool. Use the most relevant "
                        "tool(s) and then produce a concise grounded answer."
                    )
                )
            ],
        )
    ]

    collected_sources: List[Dict[str, Any]] = []
    final_text = ""

    for _ in range(max_steps):
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=config,
        )

        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            final_text = getattr(response, "text", "") or ""
            break

        candidate = candidates[0]
        parts = getattr(candidate.content, "parts", []) or []
        function_calls = _extract_function_calls(parts)

        if not function_calls:
            final_text = getattr(response, "text", "") or ""
            break

        contents.append(candidate.content)

        for call in function_calls:
            name = getattr(call, "name", "")
            args = getattr(call, "args", None) or getattr(call, "arguments", None) or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"value": args}

            tool_result = await _execute_tool(name, args, query=query, collection=collection)
            collected_sources.extend(tool_result.sources)

            function_response = types.Part.from_function_response(
                name=name,
                response=tool_result.result,
                id=getattr(call, "id", None),
            )
            contents.append(types.Content(role="user", parts=[function_response]))
    else:
        final_text = final_text or "I couldn't complete the tool loop within the configured step limit."

    if not final_text:
        final_text = "I couldn't produce a final answer from the available tool results."

    return final_text, collected_sources, []
