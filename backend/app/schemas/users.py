import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserUpdate(BaseModel):
    telegram_chat_id: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    telegram_chat_id: str | None
    created_at: datetime
