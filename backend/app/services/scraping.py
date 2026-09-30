import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.products import Product
from app.schemas.products import OfferCreate, ProductCreate
from app.services import products as products_service
from worker.scraping.engine import PlaywrightScraper
from worker.scraping.strategies import detect_strategy


async def ingest_from_url(
    db: AsyncSession, url: str, product_id: uuid.UUID | None
) -> Product:
    strategy = detect_strategy(url)
    scraped = await PlaywrightScraper().scrape(url, strategy)

    offer_data = OfferCreate(
        url=url,
        retailer=strategy.name,
        scraper_strategy=strategy.name,
        price=scraped.price,
        scraped_name=scraped.name,
        scraped_image_url=scraped.image_url,
    )

    if product_id is not None:
        product = await products_service.get_product(db, product_id)
        if product is None:
            raise ValueError("Product not found")
        await products_service.add_offer(db, product, offer_data)
        await db.commit()
        await db.refresh(product, attribute_names=["offers"])
        return product

    product = await products_service.create_product(
        db,
        ProductCreate(canonical_name=scraped.name, image_url=scraped.image_url, offer=offer_data),
    )
    return product
