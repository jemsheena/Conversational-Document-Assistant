from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    collection: str
    query: str
    k: Optional[int] = 12
    rerank_k: Optional[int] = 6
    model: Optional[str] = None
    max_tokens: Optional[int] = 600
    conversation_id: Optional[str] = None
    citations: Optional[bool] = True


class Source(BaseModel):
    doc: str
    page: int
    score: float
    snippet: str


class ChatTokenResponse(BaseModel):
    token: str
    done: bool = False
    sources: Optional[List[Source]] = None
