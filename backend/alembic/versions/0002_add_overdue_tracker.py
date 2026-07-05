"""add overdue_tracker table for late fee and interest tracking

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "overdue_tracker",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("auth_id", sa.String(length=64), nullable=True),
        sa.Column("overdue_date", sa.Date(), nullable=False),
        sa.Column("days_overdue", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("overdue_amount_lak", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("late_fee_charged", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("interest_charged", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("late_fee_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_fee_assessment", sa.Date(), nullable=True),
        sa.Column("last_interest_assessment", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["consumer_id"], ["consumers.consumer_id"], ),
        sa.ForeignKeyConstraint(["auth_id"], ["auth_requests.auth_id"], ),
    )
    op.create_index(op.f("ix_overdue_tracker_consumer_id"), "overdue_tracker", ["consumer_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_overdue_tracker_consumer_id"), table_name="overdue_tracker")
    op.drop_table("overdue_tracker")
