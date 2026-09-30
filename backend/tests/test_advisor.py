from datetime import datetime, timedelta
from decimal import Decimal

from app.services.advisor import compute_recommendation


class FakePoint:
    def __init__(self, days_ago: int, price: str):
        self.scraped_at = datetime(2026, 1, 30) - timedelta(days=days_ago)
        self.price = Decimal(price)


def test_insufficient_data_with_few_points():
    history = [FakePoint(0, "100")] * 3
    rec = compute_recommendation(history, Decimal("100"))
    assert rec.verdict == "insufficient_data"


def test_insufficient_data_with_no_current_price():
    history = [FakePoint(i, "100") for i in range(10)]
    rec = compute_recommendation(history, None)
    assert rec.verdict == "insufficient_data"


def test_buy_now_when_current_equals_historical_min():
    history = [
        FakePoint(60, "200"),
        FakePoint(45, "190"),
        FakePoint(30, "180"),
        FakePoint(10, "170"),
        FakePoint(0, "100"),
    ]
    rec = compute_recommendation(history, Decimal("100"))
    assert rec.verdict == "buy_now"
    assert rec.historical_min == Decimal("100")


def test_good_time_within_low_percentile():
    history = [FakePoint(9 * (i + 1), "200") for i in range(9)] + [FakePoint(90, "90")]
    rec = compute_recommendation(history, Decimal("110"))
    assert rec.verdict == "good_time"
    assert rec.percentile_rank is not None and rec.percentile_rank <= 20


def test_wait_when_price_above_moving_average():
    history = [
        FakePoint(20, "100"),
        FakePoint(15, "100"),
        FakePoint(10, "100"),
        FakePoint(5, "100"),
        FakePoint(0, "150"),
    ]
    rec = compute_recommendation(history, Decimal("150"))
    assert rec.verdict == "wait"


def test_neutral_when_price_is_unremarkable():
    history = [
        FakePoint(60, "200"),
        FakePoint(30, "160"),
        FakePoint(10, "140"),
        FakePoint(5, "150"),
        FakePoint(0, "150"),
    ]
    rec = compute_recommendation(history, Decimal("150"))
    assert rec.verdict == "neutral"
