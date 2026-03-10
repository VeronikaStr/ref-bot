import os
import logging
import random
import sqlite3
from datetime import datetime, date
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)
from aiogram.client.default import DefaultBotProperties

# ============= НАСТРОЙКИ =============
API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise Exception("Ошибка: переменная окружения TELEGRAM_BOT_TOKEN не найдена!")

DB_NAME = "users.db"

# Ссылка на картинку-заглушку (замени на свою)
PRIZE_IMAGE_URL = "https://via.placeholder.com/400x200.png?text=Gift"

# ID твоего бота (для упоминания в заданиях)
BOT_USERNAME = "CHERRYSPINBOT"  # замени на свой юзернейм без @

# Задания (можно добавлять новые)
TASKS = {
    "task_comment": {
        "name": "📢 Оставить комментарий",
        "description": f"Оставь комментарий под любым постом в нашем канале (ссылка) с текстом «Крутой бот, всем советую @{BOT_USERNAME}» и отправь скриншот.",
        "reward": 50,
        "channel_link": "https://t.me/your_channel"  # замени на свой канал
    }
}
# ======================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ----- РАБОТА С БАЗОЙ ДАННЫХ -----
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Таблица пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            last_case_date TEXT,
            total_cases INTEGER DEFAULT 0
        )
    """)
    # Таблица выполненных заданий
    cur.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id INTEGER,
            task_id TEXT,
            completed_at TEXT,
            PRIMARY KEY (user_id, task_id)
        )
    """)
    # Таблица заданий, ожидающих проверки (пользователь нажал "Я выполнил" и должен прислать скрин)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pending_tasks (
            user_id INTEGER PRIMARY KEY,
            task_id TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id, username=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row is None:
        cur.execute("""
            INSERT INTO users (user_id, username, balance, last_case_date, total_cases)
            VALUES (?, ?, 0, NULL, 0)
        """, (user_id, username))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    conn.close()
    return row

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for key, value in kwargs.items():
        cur.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def add_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Функции для работы с заданиями
