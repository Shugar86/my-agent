"""Phase 3: teams, invites, usage events, workspace scoping."""

from alembic import op
import sqlalchemy as sa

revision = "004_teams"
down_revision = "003_phase2_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("plan", sa.String(32), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.String(64), nullable=False, index=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_team_members_team_user", "team_members", ["team_id", "user_id"], unique=True)

    op.create_table(
        "team_invites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("team_id", sa.String(64), nullable=False, index=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "usage_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("team_id", sa.String(64), nullable=True, index=True),
        sa.Column("user_id", sa.String(64), nullable=True, index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    with op.batch_alter_table("workflows") as batch:
        batch.add_column(sa.Column("workspace_id", sa.String(64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("workflows") as batch:
        batch.drop_column("workspace_id")
    op.drop_table("usage_events")
    op.drop_table("team_invites")
    op.drop_index("ix_team_members_team_user", "team_members")
    op.drop_table("team_members")
    op.drop_table("teams")
