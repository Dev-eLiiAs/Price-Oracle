from worker.scraping.strategies.base import ScraperStrategy

STRATEGY = ScraperStrategy(
    name="pccomponentes",
    domains=("pccomponentes.com",),
    name_selector="h1",
    price_selector="#pdp-price-current-container",
    image_selector="meta[property='og:image']",
    wait_for_selector="h1",
    image_attr="content",
)
