import asyncpg
from config import DATABASE_URL

pool=None

async def connect():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

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