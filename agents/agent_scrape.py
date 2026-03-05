"""Агент парсинга сайтов компаний для поиска контактов."""

import random
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Добавляем корень проекта в путь импортов, чтобы модуль db работал из папки agents/
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db import get_companies_by_status, update_company  # noqa: E402

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
TELEGRAM_PATTERN = re.compile(r"(?:https?://)?t\.me/([a-zA-Z0-9_]{5,})|@([a-zA-Z0-9_]{5,})")


def _clean_text(raw_text: str) -> str:
    """Очищает текст от лишних пробелов и ограничивает длину до 2000 символов."""
    return " ".join(raw_text.split())[:2000]


def _extract_contacts(text: str) -> tuple[str, str]:
    """Извлекает первый email и первый Telegram из текста."""
    email_match = EMAIL_PATTERN.search(text)
    telegram_match = TELEGRAM_PATTERN.search(text)

    email = email_match.group(0) if email_match else ""
    telegram = ""

    if telegram_match:
        username = telegram_match.group(1) or telegram_match.group(2) or ""
        if username:
            telegram = f"@{username}"

    return email, telegram


def scrape_new_companies(batch: int = 20):
    """Парсит сайты компаний со статусом new и сохраняет найденные контакты в БД."""
    companies = get_companies_by_status("new", batch)

    processed_count = 0
    contacts_found_count = 0
    error_count = 0

    for company in companies:
        company_id = company.get("id")
        company_name = company.get("name") or "Без названия"
        website = (company.get("website") or "").strip()

        if not website:
            update_company(company_id, status="no_site")
            processed_count += 1
            continue

        try:
            response = requests.get(
                website,
                timeout=10,
                headers=REQUEST_HEADERS,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Удаляем скрипты и стили, чтобы не мешали анализу текста страницы
            for element in soup(["script", "style"]):
                element.decompose()

            website_text = _clean_text(soup.get_text(separator=" "))
            email, telegram = _extract_contacts(website_text)

            update_company(
                company_id,
                email=email,
                telegram=telegram,
                website_text=website_text,
                status="scraped",
            )

            if email or telegram:
                contacts_found_count += 1

        except requests.RequestException as error:
            update_company(company_id, status="error")
            error_count += 1
            print(f"Ошибка у {company_name}: {error}")

        processed_count += 1

        # Добавляем случайную паузу между запросами к сайтам
        time.sleep(random.uniform(3, 5))

    print(
        f"Обработано: {processed_count}, найдено контактов: {contacts_found_count}, ошибок: {error_count}"
    )


if __name__ == '__main__':
    scrape_new_companies(batch=5)
