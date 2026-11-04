"""Отправка сообщений в Telegram."""
import time
import requests
from .config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from .log import log


def telegram(text: str) -> bool:
    # Жесткая очистка от всех возможных пробелов и переносов строк
    token = "".join(str(TELEGRAM_TOKEN).split())
    chat_id = "".join(str(TELEGRAM_CHAT_ID).split())

    if not token or not chat_id:
        log("[нет TELEGRAM_TOKEN/CHAT_ID]", text)
        return False

    for _ in range(3):
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": text,
                      "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=15,
            )
            if r.ok:
                return True
            log("Telegram error", r.status_code, r.text[:200])
        except Exception as e:
            log("Telegram exception", e)
        time.sleep(3)
    return False
