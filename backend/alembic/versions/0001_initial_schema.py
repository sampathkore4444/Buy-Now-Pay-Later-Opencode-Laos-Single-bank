"""initial BNPL database schema

Revision ID: 0001
Revises:
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- merchants ---
    op.create_table(
        "merchants",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=False),
        sa.Column("application_id", sa.String(length=32), nullable=False),
        sa.Column("business_name", sa.String(length=256), nullable=False),
        sa.Column("business_name_lao", sa.String(length=256), nullable=True),
        sa.Column("registration_number", sa.String(length=64), nullable=True),
        sa.Column("tax_id", sa.String(length=64), nullable=True),
        sa.Column("business_type", sa.String(length=32), nullable=False),
        sa.Column("merchant_category", sa.String(length=64), nullable=False),
        sa.Column("mcc_code", sa.String(length=8), nullable=True),
        sa.Column("owner_name", sa.String(length=128), nullable=False),
        sa.Column("owner_id_card", sa.String(length=32), nullable=False),
        sa.Column("owner_phone", sa.String(length=20), nullable=False),
        sa.Column("owner_email", sa.String(length=128), nullable=False),
        sa.Column("settlement_bank_code", sa.String(length=16), nullable=False),
        sa.Column("settlement_account_no", sa.String(length=34), nullable=False),
        sa.Column("settlement_account_name", sa.String(length=128), nullable=False),
        sa.Column("address_street", sa.String(length=256), nullable=True),
        sa.Column("address_district", sa.String(length=64), nullable=True),
        sa.Column("address_province", sa.String(length=64), nullable=True),
        sa.Column("address_gps", sa.String(length=32), nullable=True),
        sa.Column("channels", sa.String(length=256), nullable=True),
        sa.Column("estimated_monthly_volume_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("average_ticket_size_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("referral_source", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING_KYC'")),
        sa.Column("risk_tier", sa.String(length=16), nullable=False, server_default=sa.text("'GREEN'")),
        sa.Column("risk_score", sa.Integer(), nullable=True, server_default=sa.text("100")),
        sa.Column("mdr_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("settlement_terms", sa.String(length=8), nullable=False, server_default=sa.text("'T+1'")),
        sa.Column("daily_limit_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("monthly_limit_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("api_key", sa.String(length=128), nullable=True),
        sa.Column("api_secret_hash", sa.String(length=256), nullable=True),
        sa.Column("webhook_url", sa.String(length=512), nullable=True),
        sa.Column("qr_code_url", sa.String(length=512), nullable=True),
        sa.Column("kyc_status", sa.String(length=16), nullable=True),
        sa.Column("aml_check", sa.String(length=16), nullable=True),
        sa.Column("sanctions_screen", sa.String(length=16), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", sa.String(length=32), nullable=False, server_default=sa.text("'SYSTEM'")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id"),
        sa.UniqueConstraint("application_id"),
        sa.UniqueConstraint("api_key"),
    )
    op.create_index(op.f("ix_merchants_merchant_id"), "merchants", ["merchant_id"])

    # --- merchant_documents ---
    op.create_table(
        "merchant_documents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("document_url", sa.String(length=512), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=True, server_default=sa.text("FALSE")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.merchant_id"], ),
    )

    # --- merchant_users ---
    op.create_table(
        "merchant_users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False, server_default=sa.text("'ADMIN'")),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("TRUE")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.merchant_id"], ),
        sa.UniqueConstraint("email"),
    )

    # --- consumers ---
    op.create_table(
        "consumers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("bank_customer_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("id_card", sa.String(length=32), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("bnpl_limit_lak", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("available_limit_lak", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("limit_expiry", sa.Date(), nullable=True),
        sa.Column("risk_tier", sa.String(length=16), nullable=False, server_default=sa.text("'GREEN'")),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("kyc_status", sa.String(length=16), nullable=False, server_default=sa.text("'VERIFIED'")),
        sa.Column("aml_status", sa.String(length=16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("consumer_id"),
        sa.UniqueConstraint("bank_customer_id"),
    )
    op.create_index(op.f("ix_consumers_consumer_id"), "consumers", ["consumer_id"])

    # --- consumer_devices ---
    op.create_table(
        "consumer_devices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("device_type", sa.String(length=32), nullable=True),
        sa.Column("last_ip_address", sa.String(length=45), nullable=True),
        sa.Column("last_gps_location", sa.String(length=32), nullable=True),
        sa.Column("trusted", sa.Boolean(), nullable=True, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["consumer_id"], ["consumers.consumer_id"], ),
    )

    # --- auth_requests ---
    op.create_table(
        "auth_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("auth_id", sa.String(length=64), nullable=False),
        sa.Column("auth_code", sa.String(length=32), nullable=True),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=False),
        sa.Column("amount_lak", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'LAK'")),
        sa.Column("txn_type", sa.String(length=16), nullable=False, server_default=sa.text("'PURCHASE'")),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("gps_location", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'INITIATED'")),
        sa.Column("approved_amount_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("remaining_limit_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("settlement_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("repayment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mdr_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("merchant_settlement_lak", sa.Numeric(19, 4), nullable=True),
        sa.Column("reason_code", sa.String(length=32), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("auth_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirm_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timeout_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_id"),
        sa.UniqueConstraint("auth_code"),
        sa.ForeignKeyConstraint(["consumer_id"], ["consumers.consumer_id"], ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.merchant_id"], ),
    )
    op.create_index(op.f("ix_auth_requests_auth_id"), "auth_requests", ["auth_id"])
    op.create_index(op.f("ix_auth_requests_consumer_id"), "auth_requests", ["consumer_id"])
    op.create_index(op.f("ix_auth_requests_merchant_id"), "auth_requests", ["merchant_id"])

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("txn_id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("auth_id", sa.String(length=64), nullable=True),
        sa.Column("consumer_id", sa.String(length=32), nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=False),
        sa.Column("txn_type", sa.String(length=16), nullable=False),
        sa.Column("txn_category", sa.String(length=32), nullable=False),
        sa.Column("amount_lak", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'LAK'")),
        sa.Column("mdr_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("mdr_amount", sa.Numeric(19, 4), nullable=True),
        sa.Column("net_settlement_amount", sa.Numeric(19, 4), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("staging_status", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("txn_id"),
        sa.UniqueConstraint("correlation_id"),
        sa.ForeignKeyConstraint(["auth_id"], ["auth_requests.auth_id"], ),
        sa.ForeignKeyConstraint(["consumer_id"], ["consumers.consumer_id"], ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.merchant_id"], ),
    )
    op.create_index(op.f("ix_transactions_txn_id"), "transactions", ["txn_id"])
    op.create_index(op.f("ix_transactions_auth_id"), "transactions", ["auth_id"])
    op.create_index(op.f("ix_transactions_consumer_id"), "transactions", ["consumer_id"])
    op.create_index(op.f("ix_transactions_merchant_id"), "transactions", ["merchant_id"])

    # --- staging_headers ---
    op.create_table(
        "staging_headers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("stg_header_id", sa.BigInteger(), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=32), nullable=False, server_default=sa.text("'BNPL_PLATFORM'")),
        sa.Column("source_ref_no", sa.String(length=128), nullable=False),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("txn_type", sa.String(length=16), nullable=False),
        sa.Column("txn_category", sa.String(length=32), nullable=False),
        sa.Column("txn_code", sa.String(length=16), nullable=True),
        sa.Column("txn_currency", sa.String(length=3), nullable=False, server_default=sa.text("'LAK'")),
        sa.Column("txn_amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("debit_account_no", sa.String(length=34), nullable=True),
        sa.Column("credit_account_no", sa.String(length=34), nullable=True),
        sa.Column("debit_account_branch", sa.String(length=8), nullable=True),
        sa.Column("credit_account_branch", sa.String(length=8), nullable=True),
        sa.Column("bnpl_txn_category", sa.String(length=32), nullable=True),
        sa.Column("bnpl_merchant_id", sa.String(length=32), nullable=True),
        sa.Column("bnpl_consumer_id", sa.String(length=32), nullable=True),
        sa.Column("bnpl_auth_id", sa.String(length=64), nullable=True),
        sa.Column("mdr_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("mdr_amount", sa.Numeric(19, 4), nullable=True),
        sa.Column("net_settlement_amount", sa.Numeric(19, 4), nullable=True),
        sa.Column("stg_status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("eod_batch_run_id", sa.String(length=64), nullable=True),
        sa.Column("eod_pickup_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("eod_posting_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("eod_failure_reason", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("hold_reason", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("correlation_id"),
    )
    op.create_index(op.f("ix_staging_headers_batch_id"), "staging_headers", ["batch_id"])

    # --- settlement_batches ---
    op.create_table(
        "settlement_batches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=True),
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_gross", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("total_mdr", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("total_net", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id"),
    )
    op.create_index(op.f("ix_settlement_batches_batch_id"), "settlement_batches", ["batch_id"])
    op.create_index(op.f("ix_settlement_batches_merchant_id"), "settlement_batches", ["merchant_id"])

    # --- settlements ---
    op.create_table(
        "settlements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("settlement_id", sa.String(length=64), nullable=False),
        sa.Column("merchant_id", sa.String(length=32), nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=False),
        sa.Column("total_txn_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_gross_amount", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("total_mdr_amount", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("total_net_amount", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("staged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("settlement_id"),
    )
    op.create_index(op.f("ix_settlements_settlement_id"), "settlements", ["settlement_id"])
    op.create_index(op.f("ix_settlements_merchant_id"), "settlements", ["merchant_id"])

    # --- notification_logs ---
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("notification_id", sa.String(length=64), nullable=False),
        sa.Column("recipient", sa.String(length=128), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("template", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'SENT'")),
        sa.Column("reference_type", sa.String(length=32), nullable=True),
        sa.Column("reference_id", sa.String(length=64), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("notification_id"),
    )

    # --- fraud_rules ---
    op.create_table(
        "fraud_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("rule_name", sa.String(length=64), nullable=False),
        sa.Column("rule_type", sa.String(length=32), nullable=False),
        sa.Column("parameter", sa.String(length=128), nullable=False),
        sa.Column("threshold", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_name"),
    )

    # --- credit_limit_refresh_logs ---
    op.create_table(
        "credit_limit_refresh_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("total_consumers", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("limits_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'RUNNING'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("credit_limit_refresh_logs")
    op.drop_table("fraud_rules")
    op.drop_table("notification_logs")
    op.drop_table("settlements")
    op.drop_table("settlement_batches")
    op.drop_table("staging_headers")
    op.drop_table("transactions")
    op.drop_table("auth_requests")
    op.drop_table("consumer_devices")
    op.drop_table("consumers")
    op.drop_table("merchant_users")
    op.drop_table("merchant_documents")
    op.drop_table("merchants")
