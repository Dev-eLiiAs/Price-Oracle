class ScrapingError(Exception):
    """Base exception for scraping failures."""


class ScrapingTimeoutError(ScrapingError):
    """The page or a required selector did not load in time."""


class ScrapingBlockedError(ScrapingError):
    """The retailer served a CAPTCHA or otherwise denied access."""


class UnsupportedRetailerError(ScrapingError):
    """No scraping strategy is registered for this URL's domain."""


class DuplicateOfferError(ScrapingError):
    """This URL is already tracked for the current user."""

    def __init__(self, message: str, product_id: str):
        super().__init__(message)
        self.product_id = product_id
