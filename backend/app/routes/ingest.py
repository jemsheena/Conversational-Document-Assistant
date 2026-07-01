import hashlib
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.deps import get_current_user
from app.dto.ingest import IngestResponse
from app.storage import get_pdf_storage
from rag.chunk import chunk_text
from rag.embed import get_embeddings
from rag.pdf import extract_text_from_pdf_bytes
from rag.store import get_or_create_store

router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest_documents(
    collection: str = Form(...),
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(900),
    overlap: int = Form(120),
    embed_model: str = Form(None),
    user: dict = Depends(get_current_user),
):
    """Ingest PDF files: parse, chunk, embed, index."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if not collection:
        collection = "default"

    doc_ids = []
    all_chunks = []
    all_metas = []

    embed_model_name = embed_model or settings.EMBED_MODEL
    storage = get_pdf_storage()

    for file in files:
        if not file.filename.endswith(".pdf"):
            continue

        file_hash = hashlib.sha256()
        content = await file.read()
        file_hash.update(content)
        file_hash_str = file_hash.hexdigest()

        storage.save_pdf(content, file_hash_str)
        pages = extract_text_from_pdf_bytes(content)

        chunks = []
        for page_num, page_text in enumerate(pages, 1):
            page_chunks = chunk_text(page_text, max_tokens=chunk_size, overlap=overlap)
            for chunk_text_val in page_chunks:
                chunks.append(
                    {
                        "text": chunk_text_val,
                        "page": page_num,
                        "doc": file.filename,
                        "doc_id": file_hash_str,
                    }
                )

        doc_ids.append(file_hash_str)
        all_chunks.extend([c["text"] for c in chunks])
        all_metas.extend(chunks)

    if not all_chunks:
        raise HTTPException(
            status_code=400,
            detail="No text chunks extracted from PDFs. Please check if PDFs are valid and contain text.",
        )

    try:
        print(f"📊 Embedding {len(all_chunks)} chunks...")
        embeddings = get_embeddings(all_chunks, model_name=embed_model_name)
        print(f"✅ Generated {len(embeddings)} embeddings")

        print(f"📦 Indexing in collection: {collection}")
        store = get_or_create_store(collection, dim=settings.EMBED_DIM)
        store.add(embeddings, all_metas)
        store.save()
        print(f"✅ Indexed {len(all_chunks)} chunks successfully")

        return IngestResponse(indexed=len(all_chunks), doc_ids=doc_ids, collection_id=collection)
    except Exception as e:
        import traceback

        error_msg = f"Failed to embed or index documents: {str(e)}"
        print(f"❌ Ingest error: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)
