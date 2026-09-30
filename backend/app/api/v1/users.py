from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.users import UserRead, UserUpdate
from app.services import users as users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(db: AsyncSession = Depends(get_db)):
    return await users_service.get_or_create_default_user(db)


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, db: AsyncSession = Depends(get_db)):
    return await users_service.update_default_user(db, data)
