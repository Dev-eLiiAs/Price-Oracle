import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.alerts import Alert
from app.models.notifications_log import NotificationLog
from app.models.users import User
from app.services import advisor as advisor_service
from app.services import products as products_service
from worker.notifications.email_sender import send_email
from worker.notifications.telegram_sender import send_telegram

ANTI_SPAM_WINDOW = timedelta(hours=24)


def _alert_triggered(alert: Alert, current_price, recommendation) -> bool:
    if current_price is None:
        return False
    if alert.threshold_type == "fixed_price":
        return alert.threshold_price is not None and current_price <= alert.threshold_price
    if alert.threshold_type == "historical_min":
        return recommendation.verdict == "buy_now"
    if alert.threshold_type == "percentile_low":
        return recommendation.verdict in ("buy_now", "good_time")
    return False


async def _recently_notified(db, alert_id: uuid.UUID) -> bool:
    stmt = (
        select(NotificationLog.id)
        .where(
            NotificationLog.alert_id == alert_id,
            NotificationLog.status == "sent",
            NotificationLog.sent_at >= datetime.utcnow() - ANTI_SPAM_WINDOW,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _send_and_log(db, user: User | None, product, alert: Alert, message: str) -> None:
    targets = (
        ("email", send_email, user.email if user else None, "Price Oracle: alerta de precio"),
        ("telegram", send_telegram, user.telegram_chat_id if user else None, None),
    )
    for channel, send_fn, target, subject in targets:
        if not target:
            continue
        status = "sent"
        try:
            if subject is not None:
                send_fn(target, subject, message)
            else:
                send_fn(target, message)
        except Exception:
            status = "failed"
        db.add(
            NotificationLog(
                user_id=product.user_id,
                alert_id=alert.id,
                product_id=product.id,
                channel=channel,
                status=status,
                message=message,
            )
        )
    await db.commit()


async def _evaluate_and_notify(product_id: str) -> None:
    async with async_session_factory() as db:
        product = await products_service.get_product(db, uuid.UUID(product_id))
        if product is None:
            return

        alerts_stmt = select(Alert).where(
            Alert.product_id == product.id, Alert.is_active.is_(True)
        )
        alerts = (await db.execute(alerts_stmt)).scalars().all()
        if not alerts:
            return

        current_price, current_retailer = await products_service.get_best_price(db, product)
        history = await products_service.get_history(db, product)
        recommendation = advisor_service.compute_recommendation(history, current_price)
        user = await db.get(User, product.user_id)

        name = product.canonical_name or "Tu producto"
        message = f"{name}: {current_price} € en {current_retailer}. ¡Alcanzó tu umbral!"

        for alert in alerts:
            if not _alert_triggered(alert, current_price, recommendation):
                continue
            if await _recently_notified(db, alert.id):
                continue
            await _send_and_log(db, user, product, alert, message)


@celery_app.task(name="worker.tasks.notifications.evaluate_and_notify")
def evaluate_and_notify(product_id: str) -> None:
    asyncio.run(_evaluate_and_notify(product_id))
