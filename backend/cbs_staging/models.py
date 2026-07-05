from sqlalchemy import (
    Column, BigInteger, Integer, SmallInteger, String, DateTime, Date,
    Numeric, Text, ForeignKey, UniqueConstraint, CheckConstraint, Index, func
)
from core.database import Base


class STG_TXN_HEADER(Base):
    __tablename__ = "STG_TXN_HEADER"
    __table_args__ = (
        CheckConstraint("STG_STATUS IN ('PENDING','PICKED','POSTED','FAILED','REVERTED','HELD')", name="chk_status"),
        CheckConstraint("TXN_AMOUNT >= 0", name="chk_amount_positive"),
        CheckConstraint(
            "(TXN_TYPE = 'DEBIT' AND DEBIT_ACCOUNT_NO IS NOT NULL) OR "
            "(TXN_TYPE = 'CREDIT' AND CREDIT_ACCOUNT_NO IS NOT NULL) OR "
            "(TXN_TYPE = 'TRANSFER' AND DEBIT_ACCOUNT_NO IS NOT NULL AND CREDIT_ACCOUNT_NO IS NOT NULL)",
            name="chk_debit_or_credit",
        ),
        Index("idx_stg_header_status", STG_STATUS, postgresql_where=STG_STATUS == "PENDING"),
        Index("idx_stg_header_batch", BATCH_ID, STG_STATUS),
        Index("idx_stg_header_source", SOURCE_SYSTEM, SOURCE_REF_NO),
        Index("idx_stg_header_eod_run", EOD_BATCH_RUN_ID),
        Index("idx_stg_header_created", CREATED_TIMESTAMP),
        Index("idx_stg_header_bnpl", BNPL_CONSUMER_ID, BNPL_MERCHANT_ID),
        {"schema": "INT_STG"},
    )

    STG_HEADER_ID = Column(BigInteger, primary_key=True, autoincrement=True)
    CORRELATION_ID = Column(String(64), nullable=False, unique=True)
    BATCH_ID = Column(String(64), nullable=False, index=True)
    SOURCE_SYSTEM = Column(String(32), nullable=False, default="BNPL_PLATFORM")
    SOURCE_REF_NO = Column(String(128), nullable=False)
    SOURCE_TIMESTAMP = Column(DateTime(3), nullable=False)

    TXN_TYPE = Column(String(16), nullable=False)
    TXN_CATEGORY = Column(String(32), nullable=False)
    TXN_CODE = Column(String(16), nullable=True)
    TXN_CURRENCY = Column(String(3), nullable=False, default="LAK")
    TXN_AMOUNT = Column(Numeric(19, 4), nullable=False)
    TXN_AMOUNT_LCY = Column(Numeric(19, 4), nullable=True)
    EXCHANGE_RATE = Column(Numeric(19, 8), nullable=True)

    DEBIT_ACCOUNT_NO = Column(String(34), nullable=True)
    CREDIT_ACCOUNT_NO = Column(String(34), nullable=True)
    DEBIT_ACCOUNT_BRANCH = Column(String(8), nullable=True)
    CREDIT_ACCOUNT_BRANCH = Column(String(8), nullable=True)

    BNPL_TXN_CATEGORY = Column(String(32), nullable=True)
    BNPL_MERCHANT_ID = Column(String(32), nullable=True)
    BNPL_CONSUMER_ID = Column(String(32), nullable=True)
    BNPL_INSTALLMENT_REF = Column(String(64), nullable=True)
    BNPL_AUTH_ID = Column(String(64), nullable=True)
    MDR_RATE = Column(Numeric(5, 4), nullable=True)
    MDR_AMOUNT = Column(Numeric(19, 4), nullable=True)
    NET_SETTLEMENT_AMOUNT = Column(Numeric(19, 4), nullable=True)

    STG_STATUS = Column(String(16), nullable=False, default="PENDING")
    STG_STATUS_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())

    EOD_BATCH_RUN_ID = Column(String(64), nullable=True)
    EOD_PICKUP_TIMESTAMP = Column(DateTime(3), nullable=True)
    EOD_POSTING_TIMESTAMP = Column(DateTime(3), nullable=True)
    EOD_FAILURE_REASON = Column(String(512), nullable=True)

    RETRY_COUNT = Column(SmallInteger, nullable=False, default=0)
    MAX_RETRIES = Column(SmallInteger, nullable=False, default=3)
    HOLD_REASON = Column(String(128), nullable=True)

    CREATED_BY = Column(String(32), nullable=False, default="BNPL_INTEGRATION")
    CREATED_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())
    MODIFIED_BY = Column(String(32), nullable=True)
    MODIFIED_TIMESTAMP = Column(DateTime(3), nullable=True)


class STG_TXN_DETAIL(Base):
    __tablename__ = "STG_TXN_DETAIL"
    __table_args__ = (
        UniqueConstraint("STG_HEADER_ID", "LINE_NO", name="uq_header_line"),
        {"schema": "INT_STG"},
    )

    STG_DETAIL_ID = Column(BigInteger, primary_key=True, autoincrement=True)
    STG_HEADER_ID = Column(BigInteger, ForeignKey("INT_STG.STG_TXN_HEADER.STG_HEADER_ID"), nullable=False)
    LINE_NO = Column(SmallInteger, nullable=False)

    DETAIL_TYPE = Column(String(16), nullable=False)
    DETAIL_AMOUNT = Column(Numeric(19, 4), nullable=False)
    DETAIL_CURRENCY = Column(String(3), nullable=False, default="LAK")
    GL_ACCOUNT_CODE = Column(String(16), nullable=True)
    COST_CENTER = Column(String(16), nullable=True)
    PROFIT_CENTER = Column(String(16), nullable=True)

    NARRATIVE_LINE1 = Column(String(140), nullable=True)
    NARRATIVE_LINE2 = Column(String(140), nullable=True)
    NARRATIVE_LINE3 = Column(String(140), nullable=True)
    NARRATIVE_LINE4 = Column(String(140), nullable=True)

    FLEX_FIELD_1 = Column(String(128), nullable=True)
    FLEX_FIELD_2 = Column(String(128), nullable=True)
    FLEX_FIELD_3 = Column(String(128), nullable=True)
    FLEX_FIELD_4 = Column(String(128), nullable=True)
    FLEX_FIELD_5 = Column(String(128), nullable=True)

    CREATED_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())


