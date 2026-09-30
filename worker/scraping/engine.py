import random
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from worker.scraping.exceptions import ScrapingBlockedError, ScrapingTimeoutError
from worker.scraping.strategies.base import ScraperStrategy

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
]

BLOCKED_MARKERS = ("captcha", "robot check", "acceso denegado", "access denied")


@dataclass
class ProxyConfig:
    server: str
    username: str | None = None
    password: str | None = None


@dataclass
class ScrapedProduct:
    name: str | None
    image_url: str | None
    price: Decimal


class PlaywrightScraper:
    def __init__(self, proxy: ProxyConfig | None = None, timeout_ms: int = 20_000) -> None:
        self.proxy = proxy
        self.timeout_ms = timeout_ms

    async def scrape(self, url: str, strategy: ScraperStrategy) -> ScrapedProduct:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context_kwargs: dict = {"user_agent": random.choice(USER_AGENTS)}
            if self.proxy is not None:
                context_kwargs["proxy"] = {
                    "server": self.proxy.server,
                    "username": self.proxy.username,
                    "password": self.proxy.password,
                }
            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            try:
                await page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                content_lower = (await page.content()).lower()
                if any(marker in content_lower for marker in BLOCKED_MARKERS):
                    raise ScrapingBlockedError(f"Blocked while scraping {url}")

                await page.wait_for_selector(strategy.wait_for_selector, timeout=self.timeout_ms)

                name = await self._text_or_none(page, strategy.name_selector)
                image_url = await self._attr_or_none(
                    page, strategy.image_selector, strategy.image_attr
                )
                price_text = await self._text_or_none(page, strategy.price_selector)
                if price_text is None:
                    raise ScrapingTimeoutError(f"Price selector not found for {url}")
                price = self._parse_price(price_text, strategy.price_regex)

                return ScrapedProduct(name=name, image_url=image_url, price=price)
            except PlaywrightTimeoutError as exc:
                raise ScrapingTimeoutError(str(exc)) from exc
            except PlaywrightError as exc:
                raise ScrapingTimeoutError(str(exc)) from exc
            finally:
                await context.close()
                await browser.close()

    @staticmethod
    async def _text_or_none(page, selector: str) -> str | None:
        locator = page.locator(selector).first
        if await locator.count() == 0:
            return None
        text = await locator.text_content()
        return text.strip() if text else None

    @staticmethod
    async def _attr_or_none(page, selector: str, attribute: str) -> str | None:
        locator = page.locator(selector).first
        if await locator.count() == 0:
            return None
        return await locator.get_attribute(attribute)

    @staticmethod
    def _parse_price(text: str, price_regex: str) -> Decimal:
        match = re.search(price_regex, text)
        if not match:
            raise ScrapingTimeoutError(f"Could not parse price from '{text}'")
        raw = match.group(0)
        normalized = raw.replace(".", "").replace(",", ".") if "," in raw else raw
        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise ScrapingTimeoutError(f"Invalid price value '{raw}'") from exc
