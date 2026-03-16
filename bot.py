import logging
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn
import os

from config import TELEGRAM_BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, LOG_LEVEL
from database import init_db, add_user, get_user, update_balance, set_daily_bonus_time, get_daily_bonus_time, get_leaderboard
from keyboards import main_menu, games_menu
from games import play_dice_game, spin_wheel, open_case, risk_game

# Логирование
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Инициализация базы
init_db()

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    referrer_id = None
    # Проверка реферального параметра
    if message.get_args().isdigit():
        referrer_id = int(message.get_args())
    added = add_user(message.from_user.id, message.from_user.username, referrer_id)
    text = "Добро пожаловать в CHERRYSPINBOT! 🎮" if added else "С возвращением!"
    await message.answer(text, reply_markup=main_menu())

# Команда /balance
@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    user = get_user(message.from_user.id)
    if user:
        balance = user[2]
        await message.answer(f"💰 Ваш баланс: {balance} монет")
    else:
        await message.answer("❌ Пользователь не найден. Используйте /start")

# Callback меню
@dp.callback_query()
async def callback_handler(query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "games":
        await query.message.edit_text("Выберите игру:", reply_markup=games_menu())
    elif data == "balance":
        user = get_user(user_id)
        await query.message.edit_text(f"💰 Баланс: {user[2]} монет", reply_markup=main_menu())
    elif data == "daily_bonus":
        last_time = get_daily_bonus_time(user_id)
        now = datetime.datetime.utcnow()
        if not last_time or (now - last_time).total_seconds() > 86400:
            reward = 100
            update_balance(user_id, reward)
            set_daily_bonus_time(user_id, now.isoformat())
            await query.message.edit_text(f"🎁 Вы получили ежедневный бонус: {reward} монет!", reply_markup=main_menu())
        else:
            remaining = 24*3600 - (now - last_time).total_seconds()
            await query.message.edit_text(f"⏳ Бонус уже получен. Осталось: {int(remaining//3600)}ч {int((remaining%3600)//60)}м", reply_markup=main_menu())
    elif data == "leaderboard":
        board = get_leaderboard()
        text = "🏆 Лидерборд:\n"
        for i, (username, balance) in enumerate(board, start=1):
            text += f"{i}. {username}: {balance} монет\n"
        await query.message.edit_text(text, reply_markup=main_menu())
    elif data.startswith("game_"):
        if data in ["game_basketball", "game_darts", "game_bowling", "game_slot"]:
            game_map = {
                "game_basketball": "basketball",
                "game_darts": "darts",
                "game_bowling": "bowling",
                "game_slot": "slot"
            }
            msg = await query.message.answer("🎲 Играем...")
            result = await play_dice_game(user_id, msg, game_map[data])
            await query.message.answer(result)
        elif data == "game_wheel":
            result = spin_wheel(user_id)
            await query.message.answer(result)
        elif data == "game_cases":
            result = open_case(user_id)
            await query.message.answer(result)
        elif data == "game_risk":
            amount = 50  # ставка по умолчанию
            result = risk_game(user_id, amount)
            await query.message.answer(result)
    elif data == "back":
        await query.message.edit_text("Главное меню:", reply_markup=main_menu())

    await query.answer()

# Starlette webhook
async def webhook(request):
    update = types.Update(**await request.json())
    await dp.update_router.dispatch(update)
    return JSONResponse({"ok": True})

app = Starlette(routes=[Route(WEBHOOK_PATH, webhook, methods=["POST"])])

# Запуск локально для теста
if __name__ == "__main__":
    import asyncio
    from aiogram import Bot, Dispatcher
    from aiogram.filters import Command
    from database import init_db

    init_db()
    bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    
    # запускаем polling
    async def main():
        from bot import dp  # импортируем все хендлеры
        await dp.start_polling(bot)

    asyncio.run(main())
    uvicorn.run("bot:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))