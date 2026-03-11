import os
import sys
import logging
import random
import sqlite3
import traceback
from datetime import datetime, date
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, Update
)
from aiogram.client.default import DefaultBotProperties

# ============= НАСТРОЙКИ =============
API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise Exception("❌ Ошибка: переменная окружения TELEGRAM_BOT_TOKEN не найдена!")

DB_NAME = "users.db"
PRIZE_IMAGE_URL = "https://via.placeholder.com/400x200.png?text=Gift"
BOT_USERNAME = "CHERRYSPINBOT"  # замените на свой юзернейм без @

TASKS = {
    "task_comment": {
        "name": "📢 Оставить комментарий",
        "description": f"Оставь комментарий под любым постом с текстом «Крутой бот, всем советую @{BOT_USERNAME}» и отправь скриншот.",
        "reward": 50,
    }
}
# ======================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальный обработчик необработанных исключений
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("💥 НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = global_exception_handler

# Инициализация бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ----- ГЛОБАЛЬНЫЙ ЛОГГЕР ВСЕХ ОБНОВЛЕНИЙ -----
@dp.update.outer_middleware()
async def log_all_updates(handler, event: Update, data):
    logger.info(f"📥 Входящее обновление: {event}")
    if event.callback_query:
        cq = event.callback_query
        logger.info(f"   CallbackQuery: data='{cq.data}', user={cq.from_user.id}")
    try:
        return await handler(event, data)
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке обновления: {e}", exc_info=True)
        raise

# ----- РАБОТА С БАЗОЙ ДАННЫХ -----
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                last_case_date TEXT,
                total_cases INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS completed_tasks (
                user_id INTEGER,
                task_id TEXT,
                completed_at TEXT,
                PRIMARY KEY (user_id, task_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pending_tasks (
                user_id INTEGER PRIMARY KEY,
                task_id TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при инициализации БД: {e}", exc_info=True)
        raise

def get_user(user_id, username=None):
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в get_user: {e}", exc_info=True)
        return None

def add_balance(user_id, amount):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в add_balance: {e}", exc_info=True)

def update_user(user_id, **kwargs):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        for key, value in kwargs.items():
            cur.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в update_user: {e}", exc_info=True)

def get_top_users(limit=10):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Ошибка в get_top_users: {e}", exc_info=True)
        return []

def is_task_completed(user_id, task_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        row = cur.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        logger.error(f"Ошибка в is_task_completed: {e}", exc_info=True)
        return False

def get_pending_task(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT task_id FROM pending_tasks WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Ошибка в get_pending_task: {e}", exc_info=True)
        return None

def set_pending_task(user_id, task_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("REPLACE INTO pending_tasks (user_id, task_id, created_at) VALUES (?, ?, ?)",
                    (user_id, task_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в set_pending_task: {e}", exc_info=True)

def clear_pending_task(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM pending_tasks WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в clear_pending_task: {e}", exc_info=True)

def mark_task_completed(user_id, task_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO completed_tasks (user_id, task_id, completed_at) VALUES (?, ?, ?)",
                    (user_id, task_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка в mark_task_completed: {e}", exc_info=True)

init_db()

# ----- ГЛАВНОЕ МЕНЮ (СТАРТ) -----
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        get_user(user_id, username)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏀 Бросок в кольцо", callback_data="game_hoop")],
            [InlineKeyboardButton(text="🎯 Бросок в цель", callback_data="game_dart")],
        ])

        await message.answer(
            "🎯 <b>Испытайте удачу!</b>\n\n"
            "Выберите, бросить мяч в кольцо или дротик в цель, чтобы получить приз 😊😍",
            reply_markup=kb
        )
        logger.info(f"✅ /start для пользователя {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в cmd_start: {e}", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")

# ----- ОБРАБОТЧИКИ ИГР -----
@dp.callback_query(F.data == "game_hoop")
async def game_hoop(callback: CallbackQuery):
    try:
        logger.info(f"🔥 game_hoop callback от {callback.from_user.id}")
        await callback.answer()
        user_id = callback.from_user.id
        user = get_user(user_id)

        if random.random() < 0.4:
            prize = random.randint(20, 50)
            add_balance(user_id, prize)
            new_balance = user[2] + prize
            await callback.message.answer(
                f"✅ <b>Попадание!</b> Ты выиграл <b>{prize} ⭐</b>!\n"
                f"💰 Твой баланс: {new_balance} ⭐."
            )
            await show_game_menu(callback.message)
        else:
            await callback.message.answer(
                "😅 <b>Промах!</b> Попробуй ещё раз."
            )
    except Exception as e:
        logger.error(f"❌ Ошибка в game_hoop: {e}", exc_info=True)
        await callback.message.answer("Ошибка в игре. Попробуйте ещё раз.")

@dp.callback_query(F.data == "game_dart")
async def game_dart(callback: CallbackQuery):
    try:
        logger.info(f"🔥 game_dart callback от {callback.from_user.id}")
        await callback.answer()
        user_id = callback.from_user.id
        user = get_user(user_id)

        if random.random() < 0.45:
            prize = random.randint(20, 50)
            add_balance(user_id, prize)
            new_balance = user[2] + prize
            await callback.message.answer(
                f"✅ <b>Попадание!</b> Ты выиграл <b>{prize} ⭐</b>!\n"
                f"💰 Твой баланс: {new_balance} ⭐."
            )
            await show_game_menu(callback.message)
        else:
            await callback.message.answer(
                "😅 <b>Промах!</b> Попробуй ещё раз."
            )
    except Exception as e:
        logger.error(f"❌ Ошибка в game_dart: {e}", exc_info=True)
        await callback.message.answer("Ошибка в игре. Попробуйте ещё раз.")

async def show_game_menu(message: types.Message):
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Открыть кейс", callback_data="open_case")],
            [InlineKeyboardButton(text="📋 Задания", callback_data="tasks_list")],
            [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
            [InlineKeyboardButton(text="🏆 Лидерборд", callback_data="leaderboard")],
            [InlineKeyboardButton(text="🎯 Играть ещё", callback_data="play_again")]
        ])
        await message.answer("Выбери действие:", reply_markup=kb)
    except Exception as e:
        logger.error(f"Ошибка в show_game_menu: {e}", exc_info=True)

@dp.callback_query(F.data == "play_again")
async def play_again(callback: CallbackQuery):
    try:
        logger.info(f"play_again callback от {callback.from_user.id}")
        await callback.answer()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏀 Бросок в кольцо", callback_data="game_hoop")],
            [InlineKeyboardButton(text="🎯 Бросок в цель", callback_data="game_dart")],
        ])
        await callback.message.answer(
            "🎯 <b>Испытайте удачу!</b>\n\n"
            "Выберите игру:",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в play_again: {e}", exc_info=True)

# ----- ОТКРЫТИЕ КЕЙСА -----
@dp.callback_query(F.data == "open_case")
async def open_case(callback: CallbackQuery):
    try:
        logger.info(f"open_case callback от {callback.from_user.id}")
        await callback.answer()
        user_id = callback.from_user.id
        user = get_user(user_id)
        if not user:
            await callback.message.answer("Ошибка получения пользователя.")
            return
        today = date.today().isoformat()
        last = user[3]

        if last == today:
            await callback.message.answer("Ты уже открывал кейс сегодня. Приходи завтра!")
            return

        prize = random.randint(10, 100)
        add_balance(user_id, prize)
        update_user(user_id, last_case_date=today, total_cases=user[4]+1)

        await callback.message.answer(
            f"🎉 Ты открыл кейс и получил <b>{prize} звёзд</b>!\n"
            f"💰 Твой баланс: {user[2] + prize} звёзд."
        )
    except Exception as e:
        logger.error(f"Ошибка в open_case: {e}", exc_info=True)

# ----- ЗАДАНИЯ -----
@dp.callback_query(F.data == "tasks_list")
async def tasks_list(callback: CallbackQuery):
    try:
        logger.info(f"tasks_list callback от {callback.from_user.id}")
        await callback.answer()
        user_id = callback.from_user.id
        kb_buttons = []
        for task_id, task in TASKS.items():
            if not is_task_completed(user_id, task_id):
                kb_buttons.append([InlineKeyboardButton(text=task["name"], callback_data=f"task_{task_id}")])

        if not kb_buttons:
            await callback.message.edit_text("🎉 Ты выполнил все доступные задания!")
            return

        kb_buttons.append([InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await callback.message.edit_text("📋 <b>Доступные задания:</b>", reply_markup=kb)
    except Exception as e:
        logger.error(f"Ошибка в tasks_list: {e}", exc_info=True)

@dp.callback_query(F.data.startswith("task_"))
async def task_detail(callback: CallbackQuery):
    try:
        logger.info(f"task_detail callback от {callback.from_user.id}, data={callback.data}")
        await callback.answer()
        task_id = callback.data.replace("task_", "")
        task = TASKS.get(task_id)
        if not task:
            await callback.message.answer("Ошибка")
            return

        if is_task_completed(callback.from_user.id, task_id):
            await callback.message.answer("Ты уже выполнил это задание!")
            return

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я выполнил", callback_data=f"done_{task_id}")],
            [InlineKeyboardButton(text="◀ Назад", callback_data="tasks_list")]
        ])
        await callback.message.edit_text(
            f"<b>{task['name']}</b>\n\n{task['description']}\n\nНаграда: {task['reward']} ⭐",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в task_detail: {e}", exc_info=True)

@dp.callback_query(F.data.startswith("done_"))
async def task_done(callback: CallbackQuery):
    try:
        logger.info(f"task_done callback от {callback.from_user.id}, data={callback.data}")
        await callback.answer()
        task_id = callback.data.replace("done_", "")
        task = TASKS.get(task_id)
        user_id = callback.from_user.id

        if is_task_completed(user_id, task_id):
            await callback.message.answer("Уже выполнено!")
            return

        if get_pending_task(user_id):
            await callback.message.answer("Сначала отправь скриншот для предыдущего задания!")
            return

        set_pending_task(user_id, task_id)
        await callback.message.edit_text(
            f"📸 Отправь скриншот выполнения задания «{task['name']}»."
        )
    except Exception as e:
        logger.error(f"Ошибка в task_done: {e}", exc_info=True)

# ----- ОБРАБОТКА СКРИНШОТОВ -----
@dp.message(F.photo)
async def handle_screenshot(message: types.Message):
    try:
        logger.info(f"Получено фото от {message.from_user.id}")
        user_id = message.from_user.id
        pending_task_id = get_pending_task(user_id)

        if not pending_task_id:
            await message.answer("У тебя нет активных заданий.")
            return

        task = TASKS.get(pending_task_id)
        if not task:
            clear_pending_task(user_id)
            await message.answer("Ошибка, попробуй снова.")
            return

        add_balance(user_id, task["reward"])
        mark_task_completed(user_id, pending_task_id)
        clear_pending_task(user_id)

        await message.answer_photo(
            photo=PRIZE_IMAGE_URL,
            caption=f"✅ Задание выполнено! +{task['reward']} ⭐"
        )
    except Exception as e:
        logger.error(f"Ошибка в handle_screenshot: {e}", exc_info=True)

# ----- БАЛАНС -----
@dp.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    try:
        logger.info(f"balance callback от {callback.from_user.id}")
        await callback.answer()
        user = get_user(callback.from_user.id)
        if not user:
            await callback.message.answer("Ошибка получения пользователя.")
            return
        await callback.message.edit_text(
            f"💰 Баланс: {user[2]} ⭐\n📦 Кейсов: {user[4]}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка в show_balance: {e}", exc_info=True)

# ----- ЛИДЕРБОРД -----
@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):
    try:
        logger.info(f"leaderboard callback от {callback.from_user.id}")
        await callback.answer()
        top = get_top_users(10)
        if not top:
            text = "Пока нет участников."
        else:
            text = "<b>🏆 Топ-10:</b>\n\n"
            for i, (uid, uname, bal) in enumerate(top, 1):
                name = uname or f"ID {uid}"
                text += f"{i}. @{name} — {bal} ⭐\n"
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Назад", callback_data="back_to_menu")]
        ]))
    except Exception as e:
        logger.error(f"Ошибка в leaderboard: {e}", exc_info=True)

# ----- КНОПКА НАЗАД (в меню после игры) -----
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    try:
        logger.info(f"back_to_menu callback от {callback.from_user.id}")
        await callback.answer()
        await show_game_menu(callback.message)
    except Exception as e:
        logger.error(f"Ошибка в back_to_menu: {e}", exc_info=True)

# ----- ВЕБ-СЕРВЕР ДЛЯ RENDER -----
async def telegram_webhook(request):
    try:
        update = types.Update(**(await request.json()))
        await dp.feed_update(bot, update)
        return Response()
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook: {e}", exc_info=True)
        return Response(status_code=500)

async def healthcheck(request):
    return PlainTextResponse("OK")

async def startup():
    logger.info("▶️ Запуск startup()...")
    try:
        webhook_url = os.environ.get("RENDER_EXTERNAL_URL")
        if not webhook_url:
            logger.error("❌ RENDER_EXTERNAL_URL не задан!")
            return

        # Получаем информацию о текущем вебхуке
        webhook_info = await bot.get_webhook_info()
        current_url = webhook_info.url
        expected_url = f"{webhook_url}/webhook"

        if current_url != expected_url:
            logger.info(f"🔄 Вебхук не совпадает (текущий: {current_url}, ожидаемый: {expected_url}), переустанавливаю...")
            await bot.set_webhook(
                expected_url,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"✅ Вебхук установлен на {expected_url} (разрешены message и callback_query)")
        else:
            logger.info(f"✅ Вебхук уже корректен: {current_url}")

        logger.info("✅ startup() завершён")
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка в startup: {e}", exc_info=True)
        raise

async def shutdown():
    logger.info("🛑 Запуск shutdown()...")
    try:
        await bot.delete_webhook()
        await bot.session.close()
        logger.info("✅ Вебхук удалён, сессия закрыта")
    except Exception as e:
        logger.error(f"Ошибка в shutdown: {e}", exc_info=True)

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
