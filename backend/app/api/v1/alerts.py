import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.alerts import AlertCreate, AlertRead
from app.services import alerts as alerts_service
from app.services import products as products_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertRead, status_code=201)
async def create_alert(data: AlertCreate, db: AsyncSession = Depends(get_db)):
    product = await products_service.get_product(db, data.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return await alerts_service.create_alert(db, data)


@router.get("", response_model=list[AlertRead])
async def list_alerts(product_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    return await alerts_service.list_alerts(db, product_id)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    alert = await alerts_service.get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    await alerts_service.delete_alert(db, alert)
