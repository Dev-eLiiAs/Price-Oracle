from worker.scraping.strategies.base import ScraperStrategy

# Fallback for any retailer without a dedicated strategy. Relies on the
# Open Graph / schema.org product metadata that most e-commerce sites publish
# for social sharing and SEO, instead of site-specific CSS selectors.
STRATEGY = ScraperStrategy(
    name="generic",
    domains=(),
    name_selector="meta[property='og:title']",
    name_attr="content",
    price_selector=(
        "meta[property='product:price:amount'], "
        "meta[property='og:price:amount'], "
        "meta[itemprop='price']"
    ),
    price_attr="content",
    image_selector="meta[property='og:image']",
    image_attr="content",
    wait_for_selector="meta[property='og:title']",
    wait_for_state="attached",
)
