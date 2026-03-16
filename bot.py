# bot.py
import os
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

# ==== Настройки бота ====
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # ставь токен через Render Environment
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://your-app.onrender.com
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ==== Обработчики команд ====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Бот успешно запущен 🚀")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Доступные команды:\n/start\n/help")

# ==== Вебхук сервер для Render ====
async def handle(request: web.Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return web.Response(text="ok")

async def on_startup(app: web.Application):
    # Устанавливаем вебхук
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logging.info("Webhook установлен")

async def on_shutdown(app: web.Application):
    logging.warning("Shutting down..")
    await bot.session.close()
    logging.warning("Bye!")

# ==== Запуск веб-сервера ====
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
