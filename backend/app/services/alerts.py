import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alerts import Alert
from app.schemas.alerts import AlertCreate

DEFAULT_USER_ID = uuid.UUID(settings.DEFAULT_USER_ID)


async def create_alert(db: AsyncSession, data: AlertCreate) -> Alert:
    alert = Alert(
        user_id=DEFAULT_USER_ID,
        product_id=data.product_id,
        threshold_price=data.threshold_price,
        threshold_type=data.threshold_type,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def list_alerts(db: AsyncSession, product_id: uuid.UUID | None = None) -> list[Alert]:
    stmt = select(Alert).where(Alert.user_id == DEFAULT_USER_ID)
    if product_id is not None:
        stmt = stmt.where(Alert.product_id == product_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_alert(db: AsyncSession, alert_id: uuid.UUID) -> Alert | None:
    stmt = select(Alert).where(Alert.id == alert_id, Alert.user_id == DEFAULT_USER_ID)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_alert(db: AsyncSession, alert: Alert) -> None:
    await db.delete(alert)
    await db.commit()
