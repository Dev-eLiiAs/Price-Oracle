import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProductOffer(Base):
    __tablename__ = "product_offers"
    __table_args__ = (UniqueConstraint("product_id", "url", name="uq_offer_product_url"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    retailer: Mapped[str] = mapped_column(String, nullable=False)
    scraper_strategy: Mapped[str] = mapped_column(String, nullable=False)
    scraped_name: Mapped[str | None] = mapped_column(String, nullable=True)
    scraped_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active", index=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_scraped_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="offers")
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="offer", cascade="all, delete-orphan"
    )
