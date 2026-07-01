from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    visibility: Mapped[str] = mapped_column(String, default="private")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class CollectionMember(Base):
    __tablename__ = "collection_members"

    collection_id: Mapped[str] = mapped_column(
        String, ForeignKey("collections.id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    permission: Mapped[str] = mapped_column(String, default="viewer")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_id: Mapped[str] = mapped_column(String, ForeignKey("collections.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    uri: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="parsed")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=False)
    collection_id: Mapped[str] = mapped_column(String, ForeignKey("collections.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String, nullable=True)
    bbox: Mapped[str | None] = mapped_column(String, nullable=True)
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_id: Mapped[str] = mapped_column(String, ForeignKey("collections.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str | None] = mapped_column(String, ForeignKey("chats.id"), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String, ForeignKey("messages.id"), nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved: Mapped[str | None] = mapped_column(Text, nullable=True)
    reranked: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    k: Mapped[int | None] = mapped_column(Integer, nullable=True)
    r: Mapped[int | None] = mapped_column(Integer, nullable=True)
