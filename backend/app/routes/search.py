from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.deps import get_current_user_optional
from rag.embed import get_embeddings
from rag.store import get_or_create_store

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(...),
    collection: str = Query(...),
    k: int = Query(10),
    user: dict = Depends(get_current_user_optional),
):
    """Semantic search - returns top passages without generation."""
    store = get_or_create_store(collection, dim=settings.EMBED_DIM)
    query_embed = get_embeddings([q], model_name=settings.EMBED_MODEL)[0]
    results = store.search(query_embed, k=k)

    return [
        {
            "doc": meta.get("doc", ""),
            "page": meta.get("page", 0),
            "score": float(score),
            "text": meta.get("text", ""),
        }
        for meta, score in results
    ]
