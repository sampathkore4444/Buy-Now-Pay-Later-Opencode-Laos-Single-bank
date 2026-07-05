"""add complaints table for consumer complaint tracking

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.String(length=64), nullable=False),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("auth_id", sa.String(length=64), nullable=True),
        sa.Column("subject", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False, server_default=sa.text("'PORTAL'")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("assigned_to", sa.String(length=64), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id"),
        sa.ForeignKeyConstraint(["consumer_id"], ["consumers.consumer_id"], ),
        sa.ForeignKeyConstraint(["auth_id"], ["auth_requests.auth_id"], ),
    )
    op.create_index(op.f("ix_complaints_complaint_id"), "complaints", ["complaint_id"])
    op.create_index(op.f("ix_complaints_consumer_id"), "complaints", ["consumer_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_complaints_consumer_id"), table_name="complaints")
    op.drop_index(op.f("ix_complaints_complaint_id"), table_name="complaints")
    op.drop_table("complaints")
