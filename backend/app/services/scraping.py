import uuid
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.products import Product
from app.schemas.products import OfferCreate, ProductCreate
from app.services import products as products_service
from worker.scraping.engine import PlaywrightScraper
from worker.scraping.exceptions import DuplicateOfferError
from worker.scraping.strategies import detect_strategy


async def ingest_from_url(
    db: AsyncSession, url: str, product_id: uuid.UUID | None
) -> Product:
    existing_offer = await products_service.find_offer_by_url(db, url)
    if existing_offer is not None:
        raise DuplicateOfferError(
            f"Ya tienes este producto guardado: "
            f"{existing_offer.product.canonical_name or 'producto sin nombre'}.",
            product_id=str(existing_offer.product_id),
        )

    strategy = detect_strategy(url)
    scraped = await PlaywrightScraper().scrape(url, strategy)

    retailer = strategy.name
    if strategy.name == "generic":
        retailer = urlparse(url).netloc.lower().removeprefix("www.") or "generic"

    offer_data = OfferCreate(
        url=url,
        retailer=retailer,
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
