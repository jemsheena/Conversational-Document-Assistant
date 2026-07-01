"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-30

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "collections",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "collection_members",
        sa.Column("collection_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("permission", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("collection_id", "user_id"),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("collection_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("uri", sa.String(), nullable=False),
        sa.Column("hash", sa.String(), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("doc_id", sa.String(), nullable=False),
        sa.Column("collection_id", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("bbox", sa.String(), nullable=True),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chats",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("collection_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "retrieval_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(), nullable=True),
        sa.Column("message_id", sa.String(), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("retrieved", sa.Text(), nullable=True),
        sa.Column("reranked", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("k", sa.Integer(), nullable=True),
        sa.Column("r", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("retrieval_logs")
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("collection_members")
    op.drop_table("collections")
    op.drop_table("users")
