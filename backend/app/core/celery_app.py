from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "price_oracle",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["worker.tasks.scraping", "worker.tasks.notifications"],
)

celery_app.conf.task_routes = {
    "worker.tasks.scraping.*": {"queue": "scraping"},
    "worker.tasks.notifications.*": {"queue": "notifications"},
}

celery_app.conf.beat_schedule = {
    "scrape-all-active-offers": {
        "task": "worker.tasks.scraping.scrape_all_active_offers",
        "schedule": settings.SCRAPE_INTERVAL_MINUTES * 60,
    },
}
