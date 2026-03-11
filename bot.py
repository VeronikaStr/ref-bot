import os
import logging
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# ============= НАСТРОЙКИ =============
API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise Exception("❌ Токен не найден!")
# ======================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ----- ТОЛЬКО ОДНА КОМАНДА /start -----
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"✅ /start от {message.from_user.id}")
    
    # Простейшие инлайн-кнопки
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Тест 1", callback_data="test1")],
        [InlineKeyboardButton(text="🎯 Тест 2", callback_data="test2")]
    ])
    
    await message.answer("👇 Нажми любую кнопку", reply_markup=kb)

# ----- ОБРАБОТЧИК КНОПОК -----
@dp.callback_query(F.data.in_({"test1", "test2"}))
async def any_callback(callback: types.CallbackQuery):
    logger.info(f"🔥 НАЖАТИЕ! data={callback.data}, user={callback.from_user.id}")
    await callback.answer("✅ Успешно!")
    await callback.message.answer(f"Ты нажал: {callback.data}")

# ----- ВЕБ-СЕРВЕР -----
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
        logger.info(f"✅ Вебхук: {webhook_url}/webhook")

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
