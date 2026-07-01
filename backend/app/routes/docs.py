from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Chunk, Document
from app.storage import get_pdf_storage

router = APIRouter()


@router.get("")
async def list_documents(
    collection: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List documents in a collection."""
    stmt = select(Document).where(Document.collection_id == collection)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "uri": row.uri,
            "pages": row.pages,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document and its chunks."""
    db.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
    db.execute(delete(Document).where(Document.id == doc_id))
    db.commit()

    try:
        get_pdf_storage().delete_pdf(doc_id)
    except Exception:
        pass

    return {"success": True}
