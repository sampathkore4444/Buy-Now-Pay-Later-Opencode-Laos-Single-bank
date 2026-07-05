import re
from datetime import timezone, timedelta
from typing import Any

LAO_TZ = timezone(timedelta(hours=7))

LAK_DECIMAL_PLACES = 4
MAX_NARRATIVE_LENGTH = 140
CORRELATION_ID_PATTERN = re.compile(r"^[a-f0-9\-]{36}$")
ACCOUNT_NO_PATTERN = re.compile(r"^[A-Z0-9\-]{1,34}$")
MERCHANT_ID_PATTERN = re.compile(r"^M-\d{12}$")
CONSUMER_ID_PATTERN = re.compile(r"^C-\d{6,}$")
AUTH_ID_PATTERN = re.compile(r"^AUTH-\d{8}-\d{3,}$")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

MDR_TIERS = {
    "TIER_1": {"min_volume": 500_000_000, "rate": 0.035, "label": "Strategic"},
    "TIER_2": {"min_volume": 50_000_000, "rate": 0.045, "label": "Standard"},
    "TIER_3": {"min_volume": 0, "rate": 0.055, "label": "Growth"},
    "TIER_4": {"rate": 0.065, "label": "High Risk"},
}

RISK_WEIGHTS = {
    "business_tenure": 0.15,
    "transaction_volume_trend": 0.20,
    "category_risk": 0.15,
    "chargeback_rate": 0.25,
    "settlement_history": 0.15,
    "complaint_rate": 0.10,
}

EOD_GRACE_PERIOD_MINUTES = 15
EOD_MAX_DURATION_HOURS = 6
CIRCUIT_BREAKER_TIMEOUT_MINUTES = 10

LATE_FEE_FLAT_LAK = 15000
LATE_FEE_GRACE_DAYS = 30
INTEREST_MONTHLY_RATE = 0.015
INTEREST_COMPOUND_DAYS = 30
LATE_FEE_MAX_PER_CONSUMER = 5

COOLING_OFF_DAYS = 3
COOLING_OFF_THRESHOLD_LAK = 1000000
DISPUTE_INVESTIGATION_DAYS = 7


def validate_correlation_id(cid: str) -> bool:
    return bool(CORRELATION_ID_PATTERN.match(cid))


def determine_mdr_rate(estimated_monthly_volume: float, risk_tier: str) -> float:
    if risk_tier == "RED":
        return MDR_TIERS["TIER_4"]["rate"]
    if estimated_monthly_volume >= MDR_TIERS["TIER_1"]["min_volume"]:
        return MDR_TIERS["TIER_1"]["rate"]
    if estimated_monthly_volume >= MDR_TIERS["TIER_2"]["min_volume"]:
        return MDR_TIERS["TIER_2"]["rate"]
    return MDR_TIERS["TIER_3"]["rate"]


def calculate_risk_score(metrics: dict[str, Any]) -> int:
    score = 0
    if metrics.get("chargeback_rate", 0) < 0.01:
        score += 25
    elif metrics.get("chargeback_rate", 0) < 0.03:
        score += 15
    else:
        score += 5
    score += min(metrics.get("business_tenure_months", 0) * 2, 15)
    if metrics.get("settlement_on_time", True):
        score += 15
    score += (100 - metrics.get("complaint_rate", 0) * 100) * 0.10
    return min(max(score, 0), 100)


def assign_risk_tier(score: int) -> str:
    if score >= 80:
        return "GREEN"
    if score >= 60:
        return "YELLOW"
    if score >= 40:
        return "ORANGE"
    return "RED"
