import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.users import User
from app.schemas.users import UserUpdate

DEFAULT_USER_ID = uuid.UUID(settings.DEFAULT_USER_ID)
PLACEHOLDER_EMAIL = "default@price-oracle.local"


async def get_or_create_default_user(db: AsyncSession) -> User:
    user = await db.get(User, DEFAULT_USER_ID)
    if user is None:
        user = User(id=DEFAULT_USER_ID, email=PLACEHOLDER_EMAIL)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def update_default_user(db: AsyncSession, data: UserUpdate) -> User:
    user = await get_or_create_default_user(db)
    if data.telegram_chat_id is not None:
        user.telegram_chat_id = data.telegram_chat_id
    await db.commit()
    await db.refresh(user)
    return user