def is_task_completed(user_id, task_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
    row = cur.fetchone()
    conn.close()
    return row is not None

def get_pending_task(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT task_id FROM pending_tasks WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def set_pending_task(user_id, task_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("REPLACE INTO pending_tasks (user_id, task_id, created_at) VALUES (?, ?, ?)",
                (user_id, task_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def clear_pending_task(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM pending_tasks WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def mark_task_completed(user_id, task_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO completed_tasks (user_id, task_id, completed_at) VALUES (?, ?, ?)",
                (user_id, task_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Инициализация БД
init_db()

# ----- ГЛАВНОЕ МЕНЮ (СТАРТ) -----
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    get_user(user_id, username)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Открыть бесплатный кейс", callback_data="open_case")],
        [InlineKeyboardButton(text="📋 Задания", callback_data="tasks_list")],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🏆 Лидерборд", callback_data="leaderboard")],
    ])
    await message.answer(
        "🎲 <b>Добро пожаловать в игровой бот!</b>\n\n"
        "Каждый день ты можешь открывать бесплатный кейс и получать звёзды.\n"
        "Выполняй задания, чтобы заработать ещё больше!\n\n"
        "👇 Выбери действие:",
        reply_markup=kb
    )

# ----- ОТКРЫТИЕ КЕЙСА (без изменений) -----
@dp.callback_query(F.data == "open_case")
async def open_case(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        user = get_user(user_id)
        today = date.today().isoformat()
        last = user[3]

        if last == today:
            await callback.answer("Ты уже открывал кейс сегодня. Приходи завтра!", show_alert=True)
            return

        prize = random.randint(10, 100)
        new_balance = user[2] + prize
        new_total = user[4] + 1

        update_user(user_id, balance=new_balance, last_case_date=today, total_cases=new_total)

        # Вместо edit_text используем answer + новое сообщение
        await callback.answer()  # просто закрываем "часики" на кнопке
        await callback.message.answer(
            f"🎉 Ты открыл кейс и получил <b>{prize} звёзд</b>!\n"
            f"💰 Твой баланс: {new_balance} звёзд."
        )
    except Exception as e:
        logger.error(f"Ошибка в open_case: {e}")
        await callback.answer("Произошла ошибка. Попробуй позже.", show_alert=True)

# ----- СПИСОК ЗАДАНИЙ -----
@dp.callback_query(F.data == "tasks_list")
async def tasks_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    kb_buttons = []
    for task_id, task in TASKS.items():
        if not is_task_completed(user_id, task_id):
            kb_buttons.append([InlineKeyboardButton(text=task["name"], callback_data=f"task_{task_id}")])
    if not kb_buttons:
        await callback.message.edit_text("🎉 Ты выполнил все доступные задания! Жди новых.")
        return
    kb_buttons.append([InlineKeyboardButton(text="◀ Назад", callback_data="back_to_main")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await callback.message.edit_text("📋 <b>Доступные задания:</b>\nВыбери задание:", reply_markup=kb)
    await callback.answer()

# ----- ДЕТАЛИ ЗАДАНИЯ -----
@dp.callback_query(F.data.startswith("task_"))
async def task_detail(callback: CallbackQuery):
    task_id = callback.data.replace("task_", "")
    task = TASKS.get(task_id)
    if not task:
        await callback.answer("Задание не найдено")
        return
    # Проверяем, не выполнено ли уже
    if is_task_completed(callback.from_user.id, task_id):
        await callback.answer("Ты уже выполнил это задание!", show_alert=True)
        return

    text = (
        f"<b>{task['name']}</b>\n\n"
        f"{task['description']}\n\n"
        f"👇 <b>Награда:</b> {task['reward']} ⭐"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я выполнил", callback_data=f"done_{task_id}")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="tasks_list")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# ----- ПОЛЬЗОВАТЕЛЬ НАЖАЛ "Я ВЫПОЛНИЛ" -----
@dp.callback_query(F.data.startswith("done_"))
async def task_done(callback: CallbackQuery):
    task_id = callback.data.replace("done_", "")
    task = TASKS.get(task_id)
    if not task:
        await callback.answer("Ошибка")
        return
    user_id = callback.from_user.id

    # Проверяем, не выполнял ли уже
    if is_task_completed(user_id, task_id):
        await callback.answer("Ты уже получил награду за это задание!", show_alert=True)
        return

    # Проверяем, нет ли уже ожидающего задания
    pending = get_pending_task(user_id)
    if pending:
        await callback.answer("Сначала заверши предыдущее задание (отправь скриншот)!", show_alert=True)
        return

    # Устанавливаем ожидание скриншота
    set_pending_task(user_id, task_id)

    await callback.message.edit_text(
        f"📸 Отправь скриншот выполнения задания «{task['name']}».\n\n"
        "Я проверю и начислю звёзды в течение нескольких минут."
    )
    await callback.answer()

# ----- ОБРАБОТКА СКРИНШОТОВ -----
@dp.message(F.photo)
async def handle_screenshot(message: types.Message):
    user_id = message.from_user.id
    pending_task_id = get_pending_task(user_id)

    if not pending_task_id:
        await message.answer("У тебя нет активных заданий, ожидающих проверки. Сначала выбери задание в меню.")
        return

    task = TASKS.get(pending_task_id)
    if not task:
        # Ошибка, очищаем ожидание
        clear_pending_task(user_id)
        await message.answer("Произошла ошибка. Попробуй выбрать задание заново.")
        return

    # Начисляем награду
    add_balance(user_id, task["reward"])
    mark_task_completed(user_id, pending_task_id)
    clear_pending_task(user_id)

    # Отправляем подтверждение с картинкой
    await message.answer_photo(
        photo=PRIZE_IMAGE_URL,
        caption=(
            f"✅ <b>Задание выполнено!</b>\n\n"
            f"Ты получил <b>{task['reward']} ⭐</b>.\n"
            f"💰 Текущий баланс: {get_user(user_id)[2]} ⭐."
        )
    )

# ----- МОЙ БАЛАНС -----
@dp.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"💰 <b>Твой баланс:</b> {user[2]} звёзд.\n"
        f"📦 Всего открыто кейсов: {user[4]}.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_main")]
        ])
    )
    await callback.answer()

# ----- ЛИДЕРБОРД -----
@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):
    top = get_top_users(10)
    if not top:
        text = "Пока нет участников."
    else:
        text = "<b>🏆 Топ-10 игроков:</b>\n\n"
        for i, (uid, uname, bal) in enumerate(top, 1):
            name = uname or f"ID {uid}"
            text += f"{i}. @{name} — {bal} ⭐\n"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_main")]
    ]))
    await callback.answer()

# ----- ВОЗВРАТ В ГЛАВНОЕ МЕНЮ -----
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Открыть бесплатный кейс", callback_data="open_case")],
        [InlineKeyboardButton(text="📋 Задания", callback_data="tasks_list")],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🏆 Лидерборд", callback_data="leaderboard")],
    ])
    await callback.message.edit_text(
        "🎲 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=kb
    )
    await callback.answer()

# ----- ВЕБ-СЕРВЕР ДЛЯ RENDER (WEBHOOK) -----
async def telegram_webhook(request):
    update = types.Update(**(await request.json()))
    await dp.feed_update(bot, update)
    return Response()

async def healthcheck(request):
    return PlainTextResponse("OK")

async def startup():
    webhook_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not webhook_url:
        logger.error("RENDER_EXTERNAL_URL не задан!")
        return
    await bot.set_webhook(f"{webhook_url}/webhook")
    logger.info(f"Вебхук установлен на {webhook_url}/webhook")

async def shutdown():
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Вебхук удалён, сессия закрыта.")

app = Starlette(
    routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/healthcheck", healthcheck, methods=["GET"]),
        Route("/", healthcheck, methods=["GET"]),
    ],
    on_startup=[startup],
    on_shutdown=[shutdown],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

