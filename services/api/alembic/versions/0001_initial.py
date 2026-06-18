"""Initial migration - all tables

Revision ID: 0001
Revises:
Create Date: 2025-06-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(), unique=True, index=True),
        sa.Column("display_name", sa.String()),
        sa.Column("email", sa.String(), unique=True),
        sa.Column("hashed_password", sa.String()),
        sa.Column("role", sa.String(), server_default="editor"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "document_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doc_id", sa.String(), index=True),
        sa.Column("user_id", sa.String(), index=True),
        sa.Column("effective_role", sa.String()),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("invited_by", sa.String(), server_default=""),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doc_id", sa.String(), unique=True, index=True),
        sa.Column("title", sa.String()),
        sa.Column("state", sa.String(), server_default="draft"),
        sa.Column("owner_id", sa.String()),
        sa.Column("anchor_statement", sa.Text()),
        sa.Column("anchor_audience", sa.Text(), server_default=""),
        sa.Column("anchor_argument", sa.Text(), server_default=""),
        sa.Column("anchor_version", sa.Integer(), server_default="1"),
        sa.Column("anchor_history", sa.Text(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "block_metas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("block_id", sa.String(), index=True),
        sa.Column("doc_id", sa.String(), index=True),
        sa.Column("tags", sa.Text(), server_default="[]"),
        sa.Column("claimant_id", sa.String(), server_default=""),
        sa.Column("drift_score", sa.Float(), server_default="0"),
        sa.Column("locked_by", sa.String(), server_default=""),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )

    op.create_table(
        "operation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("op_id", sa.String(64), unique=True, nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(128), nullable=False),
        sa.Column("doc_id", sa.String(128), nullable=False, index=True),
        sa.Column("before_state", sa.Text(), server_default=""),
        sa.Column("after_state", sa.Text(), server_default=""),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_operation_logs_doc_id", "operation_logs", ["doc_id"])
    op.create_index("ix_operation_logs_user_id", "operation_logs", ["user_id"])
    op.create_index("ix_operation_logs_action", "operation_logs", ["action"])
    op.create_index("ix_operation_logs_timestamp", "operation_logs", ["timestamp"])

    op.create_table(
        "ai_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_id", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("block_id", sa.String(128), nullable=False),
        sa.Column("doc_id", sa.String(128), nullable=False, index=True),
        sa.Column("ai_source", sa.String(256), nullable=False),
        sa.Column("ai_memory_type", sa.String(16), nullable=False, server_default="public"),
        sa.Column("old_content", sa.Text(), server_default=""),
        sa.Column("new_content", sa.Text(), server_default=""),
        sa.Column("rationale", sa.Text(), server_default=""),
        sa.Column("anchor_alignment_score", sa.Float(), server_default="0"),
        sa.Column("diff_summary", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
    )
    op.create_index("ix_ai_proposals_doc_id", "ai_proposals", ["doc_id"])
    op.create_index("ix_ai_proposals_block_id", "ai_proposals", ["block_id"])
    op.create_index("ix_ai_proposals_status", "ai_proposals", ["status"])
    op.create_index("ix_ai_proposals_ai_source", "ai_proposals", ["ai_source"])

    op.create_table(
        "ai_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doc_id", sa.String(128), nullable=False, index=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("ai_role", sa.String(128), nullable=False),
        sa.Column("rule", sa.Text(), server_default=""),
        sa.Column("memory_type", sa.String(16), nullable=False, server_default="public"),
        sa.Column("solidified", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("trigger_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_memories_doc_id", "ai_memories", ["doc_id"])
    op.create_index("ix_ai_memories_user_id", "ai_memories", ["user_id"])
    op.create_index("ix_ai_memories_memory_type", "ai_memories", ["memory_type"])

    op.create_table(
        "review_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), unique=True),
        sa.Column("doc_id", sa.String(36), nullable=False, index=True),
        sa.Column("snapshot_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snap_id", sa.String(36), unique=True),
        sa.Column("doc_id", sa.String(36), nullable=False, index=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("yjs_snapshot", sa.Text(), server_default=""),
        sa.Column("block_metas_json", sa.Text(), server_default="[]"),
        sa.Column("anchor_json", sa.Text(), server_default="{}"),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "arbitrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("arb_id", sa.String(36), unique=True),
        sa.Column("doc_id", sa.String(36), nullable=False, index=True),
        sa.Column("block_id", sa.String(36), nullable=False),
        sa.Column("conflict_type", sa.String(32), nullable=False),
        sa.Column("proposals_json", sa.Text(), server_default="[]"),
        sa.Column("ai_sources_json", sa.Text(), server_default="[]"),
        sa.Column("claimant_id", sa.String(36), server_default=""),
        sa.Column("resolution", sa.String(32), nullable=True),
        sa.Column("decider_id", sa.String(36), server_default=""),
        sa.Column("decider_reason", sa.Text(), server_default=""),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("arbitrations")
    op.drop_table("snapshots")
    op.drop_table("review_sessions")
    op.drop_index("ix_ai_memories_memory_type", table_name="ai_memories")
    op.drop_index("ix_ai_memories_user_id", table_name="ai_memories")
    op.drop_index("ix_ai_memories_doc_id", table_name="ai_memories")
    op.drop_table("ai_memories")
    op.drop_index("ix_ai_proposals_ai_source", table_name="ai_proposals")
    op.drop_index("ix_ai_proposals_status", table_name="ai_proposals")
    op.drop_index("ix_ai_proposals_block_id", table_name="ai_proposals")
    op.drop_index("ix_ai_proposals_doc_id", table_name="ai_proposals")
    op.drop_table("ai_proposals")
    op.drop_index("ix_operation_logs_timestamp", table_name="operation_logs")
    op.drop_index("ix_operation_logs_action", table_name="operation_logs")
    op.drop_index("ix_operation_logs_user_id", table_name="operation_logs")
    op.drop_index("ix_operation_logs_doc_id", table_name="operation_logs")
    op.drop_table("operation_logs")
    op.drop_table("block_metas")
    op.drop_table("documents")
    op.drop_table("document_permissions")
    op.drop_table("users")
