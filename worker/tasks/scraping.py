import asyncio
import uuid
from datetime import datetime, timedelta

from celery import Task
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.price_history import PriceHistory
from app.models.product_offers import ProductOffer
from worker.scraping.engine import PlaywrightScraper
from worker.scraping.exceptions import ScrapingBlockedError, ScrapingTimeoutError
from worker.scraping.strategies import get_strategy

UNAVAILABLE_RETRY_COOLDOWN = timedelta(hours=24)
MAX_CONSECUTIVE_FAILURES = 5


async def _scrape_offer(offer_id: str) -> None:
    async with async_session_factory() as db:
        offer = await db.get(ProductOffer, uuid.UUID(offer_id))
        if offer is None:
            return

        strategy = get_strategy(offer.scraper_strategy)
        scraped = await PlaywrightScraper().scrape(offer.url, strategy)

        db.add(PriceHistory(offer_id=offer.id, price=scraped.price))
        offer.last_scraped_at = datetime.utcnow()
        offer.consecutive_failures = 0
        offer.status = "active"
        if scraped.name:
            offer.scraped_name = scraped.name
        if scraped.image_url:
            offer.scraped_image_url = scraped.image_url

        await db.commit()


async def _record_scrape_failure(offer_id: str) -> None:
    async with async_session_factory() as db:
        offer = await db.get(ProductOffer, uuid.UUID(offer_id))
        if offer is None:
            return

        offer.consecutive_failures += 1
        offer.last_scraped_at = datetime.utcnow()
        if offer.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            offer.status = "unavailable"

        await db.commit()


class ScrapeOfferTask(Task):
    name = "worker.tasks.scraping.scrape_offer"
    autoretry_for = (ScrapingTimeoutError, ScrapingBlockedError)
    retry_backoff = True
    retry_backoff_max = 120
    max_retries = 3

    def run(self, offer_id: str) -> None:
        asyncio.run(_scrape_offer(offer_id))

    def on_failure(self, exc, task_id, args, kwargs, einfo) -> None:
        offer_id = args[0] if args else kwargs.get("offer_id")
        if offer_id is not None:
            asyncio.run(_record_scrape_failure(offer_id))


scrape_offer = celery_app.register_task(ScrapeOfferTask())


async def _dispatch_active_offers() -> None:
    now = datetime.utcnow()
    async with async_session_factory() as db:
        stmt = select(ProductOffer.id, ProductOffer.status, ProductOffer.last_scraped_at).where(
            ProductOffer.status.in_(["active", "unavailable"])
        )
        result = await db.execute(stmt)
        rows = result.all()

    for offer_id, status, last_scraped_at in rows:
        if status == "unavailable" and last_scraped_at is not None:
            if now - last_scraped_at < UNAVAILABLE_RETRY_COOLDOWN:
                continue
        scrape_offer.delay(str(offer_id))


@celery_app.task(name="worker.tasks.scraping.scrape_all_active_offers")
def scrape_all_active_offers() -> None:
    asyncio.run(_dispatch_active_offers())
