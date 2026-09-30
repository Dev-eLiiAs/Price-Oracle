"""seed default user

Revision ID: b242076acba6
Revises: 16d4da402081
Create Date: 2026-09-30 11:24:06.683195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.config import settings

revision: str = 'b242076acba6'
down_revision: Union[str, None] = '16d4da402081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

users_table = sa.table(
    "users",
    sa.column("id", sa.UUID),
    sa.column("email", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        users_table,
        [{"id": settings.DEFAULT_USER_ID, "email": "owner@price-oracle.local"}],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE id = :id").bindparams(id=settings.DEFAULT_USER_ID)
    )
