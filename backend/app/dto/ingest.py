from typing import List, Optional

from pydantic import BaseModel


class IngestRequest(BaseModel):
    collection: str
    chunk_size: Optional[int] = 900
    overlap: Optional[int] = 120
    embed_model: Optional[str] = None  # defaults to config


class IngestResponse(BaseModel):
    indexed: int
    doc_ids: List[str]
    collection_id: str
