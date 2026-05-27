"""Unified schema: chat sessions, scheduled jobs log, feedback, user columns."""

from alembic import op
import sqlalchemy as sa

revision = "005_unified_schema"
down_revision = "004_teams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {t for t in insp.get_table_names()}

    if "chat_sessions" not in existing:
        op.create_table(
            "chat_sessions",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("source", sa.String(64), nullable=False, server_default="web"),
            sa.Column("user_id", sa.String(255), nullable=True),
            sa.Column("model", sa.String(255), nullable=True),
            sa.Column("model_config", sa.Text(), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=True),
            sa.Column("parent_session_id", sa.String(255), nullable=True),
            sa.Column("started_at", sa.Float(), nullable=False),
            sa.Column("ended_at", sa.Float(), nullable=True),
            sa.Column("end_reason", sa.String(64), nullable=True),
            sa.Column("message_count", sa.Integer(), server_default="0"),
            sa.Column("tool_call_count", sa.Integer(), server_default="0"),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("language", sa.String(16), nullable=True),
            sa.Column("cost_usd", sa.Float(), server_default="0"),
            sa.Column("input_tokens", sa.Integer(), server_default="0"),
            sa.Column("output_tokens", sa.Integer(), server_default="0"),
            sa.Column("compression_count", sa.Integer(), server_default="0"),
        )
        op.create_index("ix_chat_sessions_started", "chat_sessions", ["started_at"])

    if "chat_messages" not in existing:
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(255), sa.ForeignKey("chat_sessions.id"), nullable=False),
            sa.Column("role", sa.String(32), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("tool_call_id", sa.String(255), nullable=True),
            sa.Column("tool_calls", sa.Text(), nullable=True),
            sa.Column("tool_name", sa.String(255), nullable=True),
            sa.Column("timestamp", sa.Float(), nullable=False),
            sa.Column("finish_reason", sa.String(64), nullable=True),
        )
        op.create_index("ix_chat_messages_session", "chat_messages", ["session_id", "timestamp"])

    if "chat_state_meta" not in existing:
        op.create_table(
            "chat_state_meta",
            sa.Column("key", sa.String(255), primary_key=True),
            sa.Column("value", sa.Text(), nullable=True),
        )

    if "scheduled_jobs_log" not in existing:
        op.create_table(
            "scheduled_jobs_log",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("job_id", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("result", sa.Text(), nullable=True),
            sa.Column("status", sa.String(64), nullable=True),
            sa.Column("executed_at", sa.DateTime(), server_default=sa.func.now()),
        )

    if "feedback" not in existing:
        op.create_table(
            "feedback",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("session_id", sa.String(255), nullable=True),
            sa.Column("message_id", sa.String(255), nullable=True),
            sa.Column("query", sa.Text(), nullable=True),
            sa.Column("response", sa.Text(), nullable=True),
            sa.Column("rating", sa.Integer(), nullable=True),
            sa.Column("agent_id", sa.String(255), nullable=True),
            sa.Column("model", sa.String(255), nullable=True),
            sa.Column("tools_used", sa.Text(), nullable=True),
            sa.Column("metadata", sa.Text(), nullable=True),
            sa.Column("created_at", sa.Text(), nullable=True),
        )
        op.create_index("ix_feedback_session", "feedback", ["session_id"])
        op.create_index("ix_feedback_rating", "feedback", ["rating"])
        op.create_index("ix_feedback_created", "feedback", ["created_at"])
    user_cols = {c["name"] for c in insp.get_columns("users")}

    if "api_keys" not in user_cols:
        op.add_column("users", sa.Column("api_keys", sa.Text(), server_default="{}"))
    if "auth_provider" not in user_cols:
        op.add_column("users", sa.Column("auth_provider", sa.String(32), server_default="local"))
    if "is_active" not in user_cols:
        op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.true()))
    if "last_login" not in user_cols:
        op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))

    if bind.dialect.name == "sqlite":
        op.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chat_messages_fts USING fts5(content)
        """)
        op.execute("""
            CREATE TRIGGER IF NOT EXISTS chat_messages_fts_insert AFTER INSERT ON chat_messages BEGIN
                INSERT INTO chat_messages_fts(rowid, content) VALUES (
                    new.id,
                    COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
                );
            END
        """)
        op.execute("""
            CREATE TRIGGER IF NOT EXISTS chat_messages_fts_delete AFTER DELETE ON chat_messages BEGIN
                DELETE FROM chat_messages_fts WHERE rowid = old.id;
            END
        """)
        op.execute("""
            CREATE TRIGGER IF NOT EXISTS chat_messages_fts_update AFTER UPDATE ON chat_messages BEGIN
                DELETE FROM chat_messages_fts WHERE rowid = old.id;
                INSERT INTO chat_messages_fts(rowid, content) VALUES (
                    new.id,
                    COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
                );
            END
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS chat_messages_fts_update")
        op.execute("DROP TRIGGER IF EXISTS chat_messages_fts_delete")
        op.execute("DROP TRIGGER IF EXISTS chat_messages_fts_insert")
        op.execute("DROP TABLE IF EXISTS chat_messages_fts")

    op.drop_index("ix_feedback_created", table_name="feedback")
    op.drop_index("ix_feedback_rating", table_name="feedback")
    op.drop_index("ix_feedback_session", table_name="feedback")
    op.drop_table("feedback")
    op.drop_table("scheduled_jobs_log")
    op.drop_table("chat_state_meta")
    op.drop_index("ix_chat_messages_session", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_started", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    insp = sa.inspect(bind)
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "last_login" in user_cols:
        op.drop_column("users", "last_login")
    if "is_active" in user_cols:
        op.drop_column("users", "is_active")
    if "auth_provider" in user_cols:
        op.drop_column("users", "auth_provider")
    if "api_keys" in user_cols:
        op.drop_column("users", "api_keys")
