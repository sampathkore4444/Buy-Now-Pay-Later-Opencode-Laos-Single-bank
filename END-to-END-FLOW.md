# BNPL Platform — End-to-End Flow Documentation

> **Platform:** Single Bank-Embedded Buy Now, Pay Later for Lao PDR
> **Tech Stack:** FastAPI + PostgreSQL + Redis + Kafka + React (MUI)

---

## Table of Contents

1. [Platform Architecture](#1-platform-architecture)
2. [Core Components](#2-core-components)
3. [End-to-End Feature Flows](#3-end-to-end-feature-flows)
   - [3.1 Merchant Onboarding](#31-merchant-onboarding)
   - [3.2 Consumer Enrollment](#32-consumer-enrollment)
   - [3.3 Purchase Authorization (Real-Time)](#33-purchase-authorization-real-time)
   - [3.4 EOD Batch Settlement](#34-eod-batch-settlement)
   - [3.5 Repayment & Auto-Debit](#35-repayment--auto-debit)
   - [3.6 Refund Processing](#36-refund-processing)
   - [3.7 Dispute & Cooling-Off](#37-dispute--cooling-off)
   - [3.8 Fee Assessment](#38-fee-assessment)
   - [3.9 Credit Limit Refresh](#39-credit-limit-refresh)
   - [3.10 Fraud Rule Evaluation](#310-fraud-rule-evaluation)
   - [3.11 Notification & SMS](#311-notification--sms)
   - [3.12 Complaint Management](#312-complaint-management)
4. [Frontend-Backend Communication](#4-frontend-backend-communication)
5. [Server Operations](#5-server-operations)
6. [Development Environment Setup](#6-development-environment-setup)

---

## 1. Platform Architecture

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + MUI)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│  │ Merchant     │  │ Dashboard   │  │ EOD Monitor │  │ Reconciliation    │  │
│  │ Portal       │  │             │  │             │  │                   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │ HTTP (port 3000 → proxy /api → port 8000)
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       KONG API GATEWAY (port 8000)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Auth     │  │ Merchant │  │ Staging  │  │ Consumer │  │ Transaction   │ │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │  │ Service       │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └───────────────┘ │
│  Rate: 100/min  Rate: 200/min  Rate: 500/min  Rate: 100/min  Rate: 200/min│
└──────────────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND API (FastAPI on port 8000)                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      18 Route Modules (19 routers)                    │   │
│  │  auth | auth_admin | merchants | consumers | transactions | staging  │   │
│  │  webhooks | refunds | disputes | settlements | eod | reconciliation |   │
│  │  fees | fraud_rules | repayments | credit | notifications | complaints│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         17 Services                                   │   │
│  │  auth_service | merchant_service | consumer_service | staging_service │   │
│  │  settlement_service | dispute_service | refund_service | fee_service  │   │
│  │  risk_service | fraud_service | reconciliation_service               │   │
│  │  webhook_service | notification_service | auto_debit_service         │   │
│  │  credit_service | metrics_service                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                 6 Scheduled Tasks (APScheduler)                      │   │
│  │  22:00 ICT → EOD Batch   06:00 ICT → Auto-Debit   02:00 ICT → CR   │   │
│  │  08:00 ICT → Late Fees   01st 09:00 ICT → Interest   23:00 ICT → Stl│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   3 Kafka Consumers (Background)                      │   │
│  │  auth_consumer | notification_consumer | staging_consumer             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  PostgreSQL    │  │  PostgreSQL    │  │    Redis        │
│  bnpl_platform │  │  cbs_staging   │  │  (Cache)       │
│  (Port 5432)   │  │  (Port 5433)   │  │  (Port 6379)   │
│  ─ merchants   │  │  INT_STG schema│  │  ─ limits      │
│  ─ consumers   │  │  STG_TXN_*    │  │  ─ merchants   │
│  ─ transactions│  │  STG_CONTROL  │  │  ─ auth tokens │
│  ─ settlements │  │  STG_ERROR_LOG│  │                 │
│  ─ disputes    │  │  STG_RECONCILE│  │                 │
│  ─ fraud_rules │  │  STG_AUDIT    │  │                 │
└────────────────┘  └────────────────┘  └────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         KAFKA (Message Queue)                                │
│  Topics: bnpl-auth | bnpl-staging | bnpl-settlement | bnpl-notification     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Dual-Database Strategy

| Database | Purpose | Tables | Schema |
|----------|---------|--------|--------|
| `bnpl_platform` (Main) | BNPL product data — merchants, consumers, transactions, auth requests, settlements, disputes, fees, fraud rules, complaints | `merchants`, `consumers`, `auth_requests`, `transactions`, `settlements`, `disputes`, `complaints`, `fraud_rules`, `notification_logs`, `overdue_tracker`, `credit_limit_refresh_logs`, `merchant_documents`, `merchant_users`, `consumer_devices`, `staging_headers` | `public` (default) |
| `cbs_staging` (CBS Interface) | Staging area for CBS financial posting — the ONLY path to the bank's General Ledger. Never write directly to live GL. | `STG_TXN_HEADER`, `STG_TXN_DETAIL`, `STG_TXN_CONTROL`, `STG_ERROR_LOG`, `STG_RECONCILE`, `STG_AUDIT_TRAIL` | `INT_STG` |

### 1.3 Event-Driven Architecture (Kafka)

Kafka decouples real-time authorization from asynchronous side effects:

| Topic | Producer | Consumer(s) | Purpose |
|-------|----------|-------------|---------|
| `bnpl-auth` | `AuthService.authorize()` | `auth_consumer.py` | On auth confirmed: create Transaction + staging records + webhook + SMS. On declined: SMS notification |
| `bnpl-staging` | `StagingService.write_transaction()` | `staging_consumer.py` | Async staging write with retry and circuit breaker |
| `bnpl-settlement` | `SettlementService` | — | Settlement events (future use) |
| `bnpl-notification` | `NotificationService` | `notification_consumer.py` | SMS dispatch through bank SMS gateway or mock |

### 1.4 Scheduled Jobs (APScheduler)

All schedules run in `Asia/Vientiane` timezone (UTC+7):

| Time (ICT) | Job | Task Class | Description |
|-----------|-----|------------|-------------|
| 02:00 daily | Credit Limit Refresh | `CreditLimitRefreshTask.refresh_all()` | Preloads all active consumer limits into Redis from bank data warehouse |
| 06:00 daily | Auto-Debit Repayment | `RepaymentBatchProcessor.process()` | Processes D+30 auto-debit repayments against consumer bank accounts |
| 08:00 daily | Late Fee Assessment | `FeeBatchProcessor.process_daily_fees()` | Assesses late fees on overdue accounts past the 30-day grace period |
| 22:00 daily | EOD Batch Settlement | `EODBatchProcessor.process()` | Main EOD: picks up READY_FOR_PICKUP batches, validates, posts to GL |
| 23:00 daily | Merchant Settlement | `SettlementBatchProcessor.process()` | Creates daily settlement records for all active merchants (T+1) |
| 01st 09:00 monthly | Monthly Interest | `FeeBatchProcessor.process_monthly_interest()` | Assesses 1.5% monthly interest on balances unpaid beyond 30 days |

---

## 2. Core Components

### 2.1 Route Modules (API Endpoints)

| Router Prefix | Auth Required | Key Endpoints |
|--------------|---------------|---------------|
| `/api/v1/bnpl` | Merchant API Key | `POST /auth`, `POST /auth/confirm`, `POST /auth/cancel`, `GET /auth/{auth_id}` |
| `/api/v1/auth` | Public | `POST /login` (admin/merchant), `POST /consumer-login` (consumer) |
| `/api/v1/merchants` | Admin JWT | `POST /onboard`, `GET /`, `GET /{id}`, `PATCH /{id}`, `POST /{id}/documents` |
| `/api/v1/consumers` | Admin/Consumer JWT | `POST /enroll`, `GET /`, `GET /me`, `GET /me/limit`, `GET /{id}/limit` |
| `/api/v1/transactions` | Admin JWT | `GET /`, `GET /{txn_id}` |
| `/api/v1/staging` | Admin JWT | `POST /transactions`, `GET /transactions/{correlation_id}`, `POST /batches/{batch_id}/finalize` |
| `/api/v1/webhooks` | Admin JWT | `POST /merchants/{merchant_id}`, `GET /logs` |
| `/api/v1/refunds` | Merchant API Key | `POST /` |
| `/api/v1/disputes` | Admin/Public | `POST /initiate`, `GET /cooling-off/{consumer_id}/{auth_id}`, `POST /cooling-off/cancel`, `POST /{id}/resolve`, `GET /consumer/{consumer_id}` |
| `/api/v1/settlements` | Admin JWT | `GET /`, `GET /{id}`, `POST /{merchant_id}/create-daily` |
| `/api/v1/eod` | Admin JWT | `GET /batches`, `GET /batches/{batch_id}`, `POST /run`, `GET /status` |
| `/api/v1/reconciliation` | Admin JWT | `POST /batch`, `GET /daily-report` |
| `/api/v1/fees` | Admin JWT | `GET /overdue`, `GET /overdue/{consumer_id}`, `POST /assess-late-fees`, `POST /assess-interest` |
| `/api/v1/fraud-rules` | Admin JWT | `GET /`, `POST /`, `PUT /{rule_id}`, `DELETE /{rule_id}` |
| `/api/v1/repayments` | Admin JWT | `POST /trigger-auto-debit`, `POST /manual` |
| `/api/v1/credit` | Admin JWT | `POST /refresh`, `GET /refresh-logs` |
| `/api/v1/notifications` | Admin JWT | `GET /` |
| `/api/v1/complaints` | Admin/Public | `POST /`, `GET /`, `POST /{id}/resolve` |

### 2.2 Model Layer (SQLAlchemy ORM)

| Model | Table | Key Fields | Relationships |
|-------|-------|------------|---------------|
| `Merchant` | `merchants` | merchant_id, business_name, mdr_rate, risk_tier, settlement_terms, daily_limit_lak, api_key, status | Has many: MerchantUser, MerchantDocument, Settlement |
| `MerchantUser` | `merchant_users` | merchant_id, name, email, password_hash, role | Belongs to: Merchant |
| `MerchantDocument` | `merchant_documents` | merchant_id, doc_type, file_path, verified_at | Belongs to: Merchant |
| `Consumer` | `consumers` | consumer_id, bank_customer_id, bnpl_limit_lak, available_limit_lak, risk_tier, kyc_status | Has many: ConsumerDevice, AuthRequest, Transaction |
| `ConsumerDevice` | `consumer_devices` | consumer_id, device_fingerprint, gps_location | Belongs to: Consumer |
| `AuthRequest` | `auth_requests` | auth_id, consumer_id, merchant_id, amount_lak, status (INITIATED→PENDING→AUTHED→CONFIRMED→SETTLED/CANCELLED/FAILED), auth_code, mdr_rate | Belongs to: Consumer, Merchant |
| `Transaction` | `transactions` | txn_id, consumer_id, merchant_id, txn_type, txn_category, amount_lak, status | Belongs to: Consumer |
| `StagingHeader` | `staging_headers` | correlation_id, batch_id, source_ref_no, stg_status, stg_header_id | Links BNPL to CBS staging |
| `Settlement` | `settlements` | settlement_id, merchant_id, settlement_date, total_net_amount, status | Belongs to: Merchant |
| `NotificationLog` | `notification_logs` | notification_id, consumer_id, channel, message_type, status | — |
| `FraudRule` | `fraud_rules` | rule_id, rule_name, rule_type, rule_config (JSON), is_active, priority | — |
| `CreditLimitRefreshLog` | `credit_limit_refresh_logs` | log_id, refresh_type, records_updated, status | — |
| `OverdueTracker` | `overdue_tracker` | consumer_id, auth_id, due_date, late_fee_assessed, interest_assessed | Belongs to: Consumer, AuthRequest |
| `Dispute` | `disputes` | dispute_id, consumer_id, auth_id, reason, status (PENDING→INVESTIGATION→RESOLVED), cooling_off_cancel | Belongs to: Consumer, AuthRequest |
| `Complaint` | `complaints` | complaint_id, consumer_id, subject, description, channel, status (OPEN→RESOLVED) | Belongs to: Consumer |

### 2.3 CBS Staging Tables (INT_STG Schema)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `STG_TXN_HEADER` | Financial posting request — one row per BNPL transaction to be posted to GL | CORRELATION_ID, BATCH_ID, TXN_TYPE, TXN_AMOUNT, DEBIT/CREDIT_ACCOUNT_NO, BNPL extensions, STG_STATUS (PENDING→PICKED→POSTED→FAILED) |
| `STG_TXN_DETAIL` | Line items for a header (1:N) — principal, MDR, fees broken out | STG_HEADER_ID, LINE_NO, DETAIL_TYPE, DETAIL_AMOUNT, GL_ACCOUNT_CODE |
| `STG_TXN_CONTROL` | Batch-level control — expected vs actual counts/amounts | BATCH_ID, CONTROL_STATUS (OPEN→READY_FOR_PICKUP→IN_PROGRESS→COMPLETED/PARTIAL/FAILED) |
| `STG_ERROR_LOG` | Persistent error journal for EOD failures | STG_HEADER_ID, ERROR_PHASE, ERROR_CODE, ERROR_MESSAGE |
| `STG_RECONCILE` | Daily reconciliation register | RECONCILE_DATE, BATCH_ID, STAGED_COUNT, POSTED_COUNT, DIFFERENCE_AMOUNT, STATUS |
| `STG_AUDIT_TRAIL` | Immutable audit log (INSERT/UPDATE operations) | OPERATION, TABLE_NAME, RECORD_ID, OLD_VALUES (JSONB), NEW_VALUES (JSONB) |

---

## 3. End-to-End Feature Flows

### 3.1 Merchant Onboarding

**Purpose:** Register a new merchant to accept BNPL payments.

**Step-by-Step:**

```
Merchant Portal → POST /api/v1/merchants/onboard
     │
     ▼
MerchantService.onboard()
     │
     ├── 1. Generate merchant_id (M-YYYYMMDD-NNNNNN)
     ├── 2. Generate API key (pk_live_*) and API secret (sk_live_*)
     ├── 3. Determine MDR rate from estimated_monthly_volume + risk_tier
     │       → Tier 1 (3.5%): >500M LAK/mo
     │       → Tier 2 (4.5%): 50M-500M LAK/mo  
     │       → Tier 3 (5.5%): <50M LAK/mo
     │       → Tier 4 (6.5%): Red risk tier
     ├── 4. Assign risk tier (GREEN/YELLOW/ORANGE/RED) based on risk score
     ├── 5. Set transaction limits (daily/monthly caps)
     ├── 6. Create Merchant record in bnpl_platform.merchants
     └── 7. Return onboarding response with credentials
```

**API Request:**
```json
POST /api/v1/merchants/onboard
{
  "application_id": "APP-20260705-001",
  "business_name": "Vientiane Electronics Shop",
  "registration_number": "VTE-123456-IC",
  "tax_id": "TAX-789012",
  "merchant_category": "ELECTRONICS",
  "owner": { "name": "Somchai", "phone": "+856-20-5555-1234" },
  "settlement_account": { "bank_code": "BCEL", "account_number": "123-456-789-0" },
  "channels": ["LAOQR", "ECOMMERCE_API"],
  "estimated_monthly_volume_lak": 50000000,
  "average_ticket_size_lak": 800000
}
```

**API Response:**
```json
{
  "merchant_id": "M-20260705-987654",
  "status": "APPROVED",
  "risk_tier": "GREEN",
  "mdr_rate": 0.045,
  "settlement_terms": "T+1",
  "daily_limit_lak": 5000000,
  "monthly_limit_lak": 150000000,
  "integration": {
    "api_key": "pk_live_abc123xyz",
    "qr_code_url": "https://qr.bnpl-bank.la/M-20260705-987654"
  }
}
```

**Document Upload:** Merchants can upload KYC documents:
```
POST /api/v1/merchants/{merchant_id}/documents
  Body: multipart/form-data (file + doc_type)
  → MerchantDocument record with file_path, verified_at
```

**Frontend Pages Involved:**
- `MerchantsPage.tsx` — Table with "Onboard Merchant" dialog, status/risk tier chips
- `MerchantDetailPage.tsx` — Detail view with merchant info, limits, document upload

---

### 3.2 Consumer Enrollment

**Purpose:** Enroll a bank customer for BNPL credit.

**Step-by-Step:**

```
Admin → POST /api/v1/consumers/enroll
     │
     ▼
ConsumerService.create_consumer()
     │
     ├── 1. Check if bank_customer_id already enrolled → 409 Conflict
     ├── 2. Generate consumer_id (C-{last 6 of bank_customer_id})
     ├── 3. Set initial bnpl_limit_lak = 0 (refreshed by daily credit refresh job)
     ├── 4. Set initial available_limit_lak = 0
     ├── 5. Set risk_tier = "GREEN" (default, refined by credit refresh)
     ├── 6. Set kyc_status = "VERIFIED" (bank already KYC'd the customer)
     └── 7. Return consumer_id + initial limit
```

**Consumer-Facing Self-Service:**
```
Consumer → POST /api/v1/auth/consumer-login
  Body: { "consumer_id": "C-123456", "phone": "+856-20-5555-1234" }
  → Returns JWT with role="consumer"

Consumer → GET /api/v1/consumers/me  (Bearer: consumer JWT)
  → Returns profile: consumer_id, name, bnpl_limit_lak, available_limit_lak, risk_tier, limit_expiry

Consumer → GET /api/v1/consumers/me/limit  (Bearer: consumer JWT)
  → Returns { consumer_id, bnpl_limit_lak, available_limit_lak, limit_expiry, risk_tier }
```

---

### 3.3 Purchase Authorization (Real-Time)

**Purpose:** The core BNPL transaction — authorize a purchase in <2 seconds.

**Step-by-Step Flow:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  CHECKOUT FLOW                                                     │
│                                                                    │
│  1. Customer selects "Pay with BNPL" at merchant checkout          │
│  2. Merchant app calls POST /api/v1/bnpl/auth                     │
│                                                                    │
│  AuthService.authorize()                                           │
│  ┌────────────────────────────────────────────────────┐            │
│  │ 1. Validate merchant (exists, APPROVED, not blocked)│            │
│  │ 2. Lookup consumer in Redis cache (<50ms)          │            │
│  │    Key: bnpl:limit:{consumer_id}                   │            │
│  │ 3. Check available_limit_lak >= amount_lak         │            │
│  │ 4. Evaluate fraud rules (FraudService)             │            │
│  │    - Check rule cache in Redis                     │            │
│  │    - Evaluate rule conditions against transaction   │            │
│  │    - If any rule BLOCKs → DECLINED                 │            │
│  │ 5. Create AuthRequest (status=AUTHED)              │            │
│  │ 6. Reserve limit in Redis (decrement available)    │            │
│  │ 7. Return AuthApprovedResponse                     │            │
│  └────────────────────────────────────────────────────┘            │
│                                                                    │
│  3. Merchant confirms → POST /api/v1/bnpl/auth/confirm            │
│     AuthService.confirm()                                          │
│     ├── Change status AUTHED → CONFIRMED                          │
│     ├── Publish Kafka event "bnpl-auth" (confirmed)               │
│     └── Kafka consumer picks up:                                  │
│         ├── Create Transaction (status=CONFIRMED)                 │
│         ├── Create StagingHeader for EOD                          │
│         ├── Send webhook to merchant                              │
│         └── Send SMS to consumer                                  │
│                                                                    │
│  4. EOD batch picks up at 22:00 → posts to GL                    │
│     → Status CONFIRMED → SETTLED                                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Auth API Request:**
```json
POST /api/v1/bnpl/auth
X-API-Key: pk_live_abc123xyz
{
  "auth_id": "AUTH-20260705-001",
  "consumer_id": "C-123456",
  "merchant_id": "M-987654",
  "amount_lak": 180000,
  "currency": "LAK",
  "txn_type": "PURCHASE",
  "channel": "LAOQR",
  "device_fingerprint": "fp_a8f2...",
  "gps_location": "17.9757,102.6331"
}
```

**Auth Approved Response:**
```json
{
  "auth_id": "AUTH-20260705-001",
  "status": "AUTHED",
  "auth_code": "AUTH-ABC123",
  "approved_amount_lak": 180000,
  "remaining_limit_lak": 140000,
  "settlement_date": "2026-07-06",
  "repayment_date": "2026-08-04",
  "mdr_rate": 0.045,
  "merchant_settlement_lak": 171900,
  "timestamp": "2026-07-05T14:23:11.000Z",
  "late_fee_disclosure": "Late fee of 15,000 LAK applies if not paid within 30-day period",
  "total_cost_due": 180000,
  "due_date_display": "04 Aug 2026"
}
```

**Auth Declined Response:**
```json
{
  "auth_id": "AUTH-20260705-001",
  "status": "DECLINED",
  "reason_code": "INSUFFICIENT_LIMIT",
  "message": "Available BNPL limit (140,000 LAK) is less than transaction amount (180,000 LAK)."
}
```

**Authorization State Machine:**

```
INITIATED ──► PENDING ──► AUTHED ──► CONFIRMED ──► SETTLED
                │                      │
                ▼                      ▼
              FAILED              CANCELLED
```

| State Transition | Trigger | Timeout |
|-----------------|---------|---------|
| INITIATED → PENDING | Checkout request received | 5 minutes |
| PENDING → AUTHED | Risk & fraud check passed | 10 seconds |
| PENDING → FAILED | Insufficient limit, fraud block, merchant issue | — |
| AUTHED → CONFIRMED | Merchant confirms transaction | 30 minutes |
| AUTHED → CANCELLED | Timeout or manual cancel | 30 minutes |
| CONFIRMED → SETTLED | EOD batch posts to GL | ~24 hours |
| CONFIRMED → FAILED | EOD validation failure | — |

---

### 3.4 EOD Batch Settlement

**Purpose:** The end-of-day batch process that takes staged transactions and posts them to the bank's General Ledger.

**7-Step Flow (implemented in `EODBatchProcessor`):**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  EOD BATCH PROCESSOR — triggered daily at 22:00 ICT (APScheduler)       │
│  or manually via POST /api/v1/eod/run                                   │
└──────────────────────────────────────────────────────────────────────────┘

Step 1: Generate EOD_BATCH_RUN_ID = "EOD_YYYYMMDD_HHMMSS_<microsecond>"

Step 2: Acquire PostgreSQL advisory lock (lock key=12345)
        → Prevents concurrent EOD instances (race condition protection)
        → If lock fails → return SKIPPED

Step 3: Detect & recover crashed runs
        → Find IN_PROGRESS controls with EOD_START_TIMESTAMP > 6 hours ago
        → Reset PICKED headers to PENDING
        → Reset control to READY_FOR_PICKUP

Step 4: Find READY_FOR_PICKUP batches
        → Batches with CONTROL_STATUS = 'READY_FOR_PICKUP'
        → With 15-minute grace period (CREATED_TIMESTAMP < NOW - 15min)
        → Uses SELECT FOR UPDATE SKIP LOCKED

Step 5: For each batch:
        ├── Update control to IN_PROGRESS
        ├── Pick all PENDING headers → PICKED
        ├── For each picked record:
        │   ├── Validate (accounts exist, amount > 0)
        │   ├── Post to live GL (update AuthRequest status to SETTLED)
        │   ├── On success: mark POSTED
        │   └── On failure: mark FAILED + log to STG_ERROR_LOG
        ├── Update control with actual counts/amounts
        └── Insert into STG_RECONCILE

Step 6: Release advisory lock

Step 7: Return summary { batches_found, batches_processed, eod_batch_run_id }
```

**Staging Write API (pre-EOD):**
```
POST /api/v1/staging/transactions
  → Creates records in STG_TXN_HEADER + STG_TXN_DETAIL (1:N)
  → Idempotent: deduplicates by SOURCE_REF_NO
  → Returns correlation_id, stg_header_id, status="PENDING"

POST /api/v1/staging/batches/{batch_id}/finalize
  → Updates STG_TXN_CONTROL to READY_FOR_PICKUP
  → Sets expected_record_count and expected_total_amount
  → This signals to EOD that the batch is ready
```

**EOD Monitoring (Frontend):**
- `EodPage.tsx` — Status cards (in progress / pending / completed / failed), batch table, "Trigger EOD" button
- `ReconciliationPage.tsx` — Batch reconciliation form and daily report viewer

---

### 3.5 Repayment & Auto-Debit

**Purpose:** Collect repayment from consumers on D+30.

**Auto-Debit Flow (scheduled at 06:00 ICT):**

```
RepaymentBatchProcessor.process()
     │
     ▼
AutoDebitService.process_daily_repayments()
     │
     ├── 1. Find all SETTLED transactions due for repayment today
     │        (auth.created_at + 30 days == today)
     ├── 2. For each due consumer:
     │       ├── Check bank account balance (via BankAdapter)
     │       ├── If sufficient: create debit Transaction (DEBIT, BNPL_REPAYMENT)
     │       ├── Create staging records for CBS (BNPL_REPAYMENT posting)
     │       ├── Increase consumer's available_limit_lak
     │       ├── Send SMS notification
     │       └── If insufficient: mark as overdue → FeeService handles late fees
     └── 3. Return { total_due, processed, failed, skipped }
```

**Manual Repayment (Admin):**
```
POST /api/v1/repayments/manual
  Body: { "consumer_id": "C-123456", "amount_lak": 50000 }
  → Creates manual debit transaction
  → Writes to staging for CBS posting
  → Restores available limit
  → Marks overdue fees as repaid if fully cleared
```

**Manual Trigger:**
```
POST /api/v1/repayments/trigger-auto-debit
  → Runs the same process as the scheduled 06:00 job but on-demand
```

**Frontend:** `OverdueTrackerPage.tsx` — Overdue list with "Assess Late Fees" / "Assess Interest" buttons

---

### 3.6 Refund Processing

**Purpose:** Merchant-initiated refund within 30 days.

**Step-by-Step:**

```
Merchant → POST /api/v1/refunds (X-API-Key: merchant's key)
  Body: { "auth_id": "AUTH-20260705-001", "reason": "Customer returned item", "amount_lak": 180000 }
     │
     ▼
RefundService.process_refund()
     │
     ├── 1. Validate: auth_id exists, belongs to this merchant (from API key)
     ├── 2. Validate: auth status is SETTLED
     ├── 3. Validate: within 30-day refund window
     ├── 4. Calculate MDR reversal amount
     ├── 5. Create reversal staging records:
     │       ├── Debit merchant account (or hold from future settlement)
     │       ├── Credit consumer BNPL account (restores available limit)
     │       └── Reverse MDR accrual
     ├── 6. Create Transaction record (REFUND type)
     ├── 7. Update auth status → REFUNDED
     └── 8. Return { refund_id, auth_id, amount_lak, status: "REFUNDED" }
```

---

### 3.7 Dispute & Cooling-Off

**Purpose:** Consumer protection — 3-day cooling-off for transactions >1,000,000 LAK, plus general dispute handling.

**Cooling-Off Flow (per spec §12.5):**

```
Consumer → GET /api/v1/disputes/cooling-off/{consumer_id}/{auth_id}
  → Checks:
    1. Auth amount >= 1,000,000 LAK (COOLING_OFF_THRESHOLD_LAK)
    2. Auth status is CONFIRMED
    3. Within 3 days of auth creation (COOLING_OFF_DAYS)
  → Returns { eligible, reason, cooling_off_expiry, days_remaining }

Consumer → POST /api/v1/disputes/cooling-off/cancel
  Body: { "consumer_id": "C-123456", "auth_id": "AUTH-20260705-001" }
  → Cancels the auth (status → CANCELLED)
  → Restores consumer's available_limit_lak in Redis and DB
  → Creates Dispute record with cooling_off_cancel=True
  → Returns { dispute_id, status: "CANCELLED" }
```

**Dispute Flow:**

```
Consumer → POST /api/v1/disputes/initiate
  Body: { "consumer_id": "C-123456", "auth_id": "AUTH-20260705-001", "reason": "FRAUD", "description": "I did not make this purchase" }
  → Creates Dispute record (status=PENDING, investigation_until=NOW+7days)
  → Returns { dispute_id, message: "Investigation will be completed within 7 days" }

Admin → POST /api/v1/disputes/{dispute_id}/resolve
  Body: { "resolution": "REFUND_ISSUED", "investigation_notes": "Confirmed fraudulent, refund processed" }
  → Sets status=RESOLVED, resolution, resolved_at
  → If resolution is REFUND_ISSUED, triggers refund flow
```

**Frontend:** Dispute management is handled via the backend API; the merchant portal focuses on fraud rules and complaints.

---

### 3.8 Fee Assessment

**Purpose:** Assess late fees and interest on overdue accounts.

**Late Fee Assessment (daily at 08:00 ICT):**

```
FeeBatchProcessor.process_daily_fees()
     │
     ▼
FeeService.assess_late_fees()
     │
     ├── 1. Find all CONFIRMED/SETTLED auths where:
     │       - repayment_date + 3-day grace period has passed
     │       - no corresponding REPAID transaction found
     ├── 2. For each overdue consumer:
     │       - Check if already has an OverdueTracker record
     │       - If late_fee_count < MAX (5), assess fee:
     │         → Flat fee: 15,000 LAK (LATE_FEE_FLAT_LAK)
     │         → Create OverdueTracker entry
     │         → Create late fee staging records for CBS
     │         → Increment late_fee_count
     └── 3. Return { total_assessed, total_amount, details }
```

**Monthly Interest Assessment (1st of month at 09:00 ICT):**

```
FeeService.assess_interest()
     │
     ├── 1. Find all overdue auths where balance unpaid > 30 days
     ├── 2. Assess 1.5% monthly interest (INTEREST_MONTHLY_RATE)
     ├── 3. Compound every 30 days (INTEREST_COMPOUND_DAYS)
     ├── 4. Create interest staging records for CBS
     └── 5. Return summary
```

**Admin API triggers:**
```
POST /api/v1/fees/assess-late-fees  → runs same process on-demand
POST /api/v1/fees/assess-interest   → runs same process on-demand
GET /api/v1/fees/overdue            → list all overdue trackers
GET /api/v1/fees/overdue/{consumer_id} → get specific consumer's overdue info
```

**Frontend:** `OverdueTrackerPage.tsx`

---

### 3.9 Credit Limit Refresh

**Purpose:** Daily refresh of consumer BNPL limits from bank data warehouse.

**Step-by-Step:**

```
CreditLimitRefreshTask.refresh_all()  (scheduled at 02:00 ICT)
     │
     ▼
     ├── 1. Query all active consumers (is_active=True)
     ├── 2. For each consumer:
     │       ├── Call CreditService.preload_limit_to_redis()
     │       ├── Calculate limit based on bank data profile
     │       │     (salary, deposit history, transaction behavior, existing loans)
     │       ├── Update bnpl_limit_lak and available_limit_lak in DB
     │       └── Set Redis key: bnpl:limit:{consumer_id}
     │           → { bnpl_limit_lak, available_limit_lak, limit_expiry, risk_tier }
     ├── 3. Log to CreditLimitRefreshLog
     └── 4. Return { total, updated, status }
```

**Admin API:**
```
POST /api/v1/credit/refresh  → on-demand refresh
GET /api/v1/credit/refresh-logs → view refresh history
```

**Frontend:** `CreditRefreshLogsPage.tsx`

---

### 3.10 Fraud Rule Evaluation

**Purpose:** Real-time fraud detection during authorization.

**Rule Configuration:**

Fraud rules are stored in `fraud_rules` table with configurable conditions:

| Rule Type | Description | Example Config |
|-----------|-------------|----------------|
| `BLOCK_MERCHANT` | Block all transactions from a merchant | `{ "merchant_id": "M-BAD-001" }` |
| `BLOCK_CONSUMER` | Block all transactions from a consumer | `{ "consumer_id": "C-FRAUD-001" }` |
| `MAX_AMOUNT` | Block transactions above threshold | `{ "max_amount_lak": 5000000 }` |
| `VELOCITY_CHECK` | Block >N transactions in M minutes | `{ "max_txns": 5, "window_minutes": 10 }` |
| `DEVICE_BLOCK` | Block specific device fingerprint | `{ "fingerprint": "fp_bad_device" }` |

**Evaluation Flow (during AuthService.authorize()):**

```
FraudService.evaluate(consumer_id, merchant_id, amount_lak, device_fingerprint)
     │
     ├── 1. Load active fraud rules from Redis cache (bnpl:fraud:rules)
     │       (cache refreshed on rules CRUD)
     ├── 2. Sort by priority (highest first)
     ├── 3. For each rule:
     │       ├── Parse rule_config JSON
     │       ├── Evaluate condition against transaction data
     │       ├── If condition matches:
     │       │   ├── If action=BLOCK → return BLOCKED
     │       │   └── If action=FLAG → add to warnings list
     │       └── If rule has expiry, skip if expired
     └── 4. Return { decision: "ALLOW" | "BLOCK", warnings: [...] }
```

**Admin CRUD:**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/fraud-rules` | List all rules (sorted by priority) |
| `POST /api/v1/fraud-rules` | Create new rule |
| `PUT /api/v1/fraud-rules/{rule_id}` | Update rule (toggle active, change priority) |
| `DELETE /api/v1/fraud-rules/{rule_id}` | Soft-delete rule |

**Frontend:** `FraudRulesPage.tsx` — Full CRUD table with add/edit dialog, toggle switch, priority ordering.

---

### 3.11 Notification & SMS

**Purpose:** Send SMS notifications to consumers and webhook events to merchants.

**Notification Service:**

The service supports these notification types:
- `BNPL_ENROLLMENT_CONFIRM` — "You are now enrolled in BNPL. Your limit: {limit} LAK"
- `AUTH_APPROVED` — "BNPL purchase of {amount} LAK at {merchant} approved. Due: {date}"
- `AUTH_DECLINED` — "BNPL purchase declined: {reason}"
- `REPAYMENT_SUCCESS` — "BNPL repayment of {amount} LAK successful. Limit restored."
- `PAYMENT_DUE_REMINDER` — "Reminder: BNPL payment of {amount} due on {date}"
- `LATE_FEE_ASSESSED` — "Late fee of {amount} LAK applied. Pay now to avoid interest."

**Flow:**

```
Any service → NotificationService.send_notification(consumer_id, message_type, params)
     │
     ├── 1. Template message with params
     ├── 2. Create NotificationLog record
     ├── 3. Publish Kafka event to "bnpl-notification" topic
     └── 4. notification_consumer.py picks up:
           ├── Try: send via SMS API (configured SMS_API_URL + SMS_API_KEY)
           └── Fallback: log to console (development mode)
```

**API:**
```
GET /api/v1/notifications?page=1&page_size=20&channel=SMS&status=SENT
  → Paginated list of notification logs with channel/status filters
```

**Frontend:** `NotificationLogsPage.tsx` — Notification log viewer with channel filter.

---

### 3.12 Complaint Management

**Purpose:** Consumer complaint tracking and resolution.

**Flow:**

```
Consumer/Admin → POST /api/v1/complaints
  Body: { "consumer_id": "C-123456", "subject": "Late fee disputed", 
          "description": "I paid on time but was charged a late fee", "channel": "PORTAL" }
  → Creates Complaint record (status=OPEN)
  → Returns { complaint_id, status: "OPEN" }

Admin → POST /api/v1/complaints/{complaint_id}/resolve
  Body: { "resolution": "Late fee waived as one-time courtesy" }
  → Sets status=RESOLVED, resolution, resolved_at

Admin → GET /api/v1/complaints?status=OPEN&page=1
  → Paginated list of complaints with status filter
```

**Frontend:** `ComplaintsPage.tsx` — Complaints list with filter tabs (Open / Resolved / All) and resolve dialog.

---

## 4. Frontend-Backend Communication

### 4.1 API Client Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + MUI)                            │
│                                                                      │
│  Every API call goes through: apiClient (Axios instance)             │
│                                                                      │
│  apiClient = axios.create({                                          │
│    baseURL: '/api/v1',            ← Vite proxy prefix               │
│    timeout: 30000,                                                    │
│    headers: { 'Content-Type': 'application/json' }                   │
│  })                                                                   │
│                                                                      │
│  Request Interceptor:                                                 │
│    → Reads access_token from localStorage                            │
│    → Sets Authorization: Bearer <token> header                      │
│                                                                      │
│  Response Interceptor:                                               │
│    → If 401 received → clear token, redirect to /login              │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Vite Proxy Configuration

In development, Vite proxies `/api` requests to the backend:

```typescript
// frontend/vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',   // Backend (or Kong at 8000)
      changeOrigin: true,
    },
  },
}
```

**Request flow in development:**
```
Browser → http://localhost:3000/api/v1/merchants
              │
              ▼ (Vite proxy)
         http://localhost:8000/api/v1/merchants
              │
              ▼ (FastAPI)
         Route handler → Service → Database → Response
```

**Request flow in production:**
```
Browser → https://bnpl.example.com/api/v1/merchants
              │
              ▼ (Nginx/Kong)
         https://backend:8000/api/v1/merchants
              │
              ▼ (FastAPI)
         Response
```

### 4.3 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  LOGIN FLOW                                                        │
│                                                                     │
│  LoginPage.tsx                                                       │
│     │                                                               │
│     ├── POST /api/v1/auth/login                                     │
│     │   Body: { "email": "admin@bnpl.la", "password": "****" }     │
│     │                                                               │
│     ├── Response: { "access_token": "eyJ...", "role": "admin" }    │
│     │                                                               │
│     ├── AuthContext stores:                                         │
│     │   ├── token → localStorage('access_token')                   │
│     │   ├── user → decoded JWT payload (sub, role, name)           │
│     │   └── isAuthenticated = true                                  │
│     │                                                               │
│     └── Navigate to /dashboard                                     │
│                                                                     │
│  EVERY SUBSEQUENT REQUEST:                                          │
│     apiClient.interceptor →                                         │
│       Authorization: Bearer eyJ...                                  │
│                                                                     │
│  PROTECTED ROUTES:                                                  │
│     ProtectedRoute.tsx checks:                                      │
│       ← isAuthenticated? → render Layout + Page                    │
│       ← else → redirect to /login                                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Three auth modes:**

| Mode | Dependency | Token Source | Used By |
|------|-----------|-------------|---------|
| **Admin JWT** | `get_current_admin` | Bearer token with `role=admin` | All admin portal endpoints |
| **Merchant API Key** | `get_api_merchant` | `X-API-Key` header | Merchant-facing endpoints (auth, refunds) |
| **Consumer JWT** | `get_current_consumer` | Bearer token with `role=consumer` | Consumer self-service endpoints |

### 4.4 Complete Page-to-Endpoint Mapping

| Page | API Endpoints Called | Service File | Query Key |
|------|---------------------|--------------|-----------|
| `LoginPage` | `POST /api/v1/auth/login` | Direct axios call in AuthContext | — |
| `DashboardPage` | `GET /api/v1/merchants?page=1&page_size=5` | `merchantService.fetchMerchants()` | `['merchants', 1]` |
| | `GET /api/v1/eod/status` | `eodService.fetchEodStatus()` | `['eod-status']` |
| | `GET /api/v1/eod/batches?page=1&page_size=5` | `eodService.fetchEodBatches()` | `['eod-batches', 1]` |
| `MerchantsPage` | `GET /api/v1/merchants?page=&search=` | `merchantService.fetchMerchants()` | `['merchants', page]` |
| | `POST /api/v1/merchants/onboard` | `merchantService.onboardMerchant()` | — (mutation) |
| `MerchantDetailPage` | `GET /api/v1/merchants/{id}` | `merchantService.fetchMerchant()` | `['merchant', id]` |
| | `GET /api/v1/merchants/{id}/documents` | `merchantService.fetchMerchantDocuments()` | `['merchant-documents', id]` |
| | `POST /api/v1/merchants/{id}/documents` | `merchantService.uploadDocument()` | — (mutation) |
| `TransactionsPage` | `GET /api/v1/transactions?page=&page_size=` | Direct `apiClient.get()` | `['transactions', page]` |
| `ConsumersPage` | `GET /api/v1/consumers?page=&search=` | `consumerService.fetchConsumers()` | `['consumers', page, search]` |
| | `POST /api/v1/consumers/enroll` | `consumerService.enrollConsumer()` | — (mutation) |
| `SettlementPage` | `GET /api/v1/settlements?page=&page_size=` | `settlementService.fetchSettlements()` | `['settlements', page]` |
| `EodPage` | `GET /api/v1/eod/batches?page=&page_size=` | `eodService.fetchEodBatches()` | `['eod-batches', page]` |
| | `GET /api/v1/eod/status` | `eodService.fetchEodStatus()` | `['eod-status']` |
| | `POST /api/v1/eod/run` | `eodService.triggerEodRun()` | — (mutation) |
| `ReconciliationPage` | `POST /api/v1/reconciliation/batch` | `reconciliationService.reconcileBatch()` | — (mutation) |
| | `GET /api/v1/reconciliation/daily-report?date=` | `reconciliationService.fetchDailyReport()` | `['daily-reconcile', date]` |
| `StagingPage` | `POST /api/v1/staging/transactions` | `stagingService.writeStagingTransaction()` | — (mutation) |
| | `GET /api/v1/staging/transactions/{correlation_id}` | `stagingService.fetchStagingStatus()` | — (direct call) |
| `WebhooksPage` | `GET /api/v1/webhooks/logs?page=&merchant_id=` | `webhookService.fetchWebhookLogs()` | `['webhook-logs', page]` |
| `MerchantHealthPage` | `GET /api/v1/merchants?page=1&page_size=1000` | `merchantService.fetchMerchants()` | `['merchants', 1]` |
| `FraudRulesPage` | `GET /api/v1/fraud-rules` | `fraudRuleService.fetchFraudRules()` | `['fraud-rules']` |
| | `POST /api/v1/fraud-rules` | `fraudRuleService.createFraudRule()` | — (mutation) |
| | `PUT /api/v1/fraud-rules/{id}` | `fraudRuleService.updateFraudRule()` | — (mutation) |
| | `DELETE /api/v1/fraud-rules/{id}` | `fraudRuleService.deleteFraudRule()` | — (mutation) |
| `OverdueTrackerPage` | `GET /api/v1/fees/overdue` | `feeService.fetchOverdueTrackers()` | `['overdue-trackers']` |
| | `POST /api/v1/fees/assess-late-fees` | `feeService.assessLateFees()` | — (mutation) |
| | `POST /api/v1/fees/assess-interest` | `feeService.assessInterest()` | — (mutation) |
| `NotificationLogsPage` | `GET /api/v1/notifications?page=&channel=` | `notificationService.fetchNotifications()` | `['notifications', page, channel]` |
| `CreditRefreshLogsPage` | `GET /api/v1/credit/refresh-logs` | `creditService.fetchCreditRefreshLogs()` | `['credit-refresh-logs']` |
| | `POST /api/v1/credit/refresh` | `creditService.triggerCreditRefresh()` | — (mutation) |
| `ComplaintsPage` | `GET /api/v1/complaints?page=&status=` | `complaintService.fetchComplaints()` | `['complaints', page, status]` |
| | `POST /api/v1/complaints` | `complaintService.createComplaint()` | — (mutation) |
| | `POST /api/v1/complaints/{id}/resolve` | `complaintService.resolveComplaint()` | — (mutation) |

### 4.5 Data Fetching Pattern (TanStack React Query)

The frontend uses `@tanstack/react-query` for all data fetching. The pattern is:

```typescript
// Service function (in services/merchantService.ts):
export const fetchMerchants = async (params: { page: number; search?: string }): Promise<MerchantList> => {
  const { data } = await apiClient.get('/merchants', { params });
  return data;
};

// Page component (in pages/MerchantsPage.tsx):
const { data, isLoading } = useQuery({
  queryKey: ['merchants', page, search],
  queryFn: () => fetchMerchants({ page, search }),
});

// Mutations (POST/PUT/DELETE):
const onboardMutation = useMutation({
  mutationFn: onboardMerchant,
  onSuccess: () => {
    enqueueSnackbar('Merchant onboarded', { variant: 'success' });
    queryClient.invalidateQueries({ queryKey: ['merchants'] });  // Refresh list
  },
});
```

### 4.6 Kong API Gateway (Production)

In production, Kong sits in front of the backend API providing:

```
Kong Gateway (port 8000) → Rate Limiting → Backend (port 8000)
```

| Route | Rate Limit | Plugins |
|-------|-----------|---------|
| `/api/v1/bnpl` | 100/min | Rate-limiting, CORS |
| `/api/v1/merchants` | 200/min | Rate-limiting, CORS |
| `/api/v1/staging` | 500/min | Rate-limiting, CORS |
| `/api/v1/consumers` | 100/min | Rate-limiting, CORS |
| `/api/v1/transactions` | 200/min | Rate-limiting, CORS |

---

## 5. Server Operations

### 5.1 Docker Setup (Full Stack)

**Prerequisites:**
- Docker 24+ and Docker Compose 2.20+
- Git
- At least 8GB RAM allocated to Docker

**Services in docker-compose.yml:**

| Service | Image | Port (Host) | Purpose |
|---------|-------|-------------|---------|
| `bnpl-api` | Build from `./backend/Dockerfile` | 8002:8000 | FastAPI backend |
| `bnpl-db` | postgres:16-alpine | 5432:5432 | Main BNPL database |
| `cbs-staging-db` | postgres:16-alpine | 5433:5432 | CBS staging database |
| `redis` | redis:7-alpine | 6379:6379 | Cache (limits, auth tokens) |
| `zookeeper` | confluentinc/cp-zookeeper:7.6 | 2181 | Kafka coordinator |
| `kafka` | confluentinc/cp-kafka:7.6 | 9092:9092 | Event streaming |
| `kong` | kong:3.7 | 8000:8000, 8443, 8001 | API Gateway |

#### Starting All Services (Docker)

```bash
# Step 1: Clone and enter the project
git clone <repo-url> bnpl-platform
cd bnpl-platform

# Step 2: Start all services in detached mode
docker-compose up -d

# Step 3: Check status
docker-compose ps

# Step 4: View logs (follow all services)
docker-compose logs -f

# Step 5: View logs for a specific service
docker-compose logs -f bnpl-api

# Step 6: Run database migrations (after services are up)
docker-compose exec bnpl-api alembic upgrade head

# Step 7: Initialize CBS staging schema
docker-compose exec bnpl-api python -c "
from cbs_staging.init_staging_schema import init_schema;
from core.database import CbsStagingSessionLocal;
init_schema(CbsStagingSessionLocal())
"

# Step 8: Verify health
curl http://localhost:8002/health

# Step 9: Access the frontend (build and serve separately, see section 5.3)
```

#### Stopping All Services (Docker)

```bash
# Graceful shutdown (preserves volumes)
docker-compose down

# Shutdown + remove volumes (WARNING: deletes all data!)
docker-compose down -v

# Stop but keep containers (can restart with `docker-compose start`)
docker-compose stop
```

#### Restarting a Single Service

```bash
docker-compose restart bnpl-api        # Restart just the API
docker-compose restart bnpl-db          # Restart just the database
```

#### Viewing Logs

```bash
docker-compose logs -f --tail=100 bnpl-api   # Last 100 lines + follow
docker-compose logs bnpl-db                   # All logs (no follow)
```

### 5.2 Without Docker (Manual Setup)

**Prerequisites:**
- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Kafka 3.5+ (with Zookeeper)
- Node.js 20+ and npm 10+

#### 5.2.1 Database Setup

```bash
# Create PostgreSQL databases
psql -U postgres -c "CREATE DATABASE bnpl_platform;"
psql -U postgres -c "CREATE DATABASE cbs_staging;"

# Create users
psql -U postgres -c "CREATE USER bnpl_user WITH PASSWORD 'bnpl_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE bnpl_platform TO bnpl_user;"
psql -U postgres -c "CREATE USER bnpl_stg_writer WITH PASSWORD 'stg_pass';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE cbs_staging TO bnpl_stg_writer;"

# Initialize CBS staging schema
psql -U bnpl_stg_writer -d cbs_staging -f backend/cbs_staging/init_staging_schema.sql
```

#### 5.2.2 Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# The API is now available at http://localhost:8000
# API docs at http://localhost:8000/docs
# ReDoc at http://localhost:8000/redoc
```

**Environment Variables (optional, defaults work for development):**

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | BNPL database host |
| `POSTGRES_PORT` | `5432` | BNPL database port |
| `POSTGRES_USER` | `bnpl_user` | BNPL database user |
| `POSTGRES_PASSWORD` | `bnpl_pass` | BNPL database password |
| `POSTGRES_DB` | `bnpl_platform` | BNPL database name |
| `CBS_STAGING_HOST` | `localhost` | CBS staging database host |
| `CBS_STAGING_PORT` | `5432` | CBS staging database port |
| `CBS_STAGING_USER` | `bnpl_stg_writer` | CBS staging user |
| `CBS_STAGING_PASSWORD` | `stg_pass` | CBS staging password |
| `CBS_STAGING_DB` | `cbs_staging` | CBS staging database |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka bootstrap servers |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |

#### 5.2.3 Frontend Setup

```bash
cd frontend
npm install
npm run dev

# The frontend is now available at http://localhost:3000
# It proxies /api requests to http://localhost:8000
```

### 5.3 Frontend Build Process

#### Development Build (with hot-reload)

```bash
cd frontend
npm install          # Install dependencies (first time or after package.json changes)
npm run dev          # Start dev server on port 3000 with HMR
```

#### Production Build

```bash
cd frontend

# Step 1: Install dependencies (if not already done)
npm install

# Step 2: Run TypeScript type check
npx tsc --noEmit

# Step 3: Build production bundle
npm run build

# Output:
#   - dist/ folder is created
#   - Contains: index.html, assets/*.js, assets/*.css
```

#### What the Build Produces

```
frontend/dist/
├── index.html              # Entry HTML (inlined scripts)
├── assets/
│   ├── index-xxxx.js       # Bundled application code (React, MUI, all pages)
│   ├── index-xxxx.css      # Compiled CSS (MUI styles + global.css)
│   └── vendor-xxxx.js      # Vendor chunk (if code-split)
```

#### Serving the Build

**Option A: Serve with a static server (development/test):**

```bash
# Install a static file server globally
npm install -g serve

# Serve the dist folder
serve -s dist -l 3000

# Or use npx (no install needed)
npx serve -s dist -l 3000
```

**Option B: Serve with Nginx (production):**

```nginx
# /etc/nginx/sites-available/bnpl
server {
    listen 80;
    server_name bnpl.example.com;

    # Frontend static files
    root /var/www/bnpl/dist;
    index index.html;

    # SPA fallback — all routes serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option C: Serve with the backend (FastAPI static files mount):**

```python
# In main.py — mount the built frontend
from fastapi.staticfiles import StaticFiles

# Only in production
if settings.ENV == "production":
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")
```

**Option D: Serve with Docker:**

Create a `frontend/Dockerfile`:

```dockerfile
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Then add to `docker-compose.yml`:

```yaml
frontend:
  build: ./frontend
  ports:
    - "3000:80"
  depends_on:
    - bnpl-api
```

#### What to Do with the `dist/` Folder

1. **Deploy to production server** — Copy `dist/` to your web server's document root
2. **Containerize** — Include `dist/` in a Docker image with Nginx
3. **CI/CD artifact** — Store as a build artifact for deployment pipelines
4. **CDN upload** — Upload `dist/` assets to a CDN (Cloudflare, AWS CloudFront, etc.)

### 5.4 Database Migrations

```bash
# Run all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 0001

# Create a new migration (autogenerate)
alembic revision --autogenerate -m "description_of_change"

# View migration history
alembic history

# View current migration version
alembic current
```

### 5.5 Useful Commands

```bash
# Backend — run tests
cd backend && pytest

# Backend — run specific test file
cd backend && pytest tests/test_auth_service.py -v

# Backend — lint check
cd backend && ruff check .

# Frontend — TypeScript check
cd frontend && npx tsc --noEmit

# Frontend — lint
cd frontend && npx eslint src/

# Both databases — connect via psql
psql -h localhost -p 5432 -U bnpl_user -d bnpl_platform
psql -h localhost -p 5433 -U bnpl_stg_writer -d cbs_staging

# Redis CLI
redis-cli -h localhost -p 6379

# Kafka — list topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Kafka — consume topic messages
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic bnpl-auth --from-beginning
```

---

## 6. Development Environment Setup

### 6.1 Quick Start (Windows)

```powershell
# 1. Clone the repository
git clone <repo-url> bnpl-platform
cd bnpl-platform

# 2. Start infrastructure (databases, cache, queue)
docker-compose up -d bnpl-db cbs-staging-db redis zookeeper kafka

# 3. Set up Python backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 4. Initialize databases
alembic upgrade head
python -c "from cbs_staging.init_staging_schema import init_schema; from core.database import CbsStagingSessionLocal; init_schema(CbsStagingSessionLocal())"

# 5. Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 6. In a new terminal, start frontend
cd frontend
npm install
npm run dev

# 7. Open in browser
start http://localhost:3000
```

### 6.2 Quick Start (Linux/Mac)

```bash
# 1. Clone and start infrastructure
git clone <repo-url> bnpl-platform
cd bnpl-platform
docker-compose up -d bnpl-db cbs-staging-db redis zookeeper kafka

# 2. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -c "from cbs_staging.init_staging_schema import init_schema; from core.database import CbsStagingSessionLocal; init_schema(CbsStagingSessionLocal())"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# 3. Frontend
cd ../frontend
npm install
npm run dev &
```

### 6.3 Quick Start (Docker Only — No Local Dependencies)

```bash
# Start everything
docker-compose up -d

# Run migrations
docker-compose exec bnpl-api alembic upgrade head

# Init CBS staging schema
docker-compose exec bnpl-api python -c "from cbs_staging.init_staging_schema import init_schema; from core.database import CbsStagingSessionLocal; init_schema(CbsStagingSessionLocal())"

# Build and serve frontend locally (since there's no frontend Docker service yet)
cd frontend
npm install
npm run dev
```

### 6.4 Default Credentials

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Admin | `admin@bnpl.la` | (set via onboarding) | Full access to all admin endpoints |
| Merchant | (per merchant) | (set via onboarding) | `X-API-Key` auth for auth/refund endpoints |
| Consumer | (per consumer) | (phone-based login) | JWT with `role=consumer` for self-service |

### 6.5 Accessing API Documentation

Once the backend is running:

| Tool | URL |
|------|-----|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |
| Health Check | `http://localhost:8000/health` |
| Metrics | `http://localhost:8000/metrics` |
| Kong (if running) | `http://localhost:8001` |

---

## Appendix: Architecture Diagram (Text)

```
                        FRONTEND (React, port 3000)
                              │
                     Vite Proxy (/api → :8000)
                              │
                    ┌─────────┴──────────┐
                    │  KONG API GATEWAY   │
                    │  (port 8000, prod)  │
                    └─────────┬──────────┘
                              │
                    ┌─────────┴──────────────────────────────────────┐
                    │         FASTAPI BACKEND (port 8000)            │
                    │                                                │
                    │  ┌─────┐ ┌──────┐ ┌─────┐ ┌─────┐ ┌────────┐ │
                    │  │Auth │ │Merch │ │Cons │ │Stg  │ │...14   │ │
                    │  │Routes│ │Routes│ │Routes│ │Routes│ │more   │ │
                    │  └──┬──┘ └──┬───┘ └──┬──┘ └──┬──┘ └────────┘ │
                    │     │       │        │       │                │
                    │  ┌──┴───┐ ┌┴────┐ ┌──┴───┐ ┌─┴──────────┐   │
                    │  │Auth  │ │Merch│ │Cons  │ │Staging     │   │
                    │  │Service│ │Serv.│ │Serv. │ │Service     │   │
                    │  └──┬───┘ └─────┘ └──────┘ └─┬───────────┘   │
                    │     │                        │               │
                    │  ┌──┴────────────────────────┴──────────┐    │
                    │  │         FraudService                 │    │
                    │  │         FeeService                   │    │
                    │  │         DisputeService               │    │
                    │  │         RefundService                │    │
                    │  │         SettlementService            │    │
                    │  │         ... (17 services total)      │    │
                    │  └──────────────────────────────────────┘    │
                    └──────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────┴─────┐       ┌─────┴──────┐       ┌─────┴──────┐
    │PostgreSQL│       │ PostgreSQL │       │   Redis    │
    │ bnpl_    │       │ cbs_staging│       │   Cache    │
    │ platform │       │ (INT_STG)  │       │            │
    └──────────┘       └────────────┘       └────────────┘
                              │
                    ┌─────────┴──────────┐
                    │  Kafka (4 topics)   │
                    │  bnpl-auth         │
                    │  bnpl-staging      │
                    │  bnpl-settlement   │
                    │  bnpl-notification │
                    └────────────────────┘
```

---

*Generated from codebase analysis. For questions, refer to the inline documentation in each module or the API docs at `/docs`.*
