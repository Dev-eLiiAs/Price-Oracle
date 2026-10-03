from urllib.parse import urlparse

from worker.scraping.exceptions import UnsupportedRetailerError
from worker.scraping.strategies import amazon, generic, pccomponentes
from worker.scraping.strategies.base import ScraperStrategy

REGISTRY: dict[str, ScraperStrategy] = {
    amazon.STRATEGY.name: amazon.STRATEGY,
    pccomponentes.STRATEGY.name: pccomponentes.STRATEGY,
    generic.STRATEGY.name: generic.STRATEGY,
}


def get_strategy(name: str) -> ScraperStrategy:
    try:
        return REGISTRY[name]
    except KeyError:
        raise UnsupportedRetailerError(f"No strategy registered for '{name}'") from None


def detect_strategy(url: str) -> ScraperStrategy:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for strategy in REGISTRY.values():
        if any(host == d or host.endswith(f".{d}") for d in strategy.domains):
            return strategy
    # No dedicated strategy for this domain — fall back to generic
    # Open Graph / schema.org metadata extraction instead of rejecting the URL.
    return generic.STRATEGY
