from typing import Dict, List

from sentence_transformers import CrossEncoder


class Reranker:
    """Cross-encoder reranker for retrieved passages."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Lazy load the reranker model."""
        if self.model is None:
            self.model = CrossEncoder(self.model_name)

    def rerank(self, query: str, passages: List[Dict], top_k: int = 6) -> List[Dict]:
        """
        Rerank passages by relevance to query.
        Returns top_k passages with updated scores.
        """
        if not passages:
            return []

        # Prepare pairs
        pairs = [[query, p["text"]] for p in passages]

        # Get scores
        scores = self.model.predict(pairs).tolist()

        # Combine and sort
        ranked = sorted(zip(passages, scores), key=lambda x: x[1], reverse=True)

        # Return top_k with updated scores
        return [{**passage, "score": float(score)} for passage, score in ranked[:top_k]]
