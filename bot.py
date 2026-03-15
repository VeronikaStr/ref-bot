import random
import sqlite3
import logging
from datetime import date
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# ================= SETTINGS =================

API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

BOT_USERNAME = "CHERRYSPINBOT"

DB_NAME = "cherry_spin.db"

    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # ================= DATABASE =================

    def init_db():
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            last_bonus TEXT,
            ref_by INTEGER
        )
        """)

        conn.commit()
        conn.close()

    init_db()

    def get_user(user_id, username=None, ref=None):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cur.fetchone()

        if not user:
            cur.execute(
                "INSERT INTO users(user_id,username,ref_by) VALUES(?,?,?)",
                (user_id, username, ref)
            )
            conn.commit()

        conn.close()

    def add_balance(user_id, amount):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET balance=balance+? WHERE user_id=?",
            (amount, user_id)
        )

        conn.commit()
        conn.close()

    def get_balance(user_id):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        result = cur.fetchone()

        conn.close()

        if result:
            return result[0]

        return 0

    # ================= MENU =================

    def main_menu():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_hoop")],
                [InlineKeyboardButton(text="🎯 Дротики", callback_data="game_dart")],
                [InlineKeyboardButton(text="🎡 Колесо удачи", callback_data="wheel")],
                [InlineKeyboardButton(text="🎁 Открыть кейс", callback_data="case")],
                [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
                [InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="bonus")],
                [InlineKeyboardButton(text="👥 Реферальная ссылка", callback_data="ref")],
                [InlineKeyboardButton(text="🏆 Лидерборд", callback_data="top")]
            ]
        )

    # ================= START =================

    @dp.message(Command("start"))
    async def start(message: types.Message):

        args = message.text.split()

        ref = None

        if len(args) > 1:
            try:
                ref = int(args[1])
            except:
                pass

        get_user(message.from_user.id, message.from_user.username, ref)

        await message.answer(
            "🍒 <b>Cherry Spin Bot</b>\n\n"
            "Играй в мини‑игры и выигрывай ⭐\n\n"
            "Выбери действие:",
            reply_markup=main_menu()
        )

    # ================= BASKETBALL =================

    @dp.callback_query(F.data == "game_hoop")
    async def hoop(callback: CallbackQuery):

        dice = await bot.send_dice(callback.message.chat.id, emoji="🏀")

        if dice.dice.value == 5:

            win = random.randint(30, 80)

            add_balance(callback.from_user.id, win)

            await callback.message.answer(
                f"🔥 Попадание!\n\n"
                f"Ты выиграл <b>{win} ⭐</b>"
            )

        else:
            await callback.message.answer("😅 Мимо кольца!")

    # ================= DART =================

    @dp.callback_query(F.data == "game_dart")
    async def dart(callback: CallbackQuery):

        dice = await bot.send_dice(callback.message.chat.id, emoji="🎯")

        if dice.dice.value == 6:

            win = random.randint(40, 90)

            add_balance(callback.from_user.id, win)

            await callback.message.answer(
                f"🎯 BULLSEYE!\n\n"
                f"Награда: <b>{win} ⭐</b>"
            )

        else:
            await callback.message.answer("💨 Почти попал!")

    # ================= WHEEL =================

    @dp.callback_query(F.data == "wheel")
    async def wheel(callback: CallbackQuery):

        win = random.choice([0,10,20,50,100])

        if win == 0:

            await callback.message.answer("😅 Ничего не выпало")

        else:

            add_balance(callback.from_user.id, win)

            await callback.message.answer(
                f"🎡 Колесо остановилось!\n\n"
                f"Ты выиграл <b>{win} ⭐</b>"
            )

    # ================= CASE =================

    @dp.callback_query(F.data == "case")
    async def case(callback: CallbackQuery):

        prize = random.randint(10,100)

        add_balance(callback.from_user.id, prize)

        await callback.message.answer(
            f"🎁 Кейс открыт!\n\n"
            f"Ты получил <b>{prize} ⭐</b>"
        )

    # ================= DAILY BONUS =================

    @dp.callback_query(F.data == "bonus")
    async def bonus(callback: CallbackQuery):

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        today = str(date.today())

        cur.execute(
            "SELECT last_bonus FROM users WHERE user_id=?",
            (callback.from_user.id,)
        )

        last = cur.fetchone()[0]

        if last == today:

            await callback.message.answer(
                "⏳ Ты уже забирал бонус сегодня"
            )

        else:

            prize = random.randint(20,60)

            add_balance(callback.from_user.id, prize)

            cur.execute(
                "UPDATE users SET last_bonus=? WHERE user_id=?",
                (today, callback.from_user.id)
            )

            conn.commit()

            await callback.message.answer(
                f"🎁 Ежедневный бонус!\n\n"
                f"+<b>{prize} ⭐</b>"
            )

        conn.close()

    # ================= BALANCE =================

    @dp.callback_query(F.data == "balance")
    async def balance(callback: CallbackQuery):

        bal = get_balance(callback.from_user.id)

        await callback.message.answer(
            f"💰 Баланс: <b>{bal} ⭐</b>"
        )

    # ================= REFERRAL =================

    @dp.callback_query(F.data == "ref")
    async def ref(callback: CallbackQuery):

        link = f"https://t.me/{BOT_USERNAME}?start={callback.from_user.id}"

        await callback.message.answer(
            "👥 Приглашай друзей и получай бонусы!\n\n"
            f"{link}"
        )

    # ================= LEADERBOARD =================

    @dp.callback_query(F.data == "top")
    async def top(callback: CallbackQuery):

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "SELECT username,balance FROM users ORDER BY balance DESC LIMIT 10"
        )

        rows = cur.fetchall()

        conn.close()

        text = "🏆 <b>Топ игроков</b>\n\n"

        for i,row in enumerate(rows,1):

            name = row[0] if row[0] else "Игрок"

            text += f"{i}. @{name} — {row[1]} ⭐\n"

        await callback.message.answer(text)

    # ================= WEBHOOK =================

    async def webhook(request):

        data = await request.json()

        update = types.Update(**data)

        await dp.feed_update(bot, update)

        return Response()

    async def health(request):
        return PlainTextResponse("OK")

    async def startup():

        url = os.environ.get("RENDER_EXTERNAL_URL")

        if url:
            await bot.set_webhook(f"{url}/webhook")

    async def shutdown():

        await bot.delete_webhook()

    app = Starlette(
        routes=[
            Route("/webhook", webhook, methods=["POST"]),
            Route("/", health)
        ],
        on_startup=[startup],
        on_shutdown=[shutdown]
    )

    if __name__ == "__main__":

        port = int(os.environ.get("PORT",8000))

        uvicorn.run(app, host="0.0.0.0", port=port)

    # ============================================================
    # END OF FILE
    # ============================================================
