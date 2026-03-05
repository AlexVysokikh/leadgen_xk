"""Модуль для работы с локальной базой данных SQLite."""

import sqlite3
from datetime import datetime

DB_PATH = "leads.db"


def get_connection():
    """Создаёт и возвращает подключение к базе данных."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Создаёт таблицу companies, если она ещё не существует."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category TEXT,
                    address TEXT,
                    phone TEXT,
                    website TEXT,
                    email TEXT,
                    telegram TEXT,
                    website_text TEXT,
                    offer_text TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TEXT
                )
                """
            )
            conn.commit()
    except sqlite3.Error as error:
        print(f"Ошибка при создании базы данных: {error}")


def insert_company(name, category, address, phone, website):
    """Добавляет компанию в базу, если не найден дубль по связке website + name."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем, существует ли уже компания с таким же названием и сайтом
            cursor.execute(
                "SELECT id FROM companies WHERE website = ? AND name = ? LIMIT 1",
                (website, name),
            )
            existing = cursor.fetchone()
            if existing:
                return False

            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO companies (
                    name,
                    category,
                    address,
                    phone,
                    website,
                    email,
                    telegram,
                    website_text,
                    offer_text,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    category,
                    address,
                    phone,
                    website,
                    "",
                    "",
                    "",
                    "",
                    "new",
                    created_at,
                ),
            )
            conn.commit()
            return True
    except sqlite3.Error as error:
        print(f"Ошибка при добавлении компании: {error}")
        return False


def update_company(company_id, **fields):
    """Обновляет переданные поля компании по её id."""
    if not fields:
        return

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Формируем безопасный SQL-запрос из переданных полей
            column_names = list(fields.keys())
            values = [fields[column] for column in column_names]
            set_clause = ", ".join([f"{column} = ?" for column in column_names])

            query = f"UPDATE companies SET {set_clause} WHERE id = ?"
            cursor.execute(query, values + [company_id])
            conn.commit()
    except sqlite3.Error as error:
        print(f"Ошибка при обновлении компании id={company_id}: {error}")


def _rows_to_dicts(rows):
    """Преобразует строки из SQLite в список словарей."""
    companies = []
    for row in rows:
        companies.append(
            {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "address": row[3],
                "phone": row[4],
                "website": row[5],
                "email": row[6],
                "telegram": row[7],
                "website_text": row[8],
                "offer_text": row[9],
                "status": row[10],
                "created_at": row[11],
            }
        )
    return companies


def get_companies_by_status(status, limit=100):
    """Возвращает компании нужного статуса в виде списка словарей."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    category,
                    address,
                    phone,
                    website,
                    email,
                    telegram,
                    website_text,
                    offer_text,
                    status,
                    created_at
                FROM companies
                WHERE status = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (status, limit),
            )
            rows = cursor.fetchall()
            return _rows_to_dicts(rows)
    except sqlite3.Error as error:
        print(f"Ошибка при получении компаний со статусом '{status}': {error}")
        return []


def get_all_companies(limit=500):
    """Возвращает все компании в виде списка словарей."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    category,
                    address,
                    phone,
                    website,
                    email,
                    telegram,
                    website_text,
                    offer_text,
                    status,
                    created_at
                FROM companies
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return _rows_to_dicts(rows)
    except sqlite3.Error as error:
        print(f"Ошибка при получении списка компаний: {error}")
        return []


if __name__ == '__main__':
    init_db()
    print("База данных создана успешно")
