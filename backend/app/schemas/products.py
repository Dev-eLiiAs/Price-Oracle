import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OfferCreate(BaseModel):
    url: str
    retailer: str
    scraper_strategy: str
    price: Decimal
    scraped_name: str | None = None
    scraped_image_url: str | None = None


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    url: str
    retailer: str
    scraper_strategy: str
    scraped_name: str | None
    scraped_image_url: str | None
    status: str
    consecutive_failures: int
    last_scraped_at: datetime | None
    created_at: datetime


class ProductCreate(BaseModel):
    canonical_name: str | None = None
    image_url: str | None = None
    offer: OfferCreate | None = None


class ProductUpdate(BaseModel):
    canonical_name: str | None = None
    image_url: str | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    canonical_name: str | None
    image_url: str | None
    created_at: datetime
    offers: list[OfferRead] = []
    best_price: Decimal | None = None
    best_price_retailer: str | None = None


class ProductFromUrl(BaseModel):
    url: str
    product_id: uuid.UUID | None = None


class PricePointCreate(BaseModel):
    price: Decimal
    currency: str = "EUR"


class RecommendationRead(BaseModel):
    verdict: str
    message: str
    current_price: Decimal | None
    historical_min: Decimal | None
    moving_average_30d: Decimal | None
    percentile_rank: float | None


class PricePointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: uuid.UUID
    price: Decimal
    currency: str
    scraped_at: datetime