class STG_TXN_CONTROL(Base):
    __tablename__ = "STG_TXN_CONTROL"
    __table_args__ = (
        CheckConstraint(
            "CONTROL_STATUS IN ('OPEN','READY_FOR_PICKUP','IN_PROGRESS','COMPLETED','PARTIAL','FAILED')",
            name="chk_control_status",
        ),
        {"schema": "INT_STG"},
    )

    BATCH_ID = Column(String(64), primary_key=True)
    SOURCE_SYSTEM = Column(String(32), nullable=False, default="BNPL_PLATFORM")

    EXPECTED_RECORD_COUNT = Column(Integer, nullable=False)
    EXPECTED_TOTAL_AMOUNT = Column(Numeric(19, 4), nullable=False)
    EXPECTED_TOTAL_AMOUNT_LCY = Column(Numeric(19, 4), nullable=True)
    EXPECTED_CURRENCY = Column(String(3), nullable=False, default="LAK")

    ACTUAL_RECORD_COUNT = Column(Integer, nullable=True)
    ACTUAL_TOTAL_AMOUNT = Column(Numeric(19, 4), nullable=True)
    ACTUAL_TOTAL_AMOUNT_LCY = Column(Numeric(19, 4), nullable=True)

    CONTROL_STATUS = Column(String(16), nullable=False, default="OPEN")
    CONTROL_STATUS_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())

    EOD_BATCH_RUN_ID = Column(String(64), nullable=True)
    EOD_START_TIMESTAMP = Column(DateTime(3), nullable=True)
    EOD_END_TIMESTAMP = Column(DateTime(3), nullable=True)

    RECONCILE_STATUS = Column(String(16), nullable=True)
    RECONCILE_DIFFERENCE = Column(Numeric(19, 4), nullable=True)
    RECONCILE_TIMESTAMP = Column(DateTime(3), nullable=True)

    CREATED_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())
    MODIFIED_TIMESTAMP = Column(DateTime(3), nullable=True)


class STG_ERROR_LOG(Base):
    __tablename__ = "STG_ERROR_LOG"
    __table_args__ = {"schema": "INT_STG"}

    ERROR_ID = Column(BigInteger, primary_key=True, autoincrement=True)
    STG_HEADER_ID = Column(BigInteger, ForeignKey("INT_STG.STG_TXN_HEADER.STG_HEADER_ID"), nullable=True)
    BATCH_ID = Column(String(64), nullable=False)
    ERROR_PHASE = Column(String(32), nullable=False)
    ERROR_CODE = Column(String(16), nullable=False)
    ERROR_SEVERITY = Column(String(8), nullable=False)
    ERROR_MESSAGE = Column(String(2000), nullable=False)
    ERROR_STACK = Column(Text, nullable=True)
    ERROR_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())
    RESOLVED_FLAG = Column(String(1), nullable=False, default="N")
    RESOLVED_TIMESTAMP = Column(DateTime(3), nullable=True)
    RESOLVED_BY = Column(String(32), nullable=True)


class STG_RECONCILE(Base):
    __tablename__ = "STG_RECONCILE"
    __table_args__ = {"schema": "INT_STG"}

    RECONCILE_DATE = Column(Date, nullable=False, primary_key=True)
    SOURCE_SYSTEM = Column(String(32), nullable=False)
    BATCH_ID = Column(String(64), nullable=False, primary_key=True)

    STAGED_COUNT = Column(Integer, nullable=False)
    STAGED_AMOUNT = Column(Numeric(19, 4), nullable=False)
    POSTED_COUNT = Column(Integer, nullable=False)
    POSTED_AMOUNT = Column(Numeric(19, 4), nullable=False)
    FAILED_COUNT = Column(Integer, nullable=False)
    FAILED_AMOUNT = Column(Numeric(19, 4), nullable=False)
    HELD_COUNT = Column(Integer, nullable=False)
    HELD_AMOUNT = Column(Numeric(19, 4), nullable=False)

    DIFFERENCE_COUNT = Column(Integer, nullable=False)
    DIFFERENCE_AMOUNT = Column(Numeric(19, 4), nullable=False)

    STATUS = Column(String(16), nullable=False)
    RECONCILE_TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())


class STG_AUDIT_TRAIL(Base):
    __tablename__ = "STG_AUDIT_TRAIL"
    __table_args__ = {"schema": "INT_STG"}

    AUDIT_ID = Column(BigInteger, primary_key=True, autoincrement=True)
    OPERATION = Column(String(16), nullable=False)
    TABLE_NAME = Column(String(32), nullable=False)
    RECORD_ID = Column(BigInteger, nullable=False)
    USER_ID = Column(String(32), nullable=False)
    TIMESTAMP = Column(DateTime(3), nullable=False, server_default=func.now())
    CLIENT_IP = Column(String(45), nullable=True)
    SESSION_ID = Column(String(128), nullable=True)
    OLD_VALUES = Column(Text, nullable=True)
    NEW_VALUES = Column(Text, nullable=True)
