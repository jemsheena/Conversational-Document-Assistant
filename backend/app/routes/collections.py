import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Collection

router = APIRouter()


class CollectionCreate(BaseModel):
    name: str
    visibility: str = "private"


class CollectionResponse(BaseModel):
    id: str
    name: str
    visibility: str
    created_at: str


@router.post("", response_model=CollectionResponse)
async def create_collection(
    req: CollectionCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    created_at = datetime.utcnow().isoformat()
    collection = Collection(
        id=str(uuid.uuid4()),
        name=req.name,
        owner_id=user["id"],
        visibility=req.visibility,
        created_at=created_at,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        visibility=collection.visibility,
        created_at=collection.created_at,
    )


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Collection)
        .where(Collection.owner_id == user["id"])
        .order_by(Collection.created_at.desc())
    )
    rows = db.execute(stmt).scalars().all()
    return [
        CollectionResponse(
            id=row.id,
            name=row.name,
            visibility=row.visibility,
            created_at=row.created_at,
        )
        for row in rows
    ]
