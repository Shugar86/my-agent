"""Alembic migration script template."""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("agent_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255)),
        sa.Column("messages", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("username", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("role", sa.String(50), server_default="user"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "installed_skills",
        sa.Column("name", sa.String(255), primary_key=True),
        sa.Column("version", sa.String(50)),
        sa.Column("source", sa.String(500)),
        sa.Column("installed_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("labels", sa.Text()),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("metrics")
    op.drop_table("installed_skills")
    op.drop_table("users")
    op.drop_table("sessions")
