import json
from datetime import datetime
from core.config import settings
from core.kafka import send_event
from common.utils import generate_uuid, utcnow


class NotificationService:

    TEMPLATES = {
        "purchase_confirmed": "Your BNPL purchase of {amount} LAK is confirmed. Due: {due_date}.",
        "repayment_reminder": "Reminder: Your BNPL payment of {amount} LAK is due on {due_date}.",
        "repayment_success": "BNPL repayment of {amount} LAK successful. Limit restored.",
        "settlement_notification": "BNPL settlement of {amount} LAK credited to your account.",
        "auth_declined": "Your BNPL transaction of {amount} LAK was declined. Reason: {reason}.",
        "late_fee_assessed": "Late fee of {fee_amount} LAK applied for overdue BNPL balance on {consumer_id}. Current overdue: {total_overdue} LAK.",
        "interest_assessed": "Monthly interest of {interest_amount} LAK applied on overdue BNPL balance. Total overdue: {total_overdue} LAK.",
        "overdue_warning": "Your BNPL payment is {days_overdue} days overdue. Please repay to avoid fees. Outstanding: {amount} LAK.",
    }

    async def send_sms(self, phone: str, template_key: str, params: dict) -> str:
        template = self.TEMPLATES.get(template_key, "BNPL notification: {message}")
        message = template.format(**params)
        notification_id = f"NOTIF-{generate_uuid()[:16]}"

        event = {
            "notification_id": notification_id,
            "recipient": phone,
            "channel": "SMS",
            "template": template_key,
            "message": message,
            "timestamp": utcnow().isoformat(),
        }
        await send_event(settings.KAFKA_NOTIFICATION_TOPIC, key=notification_id, value=json.dumps(event).encode())
        return notification_id

    async def notify_purchase_confirmed(self, phone: str, amount: float, due_date: str) -> str:
        return await self.send_sms(phone, "purchase_confirmed", {"amount": f"{amount:,.0f}", "due_date": due_date})

    async def notify_repayment_reminder(self, phone: str, amount: float, due_date: str) -> str:
        return await self.send_sms(phone, "repayment_reminder", {"amount": f"{amount:,.0f}", "due_date": due_date})

    async def notify_repayment_success(self, phone: str, amount: float) -> str:
        return await self.send_sms(phone, "repayment_success", {"amount": f"{amount:,.0f}"})

    async def notify_settlement(self, phone: str, amount: float) -> str:
        return await self.send_sms(phone, "settlement_notification", {"amount": f"{amount:,.0f}"})

    async def notify_declined(self, phone: str, amount: float, reason: str) -> str:
        return await self.send_sms(phone, "auth_declined", {"amount": f"{amount:,.0f}", "reason": reason})

    async def notify_late_fee(self, phone: str, fee_amount: float, consumer_id: str, total_overdue: float) -> str:
        return await self.send_sms(phone, "late_fee_assessed", {
            "fee_amount": f"{fee_amount:,.0f}",
            "consumer_id": consumer_id,
            "total_overdue": f"{total_overdue:,.0f}",
        })

    async def notify_interest_assessed(self, phone: str, interest_amount: float, total_overdue: float) -> str:
        return await self.send_sms(phone, "interest_assessed", {
            "interest_amount": f"{interest_amount:,.0f}",
            "total_overdue": f"{total_overdue:,.0f}",
        })

    async def notify_overdue_warning(self, phone: str, days_overdue: int, amount: float) -> str:
        return await self.send_sms(phone, "overdue_warning", {
            "days_overdue": str(days_overdue),
            "amount": f"{amount:,.0f}",
        })
