import sqlite3
from typing import Optional, Dict

def init_db() -> None:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            qr_code_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def save_user(telegram_id: int, name: str, phone: str, gender: str, birth_date: str, qr_code_path: str) -> None:
    print(f"Saving user: {telegram_id}, {name}, {phone}, {gender}, {birth_date}, {qr_code_path}")  # Логирование
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (telegram_id, name, phone, gender, birth_date, qr_code_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (telegram_id, name, phone, gender, birth_date, qr_code_path))
    conn.commit()
    conn.close()
    print(f"User {telegram_id} saved successfully")

def get_user_data(telegram_id: int) -> Optional[Dict[str, str]]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('SELECT name, phone, gender, birth_date, qr_code_path FROM users WHERE telegram_id = ?', (telegram_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return {
            'name': user_data[0],
            'phone': user_data[1],
            'gender': user_data[2],
            'birth_date': user_data[3],
            'qr_code_path': user_data[4]
        }
    return None

def get_qr_code(telegram_id: int) -> Optional[str]:
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('SELECT qr_code_path FROM users WHERE telegram_id = ?', (telegram_id,))
    qr_code_path = c.fetchone()
    conn.close()
    if qr_code_path:
        return qr_code_path[0]
    return None
