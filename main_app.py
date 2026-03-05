# main_app.py
# Локальная веб-админка на Streamlit для управления всеми агентами лидогенерации
# Запуск: streamlit run main_app.py

import streamlit as st
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Импорт агентов и базы данных
try:
    from agents.agent_search import search_and_save
except ImportError as e:
    st.error(f"❌ Ошибка импорта agent_search: {e}")
    search_and_save = None

try:
    from agents.agent_scrape import scrape_new_companies
except ImportError as e:
    st.error(f"❌ Ошибка импорта agent_scrape: {e}")
    scrape_new_companies = None

try:
    from agents.agent_writer import generate_offers
except ImportError as e:
    st.error(f"❌ Ошибка импорта agent_writer: {e}")
    generate_offers = None

try:
    from agents.agent_sender import send_offers as send_approved
except ImportError as e:
    st.error(f"❌ Ошибка импорта agent_sender: {e}")
    send_approved = None

try:
    from db import get_companies, get_companies_by_status, update_company, get_company
except ImportError as e:
    st.error(f"❌ Ошибка импорта db: {e}")
    get_companies = get_companies_by_status = update_company = get_company = None

# Константы для быстрого выбора районов Москвы
MOSCOW_DISTRICTS = {
    "ЦАО": "37.55,55.70~37.72,55.79",
    "САО": "37.35,55.79~37.65,55.90",
    "СВАО": "37.60,55.79~37.90,55.92",
    "ВАО": "37.65,55.72~37.95,55.85",
    "ЮВАО": "37.65,55.65~37.95,55.75",
    "ЮАО": "37.50,55.60~37.75,55.72",
    "ЮЗАО": "37.30,55.62~37.60,55.74",
    "ЗАО": "37.25,55.70~37.55,55.82",
    "СЗАО": "37.25,55.78~37.55,55.90",
    "Ввести вручную": ""
}

# Заголовок страницы
st.set_page_config(page_title="Кубик Медиа - Агент лидогенерации", page_icon="🎯", layout="wide")
st.title("🎯 Кубик Медиа — Агент лидогенерации")

# Боковое меню
st.sidebar.title("Навигация")
section = st.sidebar.radio(
    "Выберите раздел:",
    ["🔍 Поиск", "📋 База лидов", "✏️ Модерация КП", "⚙️ Управление"]
)

# ============================================================
# Раздел 1 — "🔍 Поиск лидов"
# ============================================================
if section == "🔍 Поиск":
    st.header("🔍 Поиск лидов")
    
    # Тип бизнеса
    business_type = st.text_input(
        "Тип бизнеса",
        placeholder="например: кафе, стоматология, фитнес"
    )
    
    # Быстрый выбор района
    district = st.selectbox(
        "Быстрый выбор района Москвы",
        list(MOSCOW_DISTRICTS.keys())
    )
    
    # Поле ввода bbox
    default_bbox = MOSCOW_DISTRICTS.get(district, "")
    bbox = st.text_input(
        "Область поиска (bbox)",
        value=default_bbox,
        placeholder="37.55,55.70~37.72,55.79"
    )
    st.caption("Координаты прямоугольника: lon1,lat1~lon2,lat2 (нижний левый ~ верхний правый)")
    
    # Кнопка поиска
    if st.button("🔍 Найти компании"):
        if not business_type:
            st.error("⚠️ Укажите тип бизнеса")
        elif not bbox:
            st.error("⚠️ Укажите область поиска (bbox)")
        elif search_and_save is None:
            st.error("❌ Модуль agent_search не загружен")
        else:
            try:
                with st.spinner("Ищем компании..."):
                    count = search_and_save(query=business_type, bbox=bbox)
                st.success(f"✅ Добавлено {count} компаний")
            except Exception as e:
                st.error(f"❌ Ошибка при поиске: {e}")

