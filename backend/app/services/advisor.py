import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.price_history import PriceHistory

MIN_DATA_POINTS = 5
RECENT_WINDOW_DAYS = 30
PERCENTILE_WINDOW_DAYS = 90
GOOD_PRICE_PERCENTILE = 20
ABOVE_TREND_FACTOR = Decimal("1.1")

Verdict = str  # "buy_now" | "good_time" | "wait" | "neutral" | "insufficient_data"


@dataclass
class Recommendation:
    verdict: Verdict
    message: str
    current_price: Decimal | None
    historical_min: Decimal | None
    moving_average_30d: Decimal | None
    percentile_rank: float | None


def compute_recommendation(
    history: list[PriceHistory], current_price: Decimal | None
) -> Recommendation:
    if current_price is None or len(history) < MIN_DATA_POINTS:
        return Recommendation(
            verdict="insufficient_data",
            message="Datos insuficientes para recomendar todavía.",
            current_price=current_price,
            historical_min=None,
            moving_average_30d=None,
            percentile_rank=None,
        )

    points = sorted(((h.scraped_at, h.price) for h in history), key=lambda p: p[0])
    all_prices = [price for _, price in points]
    now = points[-1][0]

    historical_min = min(all_prices)

    recent_30 = [price for ts, price in points if now - ts <= timedelta(days=RECENT_WINDOW_DAYS)]
    moving_average_30d = Decimal(str(statistics.fmean(recent_30 or all_prices)))

    recent_90 = [price for ts, price in points if now - ts <= timedelta(days=PERCENTILE_WINDOW_DAYS)]
    window = recent_90 or all_prices
    percentile_rank = (sum(1 for p in window if p <= current_price) / len(window)) * 100

    if current_price <= historical_min:
        verdict: Verdict = "buy_now"
        message = "Precio más bajo registrado. Es el mejor momento para comprar."
    elif percentile_rank <= GOOD_PRICE_PERCENTILE:
        verdict = "good_time"
        message = "Buen momento: el precio está entre los más bajos de los últimos meses."
    elif current_price > moving_average_30d * ABOVE_TREND_FACTOR:
        verdict = "wait"
        message = "El precio está por encima de la tendencia reciente. Mejor esperar."
    else:
        verdict = "neutral"
        message = "El precio está dentro de lo habitual para este producto."

    return Recommendation(
        verdict=verdict,
        message=message,
        current_price=current_price,
        historical_min=historical_min,
        moving_average_30d=moving_average_30d,
        percentile_rank=round(percentile_rank, 1),
    )
