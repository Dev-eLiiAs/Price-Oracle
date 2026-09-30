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
