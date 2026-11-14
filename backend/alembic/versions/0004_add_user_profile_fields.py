"""Add extended user profile fields (middle_initial, phone_number, birthday, gender, avatar_url, default_daily_budget).

Revision ID: 0004_add_user_profile_fields
Revises: 0003_widen_phone_column
Create Date: 2026-11-14
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_add_user_profile_fields"
down_revision: Union[str, None] = "0003_widen_phone_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = {c["name"] for c in insp.get_columns("users")}
    if "middle_initial" not in existing_cols:
        op.add_column("users", sa.Column("middle_initial", sa.String(length=16), nullable=True))
    if "phone_number" not in existing_cols:
        op.add_column("users", sa.Column("phone_number", sa.String(length=40), nullable=True))
    if "birthday" not in existing_cols:
        op.add_column("users", sa.Column("birthday", sa.String(length=40), nullable=True))
    if "gender" not in existing_cols:
        op.add_column("users", sa.Column("gender", sa.String(length=32), nullable=True))
    if "avatar_url" not in existing_cols:
        op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    if "default_daily_budget" not in existing_cols:
        op.add_column("users", sa.Column("default_daily_budget", sa.Numeric(precision=10, scale=2), server_default="3000.0", nullable=True))


def downgrade() -> None:
    op.drop_column("users", "default_daily_budget")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "gender")
    op.drop_column("users", "birthday")
    op.drop_column("users", "phone_number")
    op.drop_column("users", "middle_initial")
