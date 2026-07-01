from typing import List, Optional

import numpy as np

from app.config import settings

_embed_model = None
_embed_model_name = None


def _load_embed_model(model_name: str):
    """Lazy load embedding model."""
    global _embed_model, _embed_model_name

    if _embed_model is not None and _embed_model_name == model_name:
        return _embed_model

    if "openai" in model_name.lower() or model_name.startswith("text-embedding"):
        # Use OpenAI embeddings
        _embed_model = "openai"
    else:
        # Use Sentence-Transformers
        from sentence_transformers import SentenceTransformer

        _embed_model = SentenceTransformer(model_name)
        _embed_model_name = model_name

    return _embed_model


def get_embeddings(texts: List[str], model_name: Optional[str] = None) -> np.ndarray:
    """
    Get embeddings for a list of texts.
    Returns numpy array of shape (len(texts), embedding_dim).
    """
    model_name = model_name or settings.EMBED_MODEL
    model = _load_embed_model(model_name)

    if model == "openai":
        # Use OpenAI API
        import openai

        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set for OpenAI embeddings")

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            model=model_name if "text-embedding" in model_name else "text-embedding-3-small",
            input=texts,
        )
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings, dtype=np.float32)
    else:
        # Use Sentence-Transformers
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype(np.float32)
