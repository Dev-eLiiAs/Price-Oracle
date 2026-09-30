from worker.scraping.strategies.base import ScraperStrategy

STRATEGY = ScraperStrategy(
    name="amazon",
    domains=("amazon.es", "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr"),
    name_selector="#productTitle",
    price_selector="span.a-price:not(.a-text-price) span.a-offscreen",
    image_selector="#landingImage",
    wait_for_selector="#productTitle",
)
