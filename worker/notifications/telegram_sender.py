import httpx

from app.core.config import settings


def send_telegram(chat_id: str, text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Telegram no configurado (TELEGRAM_BOT_TOKEN vacío)")

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = httpx.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    response.raise_for_status()
