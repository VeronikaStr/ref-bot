import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.filters import Command
from aiohttp import web
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Хэндлер на /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Бот запущен и работает на Render!")

# aiohttp приложение для webhook
async def handle(request: web.Request):
    update = types.Update(**await request.json())
    await dp.update_dispatcher(update)
    return web.Response(text="ok")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
