import sqlite3
from contextlib import closing
import datetime
from config import DATABASE_PATH

# Инициализация базы данных
def init_db():
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                daily_bonus_time TEXT,
                referrer_id INTEGER,
                referrals INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

# Регистрация нового пользователя
def add_user(user_id, username, referrer_id=None):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO users (user_id, username, balance, xp, level, referrer_id, referrals)
                VALUES (?, ?, 0, 0, 1, ?, 0)
            ''', (user_id, username, referrer_id))
            conn.commit()
            return True
        return False

# Получение данных пользователя
def get_user(user_id):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        return cursor.fetchone()

# Обновление баланса
def update_balance(user_id, amount):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id=?', (amount, user_id))
        conn.commit()

# Обновление XP и уровня
def add_xp(user_id, amount):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT xp, level FROM users WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        if row:
            xp, level = row
            xp += amount
            new_level = level
            if xp >= level * 100:
                new_level += 1
                xp = xp - level * 100
            cursor.execute('UPDATE users SET xp=?, level=? WHERE user_id=?', (xp, new_level, user_id))
            conn.commit()

# Обновление времени последнего ежедневного бонуса
def set_daily_bonus_time(user_id, time):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET daily_bonus_time=? WHERE user_id=?', (time, user_id))
        conn.commit()

# Получение времени последнего бонуса
def get_daily_bonus_time(user_id):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT daily_bonus_time FROM users WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return datetime.datetime.fromisoformat(row[0])
        return None

# Лидерборд
def get_leaderboard(limit=10):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, balance FROM users ORDER BY balance DESC LIMIT ?', (limit,))
        return cursor.fetchall()