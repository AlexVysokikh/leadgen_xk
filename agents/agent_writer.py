"""Агент генерации коммерческих предложений через OpenAI."""

import os
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Добавляем корень проекта в путь импортов, чтобы модуль db работал из папки agents/
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db import get_companies_by_status, update_company  # noqa: E402

# Загружаем переменные окружения из .env в корне проекта
load_dotenv(ROOT_DIR / ".env")

# Инициализируем клиент OpenAI из переменных окружения
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "").strip(),
    base_url=os.getenv("OPENAI_BASE_URL", "").strip() or None,
)


def _build_prompt(company: dict) -> str:
    """Формирует промпт для генерации коммерческого предложения."""
    return f'''Ты менеджер по продажам компании "Кубик Медиа" — сервис индор-рекламы
(цифровые экраны внутри торговых центров, бизнес-центров, фитнес-клубов).

Данные о потенциальном клиенте:
Компания: {company.get("name", "")}
Категория бизнеса: {company.get("category", "")}
Адрес: {company.get("address", "")}
Текст с сайта компании: {company.get("website_text", "")}

Напиши короткое живое сообщение (4-5 предложений) с предложением о сотрудничестве.
Используй конкретные детали из текста сайта, чтобы показать что ты изучил их бизнес.
Цель сообщения — договориться о коротком созвоне на 15 минут.
Не используй шаблонные фразы и канцелярит.
Пиши по-русски, деловито но по-человечески.'''


def generate_offers(batch: int = 20):
    """Генерирует коммерческие предложения для компаний со статусом scraped."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Ошибка: не найден OPENAI_API_KEY в файле .env")
        return []

    companies = get_companies_by_status("scraped", batch)
    total_count = len(companies)

    if total_count == 0:
        print("Нет компаний со статусом 'scraped' для генерации КП")
        print("Сгенерировано КП: 0 из 0 компаний")
        return []

    generated_items = []

    for company in companies:
        company_id = company.get("id")
        company_name = company.get("name") or "Без названия"
        prompt = _build_prompt(company)

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.8,
            )

            offer_text = (response.choices[0].message.content or "").strip()
            if not offer_text:
                raise ValueError("Пустой ответ модели")

            update_company(company_id, offer_text=offer_text, status="needs_approval")
            generated_items.append({"company": company, "offer_text": offer_text})
            print(f"✅ КП сгенерировано для [{company_name}]")
        except Exception as error:
            print(f"Ошибка для [{company_name}]: {error}")

        # Делаем паузу между запросами к API
        time.sleep(random.uniform(1, 2))

    print(f"Сгенерировано КП: {len(generated_items)} из {total_count} компаний")
    return generated_items


if __name__ == '__main__':
    generated = generate_offers(batch=3)
    if generated:
        first_company_name = generated[0]["company"].get("name") or "Без названия"
        print(f"\nПервое сгенерированное КП для [{first_company_name}]:\n")
        print(generated[0]["offer_text"])
    else:
        print("Сгенерированных КП нет")
