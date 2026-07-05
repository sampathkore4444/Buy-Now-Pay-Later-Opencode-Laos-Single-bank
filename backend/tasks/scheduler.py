from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from core.config import settings
from common.constants import LAO_TZ


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=LAO_TZ)

    scheduler.add_job(
        "tasks.eod_batch:EODBatchProcessor().process",
        trigger=CronTrigger(hour=22, minute=0, timezone=LAO_TZ),
        id="eod_batch",
        name="EOD batch processing at 22:00 ICT",
        replace_existing=True,
    )

    scheduler.add_job(
        "tasks.repayment_batch:RepaymentBatchProcessor().process",
        trigger=CronTrigger(hour=6, minute=0, timezone=LAO_TZ),
        id="auto_debit",
        name="Auto-debit repayment batch at 06:00 ICT",
        replace_existing=True,
    )

    scheduler.add_job(
        "tasks.credit_refresh:CreditLimitRefreshTask().refresh_all",
        trigger=CronTrigger(hour=2, minute=0, timezone=LAO_TZ),
        id="credit_refresh",
        name="Credit limit refresh from data warehouse at 02:00 ICT",
        replace_existing=True,
    )

    scheduler.add_job(
        "tasks.fee_batch:FeeBatchProcessor().process_daily_fees",
        trigger=CronTrigger(hour=8, minute=0, timezone=LAO_TZ),
        id="daily_late_fees",
        name="Daily late fee assessment at 08:00 ICT",
        replace_existing=True,
    )

    scheduler.add_job(
        "tasks.fee_batch:FeeBatchProcessor().process_monthly_interest",
        trigger=CronTrigger(day=1, hour=9, minute=0, timezone=LAO_TZ),
        id="monthly_interest",
        name="Monthly interest assessment on 1st of month at 09:00 ICT",
        replace_existing=True,
    )

    scheduler.add_job(
        "tasks.settlement_batch:SettlementBatchProcessor().process",
        trigger=CronTrigger(hour=23, minute=0, timezone=LAO_TZ),
        id="merchant_settlement",
        name="Merchant settlement batch at 23:00 ICT",
        replace_existing=True,
    )

    scheduler.start()
    return scheduler
