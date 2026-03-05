"""Агент имитации отправки коммерческих предложений."""

import random
import sys
import time
from pathlib import Path

# Добавляем корень проекта в путь импортов для корректного импорта db.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db import get_companies_by_status, update_company


def send_offers(batch: int = 20):
    """Имитирует отправку коммерческих предложений компаниям со статусом approved."""
    try:
        companies = get_companies_by_status("approved", batch)
    except Exception as error:
        print(f"Ошибка при получении компаний для отправки: {error}")
        return

    total = len(companies)
    sent_count = 0

    if total == 0:
        print("Нет компаний со статусом approved для отправки.")
        print("Отправлено КП: 0 из 0 компаний")
        return

    for company in companies:
        company_id = company.get("id")
        name = company.get("name") or "Без названия"
        email = (company.get("email") or "").strip()
        telegram = (company.get("telegram") or "").strip()
        offer_text = company.get("offer_text") or ""

        contact = email or telegram

        print(f"📧 Имитация отправки КП для {name} на {contact or 'контакт не указан'}...")
        print("--- Текст КП ---")
        print(offer_text if offer_text else "Текст КП отсутствует")
        print("----------------")

        if contact:
            try:
                update_company(company_id, status="sent")
                sent_count += 1
                print(f"✅ КП успешно отправлено для {name}")
            except Exception as error:
                print(f"Ошибка при обновлении статуса компании {name}: {error}")
        else:
            print(f"⚠️ Нет контактов для {name}")
            try:
                update_company(company_id, status="error")
            except Exception as error:
                print(f"Ошибка при обновлении статуса компании {name}: {error}")

        time.sleep(random.uniform(3, 5))

    print(f"Отправлено КП: {sent_count} из {total} компаний")


if __name__ == '__main__':
    send_offers(batch=5)
