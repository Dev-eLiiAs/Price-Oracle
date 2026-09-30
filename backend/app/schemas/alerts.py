import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    product_id: uuid.UUID
    threshold_price: Decimal | None = None
    threshold_type: str = "fixed_price"


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    threshold_price: Decimal | None
    threshold_type: str
    is_active: bool
    created_at: datetime
