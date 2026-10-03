from dataclasses import dataclass


@dataclass(frozen=True)
class ScraperStrategy:
    name: str
    domains: tuple[str, ...]
    name_selector: str
    price_selector: str
    image_selector: str
    wait_for_selector: str
    price_regex: str = r"[\d.,]+"
    image_attr: str = "src"
    name_attr: str | None = None
    price_attr: str | None = None
    wait_for_state: str = "visible"
