"""Phase 2: workflow_state, marketplace ratings, template publish."""

from alembic import op
import sqlalchemy as sa

revision = "003_phase2_features"
down_revision = "002_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workflow_id", sa.String(64), nullable=False, index=True),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_state_wf_key", "workflow_state", ["workflow_id", "key"], unique=True)

    with op.batch_alter_table("workflow_templates") as batch:
        batch.add_column(sa.Column("author_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("rating_avg", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("published", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("created_by", sa.String(64), nullable=True))

    op.create_table(
        "template_ratings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("template_id", sa.String(64), nullable=False, index=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_template_ratings_user_tpl", "template_ratings", ["user_id", "template_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_template_ratings_user_tpl", "template_ratings")
    op.drop_table("template_ratings")
    with op.batch_alter_table("workflow_templates") as batch:
        batch.drop_column("created_by")
        batch.drop_column("published")
        batch.drop_column("rating_count")
        batch.drop_column("rating_avg")
        batch.drop_column("author_id")
    op.drop_index("ix_workflow_state_wf_key", "workflow_state")
    op.drop_table("workflow_state")
