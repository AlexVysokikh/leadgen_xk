"""Агент отправки коммерческих предложений.

Поведение:
- Если TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID заданы — шлёт реальное уведомление менеджеру.
- Если ключи не заданы — режим имитации (печать в консоль).
"""
import os
import random
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from db import get_companies_by_status, update_company  # noqa: E402

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _send_telegram(token: str, chat_id: str, text: str) -> bool:
    url = TELEGRAM_API_URL.format(token=token)
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Telegram error: {e}")
        return False


def _build_message(company: dict) -> str:
    name = company.get("name") or "?"
    category = company.get("category") or "-"
    address = company.get("address") or "-"
    phone = company.get("phone") or "-"
    email = company.get("email") or "-"
    telegram = company.get("telegram") or "-"
    website = company.get("website") or "-"
    offer = company.get("offer_text") or "-"
    return (
        "<b>XK Media: новый лид для звонка</b>\n"
        f"<b>{name}</b> | {category}\n"
        f"📍 {address}\n"
        f"📞 {phone}\n"
        f"📧 {email}\n"
        f"📬 {telegram}\n"
        f"🌐 {website}\n"
        f"\n<b>KP:</b>\n{offer}"
    )


def send_offers(batch: int = 20):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    use_tg = bool(token and chat_id)

    try:
        companies = get_companies_by_status("approved", batch)
    except Exception as e:
        print(f"DB error: {e}")
        return

    total = len(companies)
    if total == 0:
        print("Нет компаний approved.")
        return

    sent = 0
    for company in companies:
        cid = company.get("id")
        name = company.get("name") or "?"
        offer = (company.get("offer_text") or "").strip()
        if not offer:
            print(f"Skip [{name}]: пустой КП")
            continue
        if use_tg:
            ok = _send_telegram(token, chat_id, _build_message(company))
            if ok:
                update_company(cid, status="sent")
                sent += 1
                print(f"Sent TG: [{name}]")
            else:
                print(f"TG fail: [{name}]")
        else:
            print(f"[sim] [{name}]: {offer[:80]}")
            update_company(cid, status="sent")
            sent += 1
            time.sleep(random.uniform(0.3, 0.7))
        time.sleep(random.uniform(0.5, 1.0))

    mode = "Telegram" if use_tg else "имитация"
    print(f"Отправлено: {sent} / {total} ({mode})")


if __name__ == '__main__':
    send_offers(batch=5)
