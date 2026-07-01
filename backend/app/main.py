import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_database
from app.routes import auth, chat, collections, docs, ingest, metrics, search

app = FastAPI(
    title="Conversational Document Assistant API",
    description="RAG-powered PDF chat system with citations",
    version="1.0.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])


@app.on_event("startup")
async def startup_event():
    """Ensure PostgreSQL schema exists on startup."""
    print(f"\n{'=' * 60}")
    print(f"Starting up — database: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"{'=' * 60}\n")

    try:
        tables = init_database()
        print(f"Database tables: {tables}")
        print(f"PDF storage: {settings.STORAGE_BACKEND}")
        print("Database ready\n")
    except Exception as e:
        print(f"Database initialization failed: {e}\n")
        import traceback

        traceback.print_exc()


@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy", "service": "rag-api"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
