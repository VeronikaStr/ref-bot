import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn

API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise Exception("Токен не найден")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Тест", callback_data="test")]
    ])
    await message.answer("Нажми кнопку", reply_markup=kb)

@dp.callback_query(F.data == "test")
async def test_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("✅ Кнопка работает!")

async def telegram_webhook(request):
    update = types.Update(**(await request.json()))
    await dp.feed_update(bot, update)
    return Response()

async def healthcheck(request):
    return PlainTextResponse("OK")

async def startup():
    webhook_url = os.environ.get("RENDER_EXTERNAL_URL")
    if webhook_url:
        await bot.set_webhook(f"{webhook_url}/webhook")
        logger.info(f"Webhook set to {webhook_url}/webhook")

async def shutdown():
    await bot.delete_webhook()
    await bot.session.close()

app = Starlette(
    routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/healthcheck", healthcheck, methods=["GET"]),
    ],
    on_startup=[startup],
    on_shutdown=[shutdown],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)																																			
