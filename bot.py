import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.utils.executor import start_webhook
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_PATH, WEBHOOK_URL, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Минимальный хэндлер на /start
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.reply("Бот запущен и работает на Render!")

# Настройки webhook для Render
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dispatcher):
    await bot.delete_webhook()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),  # Render сам передаёт PORT
    )
