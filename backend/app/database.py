from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_user_name_column() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "name" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR"))

    from app.models import User

    db = SessionLocal()
    try:
        for user in db.query(User).all():
            if not user.name:
                user.name = user.email.split("@")[0] or "User"
        db.commit()
    finally:
        db.close()

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ALTER COLUMN name SET NOT NULL"))


def init_database() -> list[str]:
    """Create tables if they do not exist. Returns list of table names."""
    inspector = inspect(engine)
    if not inspector.has_table("collections"):
        Base.metadata.create_all(bind=engine)
    _ensure_user_name_column()
    inspector = inspect(engine)
    return inspector.get_table_names()
