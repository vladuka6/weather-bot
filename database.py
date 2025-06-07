import sqlite3
from config import DB_NAME

def init_db():
    """Ініціалізація таблиці user_settings, якщо не створена."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            city TEXT,
            notify_times TEXT
        );
    """)
    conn.commit()
    conn.close()

def get_user_settings(user_id: int):
    """Повертає (city, notify_times) для заданого user_id або (None, None)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT city, notify_times FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return (row[0], row[1]) if row else (None, None)

def set_city(user_id: int, city: str):
    """Зберігає або оновлює місто користувача."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_settings (user_id, city, notify_times) VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET city=excluded.city
    """, (user_id, city, None))  # notify_times залишається None, якщо не встановлено
    conn.commit()
    conn.close()

def set_notify_times(user_id: int, notify_times: str):
    """Зберігає або оновлює список часів сповіщень (формат HH:MM через кому)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_settings (user_id, notify_times) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET notify_times=excluded.notify_times
    """, (user_id, notify_times))
    conn.commit()
    conn.close()

def get_all_users():
    """Повертає список (user_id, city, notify_times) для всіх користувачів."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, city, notify_times FROM user_settings")
    rows = cursor.fetchall()
    conn.close()
    return rows