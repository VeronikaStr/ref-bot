import asyncpg
import logging
from config import DATABASE_URL

pool = None

async def connect():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    # Создаём таблицу, если её нет
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                balance INT DEFAULT 0,
                exp INT DEFAULT 0,
                level INT DEFAULT 1
            )
        """)
    logging.info("✅ Таблица users проверена/создана")

# Остальные функции (add_balance, get_user и т.д.) остаются без изменений

async def create_user(user_id):

    async with pool.acquire() as conn:

        await conn.execute("""
        INSERT INTO users(user_id,balance,exp,level)
        VALUES($1,100,0,1)
        ON CONFLICT DO NOTHING
        """,user_id)

async def add_balance(user,amount):

    async with pool.acquire() as conn:

        await conn.execute(
            "UPDATE users SET balance=balance+$1 WHERE user_id=$2",
            amount,user
        )

async def get_user(user):

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            "SELECT * FROM users WHERE user_id=$1",
            user
        )
