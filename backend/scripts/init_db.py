"""Initialize database schema (PostgreSQL via SQLAlchemy)."""

from app.database import init_database


def init_db() -> list[str]:
    """Create tables if they don't exist."""
    tables = init_database()
    print(f"Database initialized — tables: {tables}")
    return tables


if __name__ == "__main__":
    init_db()