# ============================================================
# Раздел 2 — "📋 База лидов"
# ============================================================
elif section == "📋 База лидов":
    st.header("📋 База лидов")
    
    if get_companies is None or get_companies_by_status is None:
        st.error("❌ Модуль db не загружен")
    else:
        # Метрики по статусам
        try:
            all_companies = get_companies()
            statuses = ["new", "scraped", "needs_approval", "approved", "sent"]
            counts = {s: len([c for c in all_companies if c.get("status") == s]) for s in statuses}
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("New", counts["new"])
            col2.metric("Scraped", counts["scraped"])
            col3.metric("Needs Approval", counts["needs_approval"])
            col4.metric("Approved", counts["approved"])
            col5.metric("Sent", counts["sent"])
        except Exception as e:
            st.warning(f"⚠️ Не удалось загрузить метрики: {e}")
        
        # Фильтр по статусу
        status_filter = st.selectbox(
            "Фильтр по статусу",
            ["Все", "new", "scraped", "needs_approval", "approved", "sent", "no_site", "error"]
        )
        
        # Получение данных
        try:
            if status_filter == "Все":
                companies = get_companies()
            else:
                companies = get_companies_by_status(status_filter)
            
            # Таблица
            if companies:
                import pandas as pd
                df = pd.DataFrame(companies)
                # Выбираем нужные колонки
                columns = ["name", "category", "address", "phone", "website", "email", "telegram", "status"]
                display_cols = [c for c in columns if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True)
                st.caption(f"Показано {len(companies)} записей")
            else:
                st.info("Нет данных для отображения")
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке данных: {e}")

# ============================================================
# Раздел 3 — "✏️ Модерация КП"
# ============================================================
elif section == "✏️ Модерация КП":
    st.header("✏️ Модерация КП")
    
    if get_companies_by_status is None or update_company is None:
        st.error("❌ Модуль db не загружен")
    else:
        try:
            companies = get_companies_by_status("needs_approval")
            
            if not companies:
                st.info("Нет КП на модерации")
            else:
                # Кнопка одобрить все
                if st.button("✅ Одобрить все без изменений"):
                    for c in companies:
                        update_company(c["id"], {"status": "approved"})
                    st.success(f"✅ Одобрено {len(companies)} КП")
                    st.rerun()
                
                # Модерация каждой компании
                for company in companies:
                    with st.expander(f"{company.get('name', 'Без названия')} — {company.get('category', 'Категория не указана')}"):
                        st.write(f"**Адрес:** {company.get('address', 'Не указан')}")
                        st.write(f"**Телефон:** {company.get('phone', 'Не указан')}")
                        st.write(f"**Сайт:** {company.get('website', 'Не указан')}")
                        
                        # Редактирование текста КП
                        offer_text = st.text_area(
                            "Текст коммерческого предложения:",
                            value=company.get("offer_text", ""),
                            height=200,
                            key=f"offer_{company['id']}"
                        )
                        
                        # Кнопка одобрить
                        if st.button(f"✅ Одобрить", key=f"approve_{company['id']}"):
                            update_company(company["id"], {
                                "offer_text": offer_text,
                                "status": "approved"
                            })
                            st.success("Одобрено!")
                            st.rerun()
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке КП: {e}")

# ============================================================
# Раздел 4 — "⚙️ Управление агентами"
# ============================================================
elif section == "⚙️ Управление":
    st.header("⚙️ Управление агентами")
    
    col1, col2, col3 = st.columns(3)
    
    # Кнопка 1: Собрать контакты
    with col1:
        if st.button("🌐 Собрать контакты с сайтов"):
            if scrape_new_companies is None:
                st.error("❌ Модуль agent_scrape не загружен")
            else:
                try:
                    with st.spinner("Собираем контакты..."):
                        count = scrape_new_companies(batch=20)
                    st.success(f"✅ Обработано {count} компаний")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
    
    # Кнопка 2: Сгенерировать КП
    with col2:
        if st.button("🤖 Сгенерировать КП"):
            if generate_offers is None:
                st.error("❌ Модуль agent_writer не загружен")
            else:
                try:
                    with st.spinner("Генерируем КП..."):
                        count = generate_offers(batch=20)
                    st.success(f"✅ Сгенерировано {count} КП")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
    
    # Кнопка 3: Симулировать рассылку
    with col3:
        if st.button("📤 Симулировать рассылку"):
            if send_approved is None:
                st.error("❌ Модуль agent_sender не загружен")
            else:
                try:
                    with st.spinner("Отправляем КП..."):
                        count = send_approved(batch=10)
                    st.success(f"✅ Отправлено {count} КП")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
    
    # Статистика
    st.subheader("📊 Текущая статистика")
    try:
        from db import get_stats
        stats = get_stats()
        if stats:
            import pandas as pd
            df_stats = pd.DataFrame([stats])
            st.table(df_stats)
        else:
            st.info("Статистика пока недоступна")
    except ImportError:
        st.warning("⚠️ Функция get_stats() не найдена в модуле db")
    except Exception as e:
        st.warning(f"⚠️ Не удалось загрузить статистику: {e}")
