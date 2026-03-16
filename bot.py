import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

# ====== Настройки через переменные окружения ======
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)

# ====== Создаем бота и диспетчера ======
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# ====== Команды бота ======
async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Помощь")
    ])

# ====== Обработчик команды /start ======
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я работаю через Render + webhook 🚀")

# ====== Webhook ======
async def handle(request: web.Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return web.Response(text="ok")

# ====== Запуск сервера ======
async def on_startup(app):
    await set_commands(bot)
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_shutdown)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
