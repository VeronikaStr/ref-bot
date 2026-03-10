import os
import logging
import asyncio
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- НАСТРОЙКИ ---
# Токен будет браться из переменной окружения на Render
API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise Exception("Ошибка: переменная окружения TELEGRAM_BOT_TOKEN не найдена!")

# Твои реферальные ссылки (такие же, как и раньше)
REF_LINKS = {
    "🔥 Бот для заданий BountyGo!": "https://t.me/SuggestionsBug_bot?start=_tgr_IgNgGHUyNWQy",
    "✨ ЗВЕЗДЫ ВАМ": "https://t.me/ggzvezdatopbot?start=_tgr_wxIiD0BlYzU6",
}

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- ИНИЦИАЛИЗАЦИЯ БОТА И ДИСПЕТЧЕРА ---
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --- ОБРАБОТЧИКИ КОМАНД (твоя логика) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет клавиатуру с кнопками при команде /start"""
    kb = [[KeyboardButton(text=name)] for name in REF_LINKS.keys()]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "🔥 Привет! Я помогу тебе получить бонусы!\n"
        "Выбери, что тебя интересует:",
        reply_markup=keyboard
    )

@dp.message(F.text.in_(REF_LINKS.keys()))
async def send_ref(message: types.Message):
    """Отправляет ссылку при нажатии на кнопку"""
    button_text = message.text
    link = REF_LINKS[button_text]
    await message.answer(
        f"🔗 Твоя ссылка:\n{link}\n\n"
        "👉 Переходи и регистрируйся! 😊"
    )

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def telegram_webhook(request):
    """Здесь Telegram будет оставлять новые сообщения для бота"""
    update = types.Update(**(await request.json()))
    await dp.feed_update(bot, update)
    return Response()

async def healthcheck(request):
    """Проверка здоровья: Render будет стучаться сюда, чтобы убедиться, что бот жив"""
    return PlainTextResponse("OK")

async def startup():
    """Что сделать при запуске сервера"""
    webhook_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not webhook_url:
        logger.error("RENDER_EXTERNAL_URL не задан! Webhook не будет установлен.")
        return
    # Устанавливаем вебхук, чтобы Telegram знал, куда слать сообщения
    await bot.set_webhook(f"{webhook_url}/webhook")
    logger.info(f"Вебхук установлен на {webhook_url}/webhook")

async def shutdown():
    """Что сделать при остановке сервера"""
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Вебхук удалён, сессия закрыта.")

# Создаём Starlette-приложение с маршрутами
app = Starlette(
    routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/healthcheck", healthcheck, methods=["GET"]),
        Route("/", healthcheck, methods=["GET"]),  # Для проверки по умолчанию
    ],
    on_startup=[startup],
    on_shutdown=[shutdown],
)

# Точка входа для локального запуска (необязательно, но пригодится для теста)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)