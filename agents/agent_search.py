"""Агент поиска компаний через API Яндекс.Карт."""

import os
import random
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Добавляем корень проекта в путь импортов, чтобы модуль db работал из папки agents/
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db import insert_company  # noqa: E402

YANDEX_SEARCH_URL = "https://search-maps.yandex.ru/v1/"


# Загружаем переменные окружения из .env в корне проекта
load_dotenv(ROOT_DIR / ".env")


def _extract_category(categories):
    """Возвращает первую рубрику компании, если она есть."""
    if not isinstance(categories, list) or not categories:
        return ""
    first = categories[0] if isinstance(categories[0], dict) else {}
    return first.get("name", "")


def _extract_phones(phones):
    """Склеивает все телефонные номера компании в одну строку."""
    if not isinstance(phones, list):
        return ""

    phone_numbers = []
    for phone_item in phones:
        if not isinstance(phone_item, dict):
            continue
        number = phone_item.get("formatted") or phone_item.get("url") or ""
        if number:
            phone_numbers.append(number)

    return ", ".join(phone_numbers)


def search_and_save(query: str, bbox: str) -> int:
    """Ищет компании в Яндекс.Картах и сохраняет новые записи в БД."""
    api_key = os.getenv("YANDEX_API_KEY", "").strip()
    if not api_key:
        print("Ошибка: не найден YANDEX_API_KEY в файле .env")
        return 0

    params = {
        "apikey": api_key,
        "text": query,
        "type": "biz",
        "lang": "ru_RU",
        "bbox": bbox,
        "results": 50,
    }

    try:
        # Делаем случайную паузу перед сетевым запросом, чтобы снизить нагрузку на API
        time.sleep(random.uniform(3, 5))
        response = requests.get(YANDEX_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as error:
        print(f"Ошибка при запросе к API Яндекс.Карт: {error}")
        return 0
    except ValueError as error:
        print(f"Ошибка: API вернул некорректный JSON: {error}")
        return 0

    if isinstance(payload, dict) and payload.get("error"):
        error_text = payload.get("message") or payload.get("error")
        print(f"Ошибка API Яндекс.Карт: {error_text}")
        return 0

    features = payload.get("features", []) if isinstance(payload, dict) else []
    if not isinstance(features, list):
        print("Ошибка: неожиданный формат ответа API Яндекс.Карт")
        return 0

    added_count = 0

    for feature in features:
        if not isinstance(feature, dict):
            continue

        properties = feature.get("properties", {})
        company_meta = properties.get("CompanyMetaData", {}) if isinstance(properties, dict) else {}

        if not isinstance(company_meta, dict):
            continue

        name = company_meta.get("name", "")
        category = _extract_category(company_meta.get("Categories"))
        address = company_meta.get("address", "")
        phone = _extract_phones(company_meta.get("Phones"))
        website = company_meta.get("url", "")

        is_added = insert_company(name, category, address, phone, website)
        if is_added:
            added_count += 1

    print(f"Добавлено {added_count} компаний по запросу '{query}'")
    return added_count


if __name__ == '__main__':
    test_query = "кафе"
    test_bbox = "37.55,55.70~37.72,55.79"
    search_and_save(test_query, test_bbox)
