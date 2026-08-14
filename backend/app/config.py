import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # Database — PostgreSQL in production; override via DATABASE_URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://rag:rag@localhost:5433/rag",
    )

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    PDF_STORAGE_DIR: str = os.path.join(DATA_DIR, "pdfs")
    INDEX_DIR: str = os.path.join(DATA_DIR, "indices")

    # PDF storage backend: "local" (disk) or "s3" (AWS)
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET")
    S3_PREFIX: str = os.getenv("S3_PREFIX", "pdfs/")

    # Embeddings
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBED_DIM: int = 384  # MiniLM-L6-v2 dimension
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # LLM Provider (groq, openai, huggingface, local, gemini)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "llama-3.3-70b-versatile")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # Groq (fast inference with OpenAI-compatible API)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Local LLM (Ollama, LM Studio, etc.)
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")  # Ollama default
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:0.5b")  # Smallest model (~0.5GB)

    # Gemini (Google Gen AI SDK / Vertex AI)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_USE_VERTEXAI: bool = _env_bool("GEMINI_USE_VERTEXAI", False)
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    GEMINI_AGENT_MODE: bool = _env_bool("GEMINI_AGENT_MODE", True)
    GEMINI_AGENT_MAX_STEPS: int = int(os.getenv("GEMINI_AGENT_MAX_STEPS", "3"))

    # Hugging Face (free alternative)
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    # Use gpt2 as default - it's a simple model that works reliably with free inference API
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "gpt2")

    # RAG defaults
    DEFAULT_K: int = 12
    DEFAULT_RERANK_K: int = 6
    DEFAULT_CHUNK_SIZE: int = 900
    DEFAULT_CHUNK_OVERLAP: int = 120
    MIN_RETRIEVAL_SCORE: float = 0.1  # Lowered to allow more lenient answer generation

    # Vector Store Configuration
    # Options: "faiss" (local, single-instance) or "pgvector" (distributed, AlloyDB)
    VECTOR_STORE: str = os.getenv("VECTOR_STORE", "faiss")

    # Rate limits
    CHAT_RATE_LIMIT: int = 10  # requests per minute
    INGEST_MAX_SIZE_MB: int = 50

    # Daily token budget per user (cost protection)
    MAX_DAILY_TOKENS_PER_USER: int = int(os.getenv("MAX_DAILY_TOKENS_PER_USER", "1000000"))  # 1M tokens
    DAILY_TOKEN_WARNING_THRESHOLD_PERCENT: int = int(os.getenv("DAILY_TOKEN_WARNING_THRESHOLD_PERCENT", "80"))

    # Caching (Pipeline Stage 9)
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "600"))  # 10 minutes

    # Prompt limits (Pipeline Stage 6)
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "8000"))

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")


settings = Settings()

# Ensure directories exist
os.makedirs(settings.PDF_STORAGE_DIR, exist_ok=True)
os.makedirs(settings.INDEX_DIR, exist_ok=True)
