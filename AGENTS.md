# Проект: Kubik Agent — автолидген из Яндекс.Карт

## Контекст
Локальный Python-агент для автоматического поиска компаний
в Яндекс.Картах и отправки им коммерческих предложений.
Запускается на ПК пользователя, без серверов и деплоя.
Пользователь — не разработчик, поэтому код максимально простой.

## Правила кода
- Все комментарии на русском языке
- Каждый файл запускается самостоятельно через if __name__ == '__main__'
- Ошибки логировать в консоль с понятным текстом на русском
- Паузы между запросами к сайтам: random 3-5 секунд
- Все ключи читать из файла .env через python-dotenv

## Стек
- Python 3.11+
- requests, python-dotenv, beautifulsoup4, streamlit, openai
- База: SQLite (файл leads.db, НЕ коммитить)
- Интерфейс: Streamlit (локально в браузере)

## Структура проекта
kubik-agent/
├── main_app.py          # Streamlit админка
├── db.py                # работа с SQLite
├── agents/
│   ├── agent_search.py  # поиск компаний через Яндекс.Карты API
│   ├── agent_scrape.py  # парсинг сайтов (email + telegram + текст)
│   ├── agent_writer.py  # генерация КП через LLM
│   └── agent_sender.py  # отправка (сначала симуляция)
├── .env.example         # образец переменных (без реальных ключей)
├── requirements.txt
└── AGENTS.md

## Переменные (.env, не коммитить)
YANDEX_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=

## Статусы лидов в БД
new → scraped → needs_approval → approved → sent
(также: no_site, error)
