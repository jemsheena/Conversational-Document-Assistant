from typing import List, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
