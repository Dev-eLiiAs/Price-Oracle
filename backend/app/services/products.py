import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.price_history import PriceHistory
from app.models.product_offers import ProductOffer
from app.models.products import Product
from app.schemas.products import OfferCreate, ProductCreate, ProductUpdate

DEFAULT_USER_ID = uuid.UUID(settings.DEFAULT_USER_ID)


async def get_best_price(db: AsyncSession, product: Product) -> tuple[Decimal | None, str | None]:
    """Best price = MIN(latest price per active offer). Returns (price, retailer)."""
    if not product.offers:
        return None, None

    best_price: Decimal | None = None
    best_retailer: str | None = None
    for offer in product.offers:
        if offer.status != "active":
            continue
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.offer_id == offer.id)
            .order_by(PriceHistory.scraped_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        latest = result.scalar_one_or_none()
        if latest is not None and (best_price is None or latest.price < best_price):
            best_price = latest.price
            best_retailer = offer.retailer
    return best_price, best_retailer


async def list_products(db: AsyncSession) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.user_id == DEFAULT_USER_ID)
        .options(selectinload(Product.offers))
        .order_by(Product.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    stmt = (
        select(Product)
        .where(Product.id == product_id, Product.user_id == DEFAULT_USER_ID)
        .options(selectinload(Product.offers))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(
        user_id=DEFAULT_USER_ID,
        canonical_name=data.canonical_name,
        image_url=data.image_url,
    )
    db.add(product)
    await db.flush()

    if data.offer is not None:
        await add_offer(db, product, data.offer)

    await db.commit()
    await db.refresh(product, attribute_names=["offers"])
    return product


async def update_product(db: AsyncSession, product: Product, data: ProductUpdate) -> Product:
    if data.canonical_name is not None:
        product.canonical_name = data.canonical_name
    if data.image_url is not None:
        product.image_url = data.image_url
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    await db.commit()


async def add_offer(db: AsyncSession, product: Product, data: OfferCreate) -> ProductOffer:
    offer = ProductOffer(
        product_id=product.id,
        url=data.url,
        retailer=data.retailer,
        scraper_strategy=data.scraper_strategy,
        scraped_name=data.scraped_name,
        scraped_image_url=data.scraped_image_url,
    )
    db.add(offer)
    await db.flush()

    price_point = PriceHistory(offer_id=offer.id, price=data.price)
    db.add(price_point)

    if product.canonical_name is None and data.scraped_name:
        product.canonical_name = data.scraped_name
    if product.image_url is None and data.scraped_image_url:
        product.image_url = data.scraped_image_url

    await db.flush()
    return offer


async def get_offer(db: AsyncSession, product: Product, offer_id: uuid.UUID) -> ProductOffer | None:
    stmt = select(ProductOffer).where(
        ProductOffer.id == offer_id, ProductOffer.product_id == product.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_price_point(db: AsyncSession, offer: ProductOffer, price: Decimal, currency: str) -> PriceHistory:
    point = PriceHistory(offer_id=offer.id, price=price, currency=currency)
    db.add(point)
    await db.commit()
    await db.refresh(point)
    return point


async def get_history(db: AsyncSession, product: Product) -> list[PriceHistory]:
    offer_ids = [offer.id for offer in product.offers]
    if not offer_ids:
        return []
    stmt = (
        select(PriceHistory)
        .where(PriceHistory.offer_id.in_(offer_ids))
        .order_by(PriceHistory.scraped_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
