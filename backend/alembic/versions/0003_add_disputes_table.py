"""add disputes table for dispute tracking and cooling-off

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disputes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dispute_id", sa.String(length=64), nullable=False),
        sa.Column("auth_id", sa.String(length=64), nullable=False),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("resolution", sa.String(length=64), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(length=128), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cooling_off_cancel", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dispute_id"),
        sa.ForeignKeyConstraint(["auth_id"], ["auth_requests.auth_id"], ),
        sa.ForeignKeyConstraint(["consumer_id"], ["consumers.consumer_id"], ),
    )
    op.create_index(op.f("ix_disputes_dispute_id"), "disputes", ["dispute_id"])
    op.create_index(op.f("ix_disputes_consumer_id"), "disputes", ["consumer_id"])
    op.create_index(op.f("ix_disputes_auth_id"), "disputes", ["auth_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_disputes_auth_id"), table_name="disputes")
    op.drop_index(op.f("ix_disputes_consumer_id"), table_name="disputes")
    op.drop_index(op.f("ix_disputes_dispute_id"), table_name="disputes")
    op.drop_table("disputes")
